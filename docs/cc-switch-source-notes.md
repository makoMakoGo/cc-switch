# CC Switch 源码学习笔记

> 维护者入门参考。按依赖顺序阅读，不是按文件大小。
> 每个模块用"接口 → 实现 → 陷阱"三段式。

---

## 第 1 章：架构全景

目标：回答"数据怎么流动"。

### 1.1 应用生命周期

启动链路（`main.rs` → `lib.rs` → 窗口）：

```text
main.rs                          // src-tauri/src/main.rs:6
  └─ lib::run()                  // src-tauri/src/lib.rs:203
       ├─ panic_hook::setup()    // src-tauri/src/lib.rs:205
       ├─ tauri::Builder::default()  // src-tauri/src/lib.rs:207
       ├─ .plugin(single_instance)   // src-tauri/src/lib.rs:211
       ├─ .plugin(deep_link)     // src-tauri/src/lib.rs:252
       ├─ .on_window_event()     // src-tauri/src/lib.rs:254  拦截关闭，最小化到托盘
       ├─ .plugin(process)       // src-tauri/src/lib.rs:275
       ├─ .plugin(dialog)        // src-tauri/src/lib.rs:276
       ├─ .plugin(store)         // src-tauri/src/lib.rs:278
       ├─ .setup(|app| {        // src-tauri/src/lib.rs:284
       │    ├─ Database::init()  // src-tauri/src/lib.rs:383  SQLite + schema 迁移
       │    ├─ migrate_from_json() // src-tauri/src/lib.rs:403  JSON→SQLite 迁移
       │    ├─ AppState::new(db) // src-tauri/src/lib.rs:423
       │    ├─ init_default_skill_repos() // src-tauri/src/lib.rs:433
       │    ├─ seed providers   // src-tauri/src/lib.rs:496  遍历 AppType::all()
       │    ├─ init_common_config_snippets() // src-tauri/src/lib.rs:1601
       │    ├─ restore_proxy_state_on_startup() // src-tauri/src/lib.rs:1558
       │    └─ create_system_tray() // src-tauri/src/tray.rs
       ├─ .invoke_handler(...)   // src-tauri/src/lib.rs:1072  注册 ~300 个命令
       └─ .run()                 // src-tauri/src/lib.rs:1379
       └─ .run(tauri::generate_context!())
```

关键点：
- `main.rs` 只有 1 行有意义代码：`lib::run()` — `src-tauri/src/main.rs:6`
- `lib.rs`（1826 行）是整个后端的"上帝文件"——模块声明（`lib.rs:1-36`）、插件注册（`lib.rs:250-283`）、命令注册（`lib.rs:1072-1377`）全在这里
- 初始化顺序很重要：先建数据库（`lib.rs:383`），再建服务（`lib.rs:423`），再注册命令（`lib.rs:1072`）

### 1.2 数据流：一次 Provider Switch 的完整调用链

以"用户在 UI 里点击切换 Claude Code 的 provider"为例：

```text
前端 (React)
  │  useProviderActions.ts → invoke("switch_claude_provider", { provider_id })
  │
  ▼
Tauri IPC 层
  │  lib.rs 中 invoke_handler 注册的命令
  │
  ▼
Rust 命令处理器 (commands/provider.rs)
  │  fn switch_claude_provider(state, provider_id)
  │    → state.db.get_provider(provider_id)      // 从 SQLite 取 provider
  │    → state.config_service.write_claude_config()  // 写 Claude 配置文件
  │
  ▼
ConfigService (services/config.rs)
  │  write_claude_config(provider)
  │    → claude_config::build_live_config(provider)  // 构建 JSON
  │    → write_json_file(path, config)               // 原子写入 ~/.claude/settings.json
  │
  ▼
文件系统
  ~/.claude/settings.json  ← Claude Code 读取这个文件
```

**Switch vs Additive 两种模式**（`src-tauri/src/app_config.rs:373`）：

```text
Switch 模式（Claude Code、Claude Desktop、Codex、Gemini）：
  - 同一时间只有一个 provider 生效
  - 切换 = 覆盖写入目标工具的配置文件
  - is_additive_mode() == false

Additive 模式（OpenCode、OpenClaw、Hermes）：
  - 所有 provider 同时写入配置文件
  - 切换 = 更新某个 provider 的 enabled 状态
  - is_additive_mode() == true
```

**代理模式下的调用链**（更复杂）：

```text
前端 → invoke("switch_claude_provider_with_proxy", { provider_id })
  → ProxyService::hot_switch_provider(app_type, provider_id)
    → 更新内存中的路由表（不重启代理）
    → 重写 Claude live config，把 API key 替换为 PROXY_MANAGED 占位符
    → 设置 base URL 为 localhost:代理端口
    → 发射 Tauri 事件通知前端
```

### 1.3 状态管理
**后端状态**（`src-tauri/src/store.rs:6`）：
```rust
pub struct AppState {           // src-tauri/src/store.rs:6
    pub db: Arc<Database>,           // SQLite 连接（Mutex 包装）
    pub proxy_service: ProxyService, // 代理服务器管理
    pub usage_cache: Arc<UsageCache>,// 用量统计缓存
}
```
`Arc<T>` = 引用计数智能指针，允许多个地方共享同一份数据（`src-tauri/src/store.rs:3`）。
`Database` 内部用 `Mutex<Connection>` 包装 SQLite 连接（`src-tauri/src/database/mod.rs:76`），因为 `rusqlite::Connection` 不是 `Sync` 的。
**ProxyService**（`src-tauri/src/services/proxy.rs:55`）：
```rust
pub struct ProxyService {       // src-tauri/src/services/proxy.rs:55
    db: Arc<Database>,
    server: Arc<RwLock<Option<ProxyServer>>>,
    app_handle: Arc<RwLock<Option<tauri::AppHandle>>>,
    switch_locks: SwitchLockManager,
}
```
- `ProxyService` 管理代理服务器的生命周期（启动、停止、配置）
- `server` 是 `Option<ProxyServer>`，因为代理可能没启动
- `switch_locks` 防止并发切换 provider
**设置缓存**（`src-tauri/src/settings.rs:5`）：
```rust
static APP_SETTINGS: OnceLock<RwLock<AppSettings>> = OnceLock::new();  // src-tauri/src/settings.rs:5
```
- `OnceLock` = 全局只初始化一次
- `RwLock` = 读写锁，多读单写
- 流程：`read_settings()` 先读文件 → 反序列化 → 缓存到内存；后续读直接返回内存缓存
- 写流程：`mutate_settings()` → 读 → clone → 修改 → 写文件 → 更新内存缓存
**前端状态**（React）：
```text
App.tsx
  ├─ localStorage("currentView")     ← 当前视图状态
  ├─ useQuery(["providers"])          ← React Query 缓存 provider 列表
  ├─ useTauriEvent("provider-changed") ← 监听后端事件刷新 UI
  └─ useProxyStatus()                 ← 轮询代理状态
```
**状态同步机制**：
- 前端通过 `invoke()` 调用 Tauri 命令，获取后端状态
- 后端通过 `app.emit()` 发射事件，通知前端状态变化
- React Query 自动缓存和刷新数据
- `useTauriEvent` hook 监听后端事件，触发 UI 更新
### 1.4 模块依赖全景图
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
   │  commands/  │  │  services/ │  │   proxy/    │
   │ (Tauri IPC) │→ │(业务逻辑)  │→ │ (HTTP代理)  │
   └──────┬──────┘  └─────┬──────┘  └──────┬──────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼──────┐
                    │  database/  │
                    │  (SQLite)   │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
   │  provider   │  │   config   │  │  settings   │
   │  (数据模型) │  │  (路径/IO) │  │  (全局配置) │
   └─────────────┘  └────────────┘  └─────────────┘
```

---

## 第 2 章：Tauri/Rust 基础速查

不需要学完整个 Rust，只需要理解这些在 cc-switch 里反复出现的模式。

### 2.1 你会反复遇到的 Rust 概念

| 概念 | 一句话解释 | cc-switch 里的例子 |
|------|-----------|-------------------|
| `Arc<T>` | 原子引用计数，多线程共享数据 | `AppState.db: Arc<Database>` |
| `Mutex<T>` | 互斥锁，同一时间只有一个线程能访问 | `Database.conn: Mutex<Connection>` |
| `RwLock<T>` | 读写锁，多读单写 | `settings.rs` 的 `APP_SETTINGS: OnceLock<RwLock<AppSettings>>` |
| `OnceLock<T>` | 全局只初始化一次的值 | 同上，设置缓存 |
| `Result<T, E>` | 可能成功(T)也可能失败(E)的返回值 | 几乎所有函数的返回类型 |
| `?` 操作符 | 提前返回错误的语法糖 | `let config = read_json_file(path)?;` |
| `#[tauri::command]` | 标记函数为 Tauri IPC 命令 | `commands/` 目录下的所有函数 |
| `serde` | 序列化/反序列化框架 | `#[derive(Serialize, Deserialize)]` 到处都是 |
| `tokio::spawn` | 异步任务 | 代理服务器启动、后台检查等 |
| `thiserror` | 自动派生 Error trait | `error.rs` 里的 `AppError` |
| `impl From<X> for Y` | 类型转换 | `CircuitBreakerConfig::from(&AppProxyConfig)` |
| `#[serde(rename_all)]` | JSON 字段命名风格转换 | `camelCase` vs `snake_case` |

### 2.2 你不需要深入的

| 概念 | 说明 |
|------|------|
| 生命周期标注 `'a` | cc-switch 里几乎不用，遇到再查 |
| trait object (`dyn Trait`) | 用得很少 |
| `unsafe` | 搜索了一下，项目里没有 |
| 泛型约束 (`where T: ...`) | 有但不复杂，跟着类型提示走就行 |
| 宏 (`macro_rules!`) | 只有 `lock_conn!` 一个自定义宏 |

### 2.3 常见模式速查
**读取配置文件并处理错误**（`src-tauri/src/config.rs`）：
```rust
// config.rs 里的典型模式
let content = std::fs::read_to_string(&path)
    .map_err(|e| AppError::io(&path, e))?;
let config: MyConfig = serde_json::from_str(&content)
    .map_err(|e| AppError::json(&path, e))?;
```
**Tauri 命令的标准签名**（`src-tauri/src/commands/`）：
```rust
#[tauri::command]                    // 标记为 Tauri IPC 命令
async fn get_providers(              // 异步函数
    state: tauri::State<'_, AppState>, // 自动注入全局状态
) -> Result<Vec<Provider>, AppError> { // 返回 Result，自动转为 JS reject
    // state.db, state.proxy_service 等都可以直接访问
}
```
**写入配置文件（原子写入）**（`src-tauri/src/config.rs`）：
```rust
// config.rs: atomic_write
fn atomic_write(path: &Path, content: &str) -> Result<(), AppError> {
    let tmp = path.with_extension("tmp");
    std::fs::write(&tmp, content)?;
    std::fs::rename(&tmp, path)?;  // 原子替换
    Ok(())
}
```
**Mutex 锁获取**（`src-tauri/src/database/mod.rs:61`）：
```rust
// database/mod.rs: lock_conn! 宏
macro_rules! lock_conn {
    ($mutex:expr) => {
        $mutex
            .lock()
            .map_err(|e| AppError::Database(format!("Mutex lock failed: {}", e)))?
    };
}
// 使用方式
let conn = lock_conn!(self.conn);
```
**serde 属性速查**：
```rust
#[derive(Serialize, Deserialize)]           // 自动派生序列化
#[serde(rename_all = "camelCase")]          // JSON 字段用 camelCase
#[serde(skip_serializing_if = "Option::is_none")]  // None 时不序列化
#[serde(default)]                           // 反序列化时缺失字段用默认值
#[serde(rename = "settingsConfig")]         // 重命名单个字段
#[serde(alias = "claudeDesktop")]           // 支持多个别名
```
**async/await 模式**（`src-tauri/src/services/`）：
```rust
// 异步函数
async fn some_operation() -> Result<(), AppError> {
    tokio::time::sleep(Duration::from_secs(1)).await;
    Ok(())
}
// 在 Tauri 命令中使用
#[tauri::command]
async fn my_command(state: tauri::State<'_, AppState>) -> Result<String, AppError> {
    let result = some_operation().await?;
    Ok(result)
}
```
## 第 3 章：后端核心模块
按依赖顺序读，不是按文件大小。先读底层工具模块，再读业务模块。
### 3.1 config.rs — 路径解析和文件 I/O（14KB）
**接口**：提供所有模块需要的路径解析和文件读写工具函数（`src-tauri/src/config.rs`）。
**核心函数**：
- `get_home_dir()` → `~` 目录（支持 `CC_SWITCH_TEST_HOME` 测试覆盖）
- `get_app_config_dir()` → `~/.cc-switch/`（`src-tauri/src/config.rs`）
- `get_claude_dir()` → `~/.claude/`
- `get_codex_dir()` → `~/.codex/`
- `read_json_file<T>(path)` → 读文件并反序列化为 Rust 结构体
- `write_json_file<T>(path, data)` → 序列化并原子写入
- `atomic_write(path, content)` → 临时文件 + rename 的安全写入
**实现亮点**：
- 所有路径函数都支持环境变量覆盖，方便测试（`CC_SWITCH_TEST_HOME`）
- `atomic_write` 用 `write_to_tmp + rename` 避免写入中断导致文件损坏
- 文件读写统一用 `AppError::io()` 和 `AppError::json()` 包装错误
**陷阱**：
- `get_home_dir()` 在某些环境下可能返回 None，导致 panic
- 路径硬编码了 `~/.claude` 等，如果用户自定义了 Claude 的配置目录会出问题
- 没有文件锁保护，并发写入可能冲突
### 3.1.5 database/ — 数据持久化（SQLite）
**接口**：SQLite 数据库的初始化、迁移、DAO 操作（`src-tauri/src/database/mod.rs`）。
**核心结构**：
```rust
pub struct Database {           // src-tauri/src/database/mod.rs:76
    pub(crate) conn: Mutex<Connection>,  // SQLite 连接（Mutex 包装）
}
```
**模块结构**（`src-tauri/src/database/`）：
}
```

**亮点**：
- `Localized` 变体支持中英双语错误消息，前端可以根据语言选择显示
- `Io` 变体包含文件路径，方便调试

**陷阱**：
- `Config(String)` 太宽泛，很多不同类型的错误都往这里塞
- 错误消息不一致，有的用英文有的用中文

### 3.3 app_config.rs — 多应用配置模型（41KB）

**接口**：定义 cc-switch 管理的 7 个 AI 工具的抽象（`src-tauri/src/app_config.rs:338`）。

**核心类型**：

```rust
pub enum AppType {            // src-tauri/src/app_config.rs:341
    Claude,        // Claude Code (CLI)
    ClaudeDesktop, // Claude Desktop (GUI)
    Codex,         // OpenAI Codex CLI
    Gemini,        // Gemini CLI
    OpenCode,      // OpenCode
    OpenClaw,      // OpenClaw
    Hermes,        // Hermes
}
```

**关键设计决策 — `is_additive_mode()`**（`src-tauri/src/app_config.rs:373`）：

```rust
impl AppType {
    pub fn is_additive_mode(&self) -> bool {  // src-tauri/src/app_config.rs:373
        matches!(self,
            AppType::OpenCode | AppType::OpenClaw | AppType::Hermes
        )
    }
}
```
```

这个分类影响整个架构：
- Switch 模式（4 个工具）：同一时间只有一个 provider 生效，切换 = 覆盖写入
- Additive 模式（3 个工具）：所有 provider 同时写入，切换 = 更新 enabled 状态

**其他重要类型**：
- `McpApps`（`src-tauri/src/app_config.rs:9`）— 哪些工具支持 MCP server 配置
- `SkillApps`（`src-tauri/src/app_config.rs:78`）— 哪些工具支持 skills
- `CommonConfigSnippets`（`src-tauri/src/app_config.rs:419`）— 跨工具共享的配置片段

**陷阱**：
- 这个文件 41KB 太大了，包含了太多职责（类型定义 + 工具特性查询 + 配置片段管理）
- `AppType` 的 match 到处都是（`McpApps:24`, `VisibleApps:66`, `CommonConfigSnippets:441`），加新工具需要改很多地方

### 3.4 provider.rs — 核心数据模型（40.6KB）

**接口**：Provider 是 cc-switch 的核心数据单元（`src-tauri/src/provider.rs:10`）。

**Provider 结构体**（`src-tauri/src/provider.rs:10-43`）：

```rust
pub struct Provider {          // src-tauri/src/provider.rs:10
    pub id: String,                    // 唯一标识
    pub name: String,                  // 显示名称
    pub settings_config: Value,        // JSON 格式的配置（API key、base URL 等）
    pub website_url: Option<String>,   // 官网地址
    pub category: Option<String>,      // 分类
    pub created_at: Option<i64>,       // 创建时间
    pub sort_index: Option<usize>,     // 排序索引
    pub notes: Option<String>,         // 备注
    pub meta: Option<ProviderMeta>,    // 元数据
    pub icon: Option<String>,          // 图标
    pub icon_color: Option<String>,    // 图标颜色
    pub in_failover_queue: bool,       // 是否在故障转移队列中
}
```
- 与数据库交互

**UniversalProvider**：
- 跨应用共享的 provider 配置
- 一次配置，多个工具复用

**陷阱**：
- `settings_config` 是 `serde_json::Value`（动态类型），不是强类型的，容易出错
- Provider 和 AppType 的关系是 N:1，但代码里很多地方假设 1:1

### 3.5 settings.rs — 设置管理（28.9KB）
**接口**：全局应用设置的读写（`src-tauri/src/settings.rs:5`），包括代理配置、UI 偏好、WebDAV 同步等。
**实现**：
```rust
static APP_SETTINGS: OnceLock<RwLock<AppSettings>> = OnceLock::new();  // src-tauri/src/settings.rs:5
pub fn read_settings() -> AppSettings {
    let settings = APP_SETTINGS.get_or_init(|| {
        let file_settings = read_settings_from_file();
        RwLock::new(file_settings)
    });
    settings.read().unwrap().clone()
}
pub fn mutate_settings<F>(f: F) -> Result<(), AppError>
where
    F: FnOnce(&mut AppSettings),
{
    let mut settings = APP_SETTINGS.get().unwrap().write().unwrap();
    f(&mut settings);
    write_settings_to_file(&settings)?;
    Ok(())
}
```
**AppSettings 包含**（`src-tauri/src/settings.rs`）：
- 代理端口、监听地址
- 每个工具的代理配置（是否启用、超时时间等）
- WebDAV 同步配置（`src-tauri/src/settings.rs:82`）
- UI 主题、语言偏好
- 可见应用列表（`VisibleApps`，`src-tauri/src/settings.rs:28`）
- 自动启动、静默启动等偏好
**VisibleApps**（`src-tauri/src/settings.rs:28`）：
```rust
pub struct VisibleApps {       // src-tauri/src/settings.rs:28
    pub claude: bool,
    pub claude_desktop: bool,
    pub codex: bool,
    pub gemini: bool,
    pub opencode: bool,
    pub openclaw: bool,
    pub hermes: bool,           // 默认不显示
}
```
**陷阱**：
- `unwrap()` 在锁获取时，如果锁被 poisoned 会 panic
- 写入失败时内存缓存和文件可能不一致
- 没有版本控制，并发修改可能丢失
### 3.6 各工具 config 模块对比
| 模块 | 文件 | 大小 | 职责 |
|------|------|------|------|
| Claude Code | `src-tauri/src/claude_config.rs` | 27.7KB | Claude Code CLI 的配置读写 |
| Claude Desktop | `src-tauri/src/claude_desktop_config.rs` | 61.5KB | Claude Desktop GUI 的配置读写 |
| Codex CLI | `src-tauri/src/codex_config.rs` | 66.5KB | OpenAI Codex CLI 的配置读写 |
| Gemini CLI | `src-tauri/src/gemini_config.rs` | 20.4KB | Gemini CLI 的配置读写 |
| OpenCode | `src-tauri/src/opencode_config.rs` | 42.6KB | OpenCode 的配置读写 |
| OpenClaw | `src-tauri/src/openclaw_config.rs` | 52.4KB | OpenClaw 的配置读写 |
| Hermes | `src-tauri/src/hermes_config.rs` | 35.2KB | Hermes 的配置读写 |
**共同模式（每个模块都有）**：
1. `read_xxx_config()` — 读取工具的配置文件（如 `~/.claude/settings.json`）
2. `write_xxx_config()` — 写入工具的配置文件
3. `build_live_config()` — 构建当前生效的配置（合并 provider + 公共配置）
4. `switch_provider()` — 切换 provider 的核心逻辑
5. `import_from_live()` — 从工具的 live 配置导入 provider
**AI Slop 特征**：
- 每个模块的 `switch_provider()` 逻辑高度相似，但没有抽取公共函数
- 配置文件格式不同导致代码差异大，但"读文件 → 解析 → 修改 → 写文件"的骨架是一样的
- `codex_config.rs`（66.5KB）和 `claude_desktop_config.rs`（61.5KB）明显过大
- 每个模块都自己实现了一遍 JSON merge 逻辑
**设计好的地方**：
- 每个模块独立，不互相依赖
- 错误处理一致（都用 `AppError`）
- 配置文件路径都通过 `config.rs` 的函数获取，不硬编码
**屎山特征**：
- 大量重复的文件读写代码（每个模块 100-200 行几乎一样）
- 没有统一的 config trait 或接口
- 每个模块都自己处理了边界情况（文件不存在、JSON 格式错误等）
- 配置文件格式不统一（有的用 JSON，有的用 TOML，有的用 YAML）
**对比分析**：
- Switch 模式工具（Claude、Codex、Gemini）的 config 模块更简单，因为只需要覆盖写入
- Additive 模式工具（OpenCode、OpenClaw、Hermes）的 config 模块更复杂，需要管理多个 provider 的 enabled 状态
- Claude Desktop 的 config 模块最大（61.5KB），因为它需要处理 MCP 服务器配置
- Codex 的 config 模块最大（66.5KB），因为它需要处理 OAuth 认证和 Copilot 集成
## 第 4 章：本地代理子系统
这是项目里最复杂的部分，单独拎出来。代理子系统实现了本地 HTTP 代理，支持 API 格式转换（Anthropic ↔ OpenAI ↔ Gemini）、多 provider 路由、故障转移和熔断。
### 4.1 proxy/ 目录结构
```text
src-tauri/src/proxy/
├── switch_lock.rs      # 切换锁（防止并发切换）
├── handlers/           # 请求处理器
├── providers/          # 格式转换器
│   ├── claude/         # Anthropic API 格式
│   ├── codex/          # OpenAI API 格式
│   ├── gemini/         # Gemini API 格式
│   └── ...
├── transform_*.rs      # API 格式转换（58-78KB 每个）
├── types.rs            # 共享类型定义
└── log_codes.rs        # 日志代码常量
```
**ProxyState**（`src-tauri/src/proxy/server.rs:34`）：
```rust
pub struct ProxyState {       // src-tauri/src/proxy/server.rs:34
    pub db: Arc<Database>,
    pub config: Arc<RwLock<ProxyConfig>>,
    pub status: Arc<RwLock<ProxyStatus>>,
    pub provider_router: Arc<ProviderRouter>,
    pub gemini_shadow: Arc<GeminiShadowStore>,
    pub codex_chat_history: Arc<CodexChatHistoryStore>,
    pub failover_manager: Arc<FailoverSwitchManager>,
}
```
**ProxyServer**（`src-tauri/src/proxy/server.rs:54`）：
- `ProxyServer::new()` 创建 `ProxyState` 并初始化所有共享组件
- `ProxyServer::start()` 绑定端口、启动 Axum 路由
- `ProxyServer::stop()` 发送 shutdown 信号、等待服务器关闭
**技术栈**：
- Axum — HTTP 框架
- Tower — 中间件层
- Hyper — 底层 HTTP 实现
- Tokio — 异步运行时
**API 格式转换**（`src-tauri/src/proxy/`）：
- `transform_codex_chat.rs`（71KB）— OpenAI Codex Chat API ↔ 内部格式
- `transform_gemini.rs`（78KB）— Gemini API ↔ 内部格式
- `providers/claude/` — Anthropic API 格式处理
- `providers/codex/` — OpenAI API 格式处理
- `providers/gemini/` — Gemini API 格式处理
**多 provider 路由逻辑**（`src-tauri/src/proxy/provider_router.rs`）：
- 每个 provider 有自己的 API key
- 代理服务器根据请求中的 API key 判断转发到哪个 provider
- 支持故障转移：主 provider 挂了自动切换到备选
- `ProviderRouter` 持有熔断器状态，跨请求保持
### 4.3 故障转移和熔断
**CircuitBreaker**（`src-tauri/src/proxy/circuit_breaker.rs:76`）：
```rust
pub struct CircuitBreaker {    // src-tauri/src/proxy/circuit_breaker.rs:76
    state: Arc<RwLock<CircuitState>>,          // Closed/Open/HalfOpen
    consecutive_failures: Arc<AtomicU32>,       // 连续失败计数
    consecutive_successes: Arc<AtomicU32>,      // 连续成功计数
    total_requests: Arc<AtomicU32>,             // 总请求数
    total_failures: Arc<AtomicU32>,             // 总失败数
    last_failure_time: Arc<RwLock<Option<Instant>>>,
    config: CircuitBreakerConfig,
}
```
**CircuitBreakerConfig**（`src-tauri/src/proxy/circuit_breaker.rs:38`）：
```rust
pub struct CircuitBreakerConfig {  // src-tauri/src/proxy/circuit_breaker.rs:38
    pub failure_threshold: u32,     // 连续失败多少次后打开熔断器
    pub success_threshold: u32,     // 半开状态下成功多少次后关闭
    pub timeout_seconds: u64,       // 熔断器打开后多久尝试半开
    pub error_rate_threshold: f64,  // 错误率阈值 (0.0-1.0)
    pub min_requests: u32,          // 计算错误率前的最小请求数
}
```
**状态转换**：
```text
Closed（正常）
  │ 连续失败 >= failure_threshold（默认 4）
  ▼
Open（熔断）
  │ 等待 timeout_seconds（默认 60 秒）
  ▼
HalfOpen（半开）
  │ 连续成功 >= success_threshold（默认 2）→ 回到 Closed
  │ 任何失败 → 回到 Open
  ▼
Closed 或 Open
```
**FailoverQueue**（数据库中的 `failover_queue` 表）：
- 存储备选 provider 列表
- 当主 provider 熔断时，按优先级尝试备选
- 所有备选都失败时，返回 `AllProvidersCircuitOpen` 错误（`src-tauri/src/error.rs:26`）
**FailoverSwitchManager**（`src-tauri/src/proxy/failover_switch.rs`）：
- 管理故障转移切换逻辑
- 与数据库交互，读取/更新 failover_queue
- 发射 Tauri 事件通知前端
**陷阱**：
- `forwarder.rs`（122KB）太大，包含了太多职责
- 熔断器状态是内存中的，重启后重置（`src-tauri/src/proxy/circuit_breaker.rs:78`）
- 并发切换时需要 `SwitchLock` 保护（`src-tauri/src/proxy/switch_lock.rs`）
- 没有持久化熔断器状态，重启后所有 provider 都是 Closed 状态
## 第 5 章：前端架构
前端是 React + TypeScript，通过 Tauri IPC 与 Rust 后端通信。前端代码在 `src/` 目录下。
### 5.1 App.tsx — 14 个视图的路由机制
**App.tsx**（1605 行）是前端的"上帝文件"（`src/App.tsx`）。
**视图切换机制**（`src/App.tsx`）：
```typescript
// localStorage 持久化当前视图
const [currentView, setCurrentView] = useState(
  localStorage.getItem("currentView") || "providers"  // 默认显示 provider 列表
);
// 14 个视图
switch (currentView) {
  case "coding-plan":  return <CodingPlan />;        // Coding Plan
  case "import-export":return <ImportExport />;      // 导入导出
  case "about":        return <About />;             // 关于页面
}
```
**App 切换机制**（`src/App.tsx`）：
```typescript
// 切换当前管理的 AI 工具
const [currentApp, setCurrentApp] = useState<AppType>(
  localStorage.getItem("currentApp") || "Claude"  // 默认管理 Claude
);
```
**AI Slop 特征**：
- 1605 行的单文件，应该拆分
- 所有视图都在一个 switch 里，没有用路由库（React Router）
- 大量内联的事件处理逻辑，应该抽取到 hooks
- 没有代码分割（code splitting），所有视图都打包在一个 chunk 里
### 5.2 hooks/ — 状态管理层
**核心 hooks**（`src/hooks/`）：
| Hook | 文件 | 职责 |
|------|------|------|
| `useProviderActions` | `src/hooks/useProviderActions.ts` | Provider 的 CRUD 操作（React Query mutations） |
| `useSettings` | `src/hooks/useSettings.ts` | 设置的读写 |
| `useSettingsForm` | `src/hooks/useSettingsForm.ts` | 设置表单状态管理 |
| `useDirectorySettings` | `src/hooks/useDirectorySettings.ts` | 工具目录配置 |
| `useProxyStatus` | `src/hooks/useProxyStatus.ts` | 代理状态实时同步 |
| `useTauriEvent` | `src/hooks/useTauriEvent.ts` | 监听 Tauri 后端事件 |
| `useAutoCompact` | `src/hooks/useAutoCompact.ts` | 自动压缩对话 |
| `useUsageCacheBridge` | `src/hooks/useUsageCacheBridge.ts` | 用量缓存桥接 |
| `useDragSort` | `src/hooks/useDragSort.ts` | 拖拽排序 |
| `useStreamCheck` | `src/hooks/useStreamCheck.ts` | 流式检查 |
| `useDarkMode` | `src/hooks/useDarkMode.ts` | 暗色模式 |
**useProviderActions 详解**（`src/hooks/useProviderActions.ts`）：
这是最核心的 hooks，封装了所有 Provider 的 CRUD 操作：
```typescript
// src/hooks/useProviderActions.ts
const switchMutation = useMutation({
  mutationFn: (providerId: string) =>
    invoke("switch_claude_provider", { providerId }),  // 调用 Tauri 命令
  onSuccess: () => {
    queryClient.invalidateQueries(["providers"]);     // 刷新缓存
    // 发射事件通知其他组件
  },
});
```
**useSettings 详解**（`src/hooks/useSettings.ts`）：
- 封装了 `get_settings` 和 `save_settings` Tauri 命令
- 使用 React Query 缓存设置数据
- 提供 `mutateSettings` 方法用于修改设置
**useProxyStatus 详解**（`src/hooks/useProxyStatus.ts`）：
- 轮询代理服务器状态（每 2 秒）
- 提供 `isRunning`, `currentProviders`, `uptime` 等状态
- 使用 `useTauriEvent` 监听代理状态变化事件
**前端 → 后端调用模式**：
```typescript
// 标准模式：invoke + React Query
const { data: providers } = useQuery(
  ["providers", currentApp],
  () => invoke("get_providers", { appType: currentApp })
);
// 事件监听模式
useTauriEvent("provider-changed", (event) => {
  queryClient.invalidateQueries(["providers"]);
});
```
**useTauriEvent 详解**（`src/hooks/useTauriEvent.ts`）：
```typescript
// src/hooks/useTauriEvent.ts
export function useTauriEvent<T>(event: string, handler: (payload: T) => void) {
  useEffect(() => {
    const unlisten = listen(event, (e) => handler(e.payload));
    return () => { unlisten.then(fn => fn()); };
  }, [event, handler]);
}
```
### 5.3 config/ — 287KB 的 preset 数据
```text
src/config/
```

每个 preset 文件定义了该工具的官方 provider 列表（名称、图标、默认配置等）。

**AI Slop 特征**：
- 7 个文件结构几乎一样，但没有抽取公共模板
- 287KB 的 TypeScript 数据，可以移到 JSON 文件
- 很多 preset 是从官网复制的，更新时需要手动同步

### 5.4 前端 → 后端的调用模式

**invoke 封装**（没有统一封装，直接用 Tauri 的 `invoke`）：

```typescript
import { invoke } from "@tauri-apps/api/core";

// 直接调用
const result = await invoke("command_name", { arg1, arg2 });
```

**Tauri event 监听**：

```typescript
import { listen } from "@tauri-apps/api/event";

const unlisten = await listen("event-name", (event) => {
  console.log(event.payload);
});

// 组件卸载时取消监听
return () => unlisten();
```

---

## 第 6 章：AI Slop 特征模式识别
这是你重构的弹药库。这些模式不是"代码风格偏好"，而是实实在在的维护负担。
### 6.1 代码膨胀模式
**过大的单文件**：
| 文件 | 行数 | 问题 |
|------|------|------|
| `lib.rs` | 1826 | 模块声明（`lib.rs:1-36`）+ 插件注册（`lib.rs:250-283`）+ 命令注册（`lib.rs:1072-1377`）+ 初始化逻辑（`lib.rs:284-1070`）全混在一起 |
| `App.tsx` | 1605 | 14 个视图 + 事件处理 + 状态管理全在一个文件 |
| `forwarder.rs` | ~3000 | 请求转发 + 格式转换 + 错误处理全在一起 |
| `codex_config.rs` | ~1600 | 配置读写 + 迁移 + 验证全在一起 |
| `claude_desktop_config.rs` | ~1500 | 同上 |
| `proxy.rs`（services） | 3910 | `ProxyService` 的所有方法全在一个文件（`src-tauri/src/services/proxy.rs:55`） |
| `provider/mod.rs`（services） | ~2600 | `ProviderService` 的所有方法全在一个文件 |
**复制粘贴的 config 模块**：
- 7 个工具的 config 模块结构几乎一样，但没有抽取公共函数
- 每个都自己实现了一遍 `read → parse → modify → write` 流程
- 没有公共的 config trait 或接口
**无意义的 wrapper 层**：
- 有些函数只是简单调用另一个函数，没有增加任何价值
- 例如 `commands/` 里很多函数只是 `state.service.method()` 的透传
**冗余的 match 分支**：
- `AppType` 的 match 在 `McpApps`（`src-tauri/src/app_config.rs:24`）、`VisibleApps`（`src-tauri/src/settings.rs:66`）、`CommonConfigSnippets`（`src-tauri/src/app_config.rs:441`）里重复出现
- 每次加新工具都要改 10+ 个 match
**冗余的 pub use 导出**：
- `lib.rs:38-51` 里有大量 `pub use` 导出，很多已经在 `commands/mod.rs` 里导出过
- 导致同一个函数从两个路径可以访问，增加了理解难度
**重复的错误处理代码**：
- 每个 config 模块都自己实现了一遍文件读取错误处理
- 每个 service 都自己实现了一遍数据库错误处理
- 应该抽取公共的错误处理宏或函数
### 6.2 过度抽象模式
**为了"未来可能需要"而加的抽象**：
- `CommonConfigSnippets`（`src-tauri/src/app_config.rs:419`）— 理论上是跨工具共享的配置片段，但实际使用率不高
- 一些 trait 定义了接口但只有一个实现
**深层嵌套的类型定义**：
- `Provider`（`src-tauri/src/provider.rs:10`）→ `ProviderMeta` → `ProviderMetaInner` → ...
- 层级太深，阅读困难
**动态类型滥用**：
- `Provider.settings_config: Value`（`src-tauri/src/provider.rs:14`）是 `serde_json::Value`，不是强类型
- 运行时才知道配置是否合法，编译器帮不上忙
- 对比：如果用 `enum ProviderSettings { Anthropic(AnthropicConfig), OpenAI(OpenAIConfig), ... }` 会更安全
**过度的 Option 包装**：
- `Provider` 结构体里很多字段都是 `Option<T>`（`src-tauri/src/provider.rs:15-38`）
- 有些字段（如 `icon`、`icon_color`）实际上总是有值的，不应该用 Option
- 增加了运行时的 None 检查负担
### 6.3 命名和组织问题
**不一致的命名约定**：
- 有的用 `xxx_config`，有的用 `xxx_settings`
- 有的函数叫 `get_xxx`，有的叫 `read_xxx`，有的叫 `fetch_xxx`
- 错误消息有的中文有的英文（`src-tauri/src/error.rs:29` 的 `Localized` 变体试图解决这个问题，但不彻底）
**模糊的模块边界**：
- `services/`（`src-tauri/src/services/mod.rs`）和 `commands/`（`src-tauri/src/commands/mod.rs`）的职责划分不清晰
- 有些逻辑放在 `services/` 里，有些直接放在 `commands/` 里
- `lib.rs` 里的 `initialize_common_config_snippets()`（`src-tauri/src/lib.rs:1601`）应该在 services 层
**放错地方的代码**：
- `cleanup_before_exit()`（`src-tauri/src/lib.rs:1513`）是代理相关的逻辑，但放在 lib.rs
- `restore_proxy_state_on_startup()`（`src-tauri/src/lib.rs:1558`）同理
- `is_chinese_locale()`（`src-tauri/src/lib.rs:1685`）是通用工具函数，但放在 lib.rs
| `lib.rs:1601-1678` | `initialize_common_config_snippets()` 放在 lib.rs | 移到 `services/config.rs` |
| `lib.rs:1685-1691` | `is_chinese_locale()` 放在 lib.rs | 移到 `config.rs` 或 `utils/` |
| `App.tsx:1-1605` | 14 个视图在 switch 里 | 用 React Router 或状态机库 |
| `codex_config.rs` 全文 | 66.5KB 太大 | 拆分成 `codex/` 目录（read.rs, write.rs, migrate.rs） |
| `claude_desktop_config.rs` 全文 | 61.5KB 太大 | 同上 |
| `services/proxy.rs:55` | `ProxyService` 3910 行 | 拆分成 takeover.rs, hot_switch.rs, config.rs |
| 7 个 config 模块 | 重复的读写逻辑 | 抽取 `ToolConfig` trait |
| 7 个 preset 文件 | 287KB TypeScript 数据 | 移到 JSON 文件，运行时加载 |
| `provider.rs:14` | `settings_config: Value` 动态类型 | 考虑用强类型 enum |
| `app_config.rs:24,66,441` | `AppType` match 重复 10+ 处 | 用 trait 或 visitor 模式统一 |
| `error.rs:8` | `Config(String)` 太宽泛 | 拆分成更具体的变体 |
| `settings.rs:5` | `OnceLock<RwLock<>>` + `unwrap()` | 用 `parking_lot::RwLock` 避免 poisoned panic |
**删除死代码**：
- 搜索 `#[allow(dead_code)]` 和未使用的函数
- 删除注释掉的代码块
- 删除 `lib.rs:38` 里重复的 `pub use` 导出（很多已经在 `commands/mod.rs` 里导出过）
**统一命名**：
- `get_xxx` / `read_xxx` / `fetch_xxx` 统一为 `read_xxx`
- `xxx_config` / `xxx_settings` 统一为 `xxx_config`
- 错误消息统一为英文（或统一为中文），不要混用
**提取重复模式**：
- 7 个 config 模块的 `read → parse → modify → write` 骨架抽取为公共函数
- 7 个 preset 文件的结构抽取为公共模板
- `AppType` 的 match 分支（`app_config.rs:24,66,441`）抽取为 trait 方法
### 7.2 中等重构（3-5 天）
**拆分过大的文件**：
- `lib.rs`（1826 行）→ `init.rs`（初始化逻辑 `lib.rs:284-1070`）+ `commands.rs`（命令注册 `lib.rs:1072-1377`）+ `lib.rs`（仅模块声明 `lib.rs:1-36`）
- `App.tsx`（1605 行）→ 每个视图一个文件 + `AppRouter.tsx`
- `codex_config.rs`（66.5KB）→ `codex/` 目录
- `claude_desktop_config.rs`（61.5KB）→ `claude_desktop/` 目录
- `services/proxy.rs`（3910 行）→ 拆分成 `takeover.rs`, `hot_switch.rs`, `config.rs`
**统一 config 模块的结构**：

```rust
// 定义统一的 config trait
trait ToolConfig {
    fn read_config(&self) -> Result<Value, AppError>;
    fn write_config(&self, config: &Value) -> Result<(), AppError>;
    fn switch_provider(&self, provider: &Provider) -> Result<(), AppError>;
}

// 每个工具实现这个 trait
struct ClaudeConfig { ... }
impl ToolConfig for ClaudeConfig { ... }
```

**简化前端 hooks 层**：
- 合并 `useSettings` + `useSettingsForm` + `useDirectorySettings`
- 抽取公共的 `useTauriCommand` hook
## 第 7 章：重构路线图
基于前 6 章的理解，制定具体重构计划。按风险从低到高排列。
### 7.1 低风险清理（先做，1-2 天）
**删除死代码**：
- 搜索 `#[allow(dead_code)]` 和未使用的函数
- 删除注释掉的代码块
- 删除 `lib.rs:38` 里重复的 `pub use` 导出
**统一命名**：
- `get_xxx` / `read_xxx` / `fetch_xxx` 统一为 `read_xxx`
- `xxx_config` / `xxx_settings` 统一为 `xxx_config`
- 错误消息统一为英文（或统一为中文）
**提取重复模式**：
- 7 个 config 模块的 `read → parse → modify → write` 骨架抽取为公共函数
- 7 个 preset 文件的结构抽取为公共模板
- `AppType` 的 match 分支抽取为 trait 方法
### 7.2 中等重构（3-5 天）
**拆分过大的文件**：
- `lib.rs`（1826 行）→ `init.rs` + `commands.rs` + `lib.rs`
- `App.tsx`（1605 行）→ 每个视图一个文件 + `AppRouter.tsx`
- `codex_config.rs`（66.5KB）→ `codex/` 目录
- `claude_desktop_config.rs`（61.5KB）→ `claude_desktop/` 目录
- `services/proxy.rs`（3910 行）→ 拆分成 `takeover.rs`, `hot_switch.rs`, `config.rs`
**统一 config 模块的结构**：
```rust
trait ToolConfig {
    fn read_config(&self) -> Result<Value, AppError>;
    fn write_config(&self, config: &Value) -> Result<(), AppError>;
    fn switch_provider(&self, provider: &Provider) -> Result<(), AppError>;
}
```
**简化前端 hooks 层**：
- 合并 `useSettings` + `useSettingsForm` + `useDirectorySettings`
- 抽取公共的 `useTauriCommand` hook
### 7.3 架构级重构（最后做，慎重，1-2 周）
**Provider 管理的统一抽象**：
- 定义 `ProviderManager` trait
- 每个工具有自己的 `ProviderManager` 实现
- 切换逻辑统一处理，不再分散在各个 config 模块
**代理子系统的简化**：
- `forwarder.rs`（122KB）拆分成多个职责单一的模块
- 抽取公共的 API 格式转换框架
- 统一错误处理和日志记录