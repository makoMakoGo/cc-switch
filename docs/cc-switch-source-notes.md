# CC Switch 源码学习笔记

> 维护者入门参考。所有数据已逐行校验源码（2026-05-27）。
> 每个模块用"接口 → 实现 → 陷阱"三段式。

---

## 第 1 章：架构全景

目标：回答"数据怎么流动"。

### 1.1 应用生命周期

启动链路（`main.rs` → `lib.rs` → 窗口）：

```text
main.rs:4                         // 22 行，仅设置 Linux WebKit 环境变量
  └─ cc_switch_lib::run()         // src-tauri/src/lib.rs:203
       ├─ panic_hook::setup_panic_hook()  // lib.rs:205
       ├─ tauri::Builder::default()       // lib.rs:207
       ├─ .plugin(single_instance)        // lib.rs:211  防止多实例
       ├─ .plugin(deep_link)              // lib.rs:252
       ├─ .on_window_event()              // lib.rs:254  拦截关闭，最小化到托盘
       ├─ .plugin(process)                // lib.rs:275
       ├─ .plugin(dialog)                 // lib.rs:276
       ├─ .plugin(opener)                 // lib.rs:277
       ├─ .plugin(store)                  // lib.rs:278  前端持久化存储
       ├─ .plugin(window_state)           // lib.rs:279
       ├─ .setup(|app| {                 // lib.rs:284
       │    ├─ app_store::refresh()       // lib.rs:288
       │    ├─ init log plugin            // lib.rs:317
       │    ├─ Database::init()           // lib.rs:383  SQLite + schema 迁移
       │    ├─ migrate_from_json()        // lib.rs:403  JSON→SQLite 迁移
       │    ├─ AppState::new(db)          // lib.rs:423
       │    ├─ proxy_service.set_app_handle() // lib.rs:426
       │    ├─ init_default_skill_repos()     // lib.rs:433
       │    ├─ skills SSOT migration          // lib.rs:443
       │    ├─ import live configs            // lib.rs:496-529
       │    ├─ seed official providers         // lib.rs:531
       │    ├─ import additive mode providers // lib.rs:579-599
       │    ├─ import OMO configs             // lib.rs:602-650
       │    ├─ import MCP servers             // lib.rs:653-695
       │    ├─ import prompts                 // lib.rs:698-720
       │    ├─ register deep link handler     // lib.rs:768
       │    ├─ create tray menu               // lib.rs:794
       │    ├─ app.manage(app_state)          // lib.rs:845
       │    ├─ init SkillService              // lib.rs:861
       │    ├─ init CopilotAuthManager        // lib.rs:871
       │    ├─ init CodexOAuthManager         // lib.rs:883
       │    ├─ init global proxy client       // lib.rs:893
       │    ├─ initialize_common_config_snippets() // lib.rs:1601
       │    ├─ restore_proxy_state_on_startup()    // lib.rs:1558
       │    ├─ session usage sync loop        // lib.rs:999
       │    └─ silent startup or show window  // lib.rs:1041
       ├─ .invoke_handler(...)     // lib.rs:1072  注册 ~271 个命令
       └─ .run()                   // lib.rs:1379
```

关键点：
- `main.rs` 仅 22 行，设置 Linux WebKit 环境变量后调用 `lib::run()`
- `lib.rs`（1825 行）是整个后端的"上帝文件"
- `.setup()` 闭包约 790 行（284-1070），包含所有初始化逻辑
- `.invoke_handler()` 注册约 271 个 Tauri 命令（1072-1377）
- 9 个插件被注册（single_instance、deep_link、process、dialog、opener、store、window_state、updater、log）

**退出流程**（`lib.rs:1383`）：
- 用户主动退出时，先保存窗口状态（`lib.rs:1401`）
- 然后 `cleanup_before_exit()`（`lib.rs:1513`）恢复 live 配置
- 使用 `stop_with_restore_keep_state()`（`lib.rs:1531`）保留代理状态
- 短暂等待 100ms 确保 I/O 刷新（`lib.rs:1406`）

### 1.2 数据流：一次 Provider Switch 的完整调用链

以"用户在 UI 里点击切换 Claude Code 的 provider"为例：

```text
前端 (React)
  │  useProviderActions.ts → invoke("switch_provider", { appType, providerId })
  │
  ▼
Tauri IPC 层
  │  lib.rs:1079 注册 commands::switch_provider
  │
  ▼
Rust 命令处理器 (commands/provider.rs)
  │  fn switch_provider(state, app_type, provider_id)
  │    → state.db.get_provider(provider_id)      // 从 SQLite 取 provider
  │    → services::provider::switch_provider()    // 写配置文件
  │
  ▼
services/provider/mod.rs
  │  switch_provider()
  │    → read_live_settings()                     // 读取当前 live 配置
  │    → build_effective_settings_with_common_config()  // 合并公共配置
  │    → write_live_with_common_config()          // 写入目标工具的配置文件
  │
  ▼
config.rs
  │  write_json_file(path, config)               // 原子写入
  │    → atomic_write(path, data)                // 临时文件 + rename
  │
  ▼
文件系统
  ~/.claude/settings.json  ← Claude Code 读取这个文件
```

**Switch vs Additive 两种模式**（`app_config.rs:373`）：

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

**代理模式下的调用链**：

```text
前端 → invoke("switch_proxy_provider", { app_type, provider_id })
  → ProxyService::hot_switch_provider()          // services/proxy.rs
    → switch_locks.acquire(app_type)             // 防止并发切换
    → 更新内存中的路由表（current_providers）
    → 重写 live 配置，把 API key 替换为 PROXY_TOKEN_PLACEHOLDER 占位符
    → 设置 base URL 为 localhost:代理端口
    → 发射 Tauri 事件通知前端
    → 释放锁
```

### 1.3 状态管理

**后端状态**（`store.rs:6`）：

```rust
pub struct AppState {           // src-tauri/src/store.rs:6
    pub db: Arc<Database>,           // SQLite 连接（Mutex 包装）
    pub proxy_service: ProxyService, // 代理服务器管理
    pub usage_cache: Arc<UsageCache>,// 用量统计缓存
}
```

`Arc<T>` = 原子引用计数，允许多个地方共享同一份数据（`store.rs:3`）。
`Database` 内部用 `Mutex<Connection>` 包装（`database/mod.rs:76`），因为 `rusqlite::Connection` 不是 `Sync` 的。

**ProxyService**（`services/proxy.rs:55`）：

```rust
pub struct ProxyService {       // src-tauri/src/services/proxy.rs:55
    db: Arc<Database>,
    server: Arc<RwLock<Option<ProxyServer>>>,
    app_handle: Arc<RwLock<Option<tauri::AppHandle>>>,
    switch_locks: SwitchLockManager,
}
```

**设置缓存**（`settings.rs:519`）：

```rust
static SETTINGS_STORE: OnceLock<RwLock<AppSettings>> = OnceLock::new();  // settings.rs:519
```

- `OnceLock` = 全局只初始化一次
- `RwLock` = 读写锁，多读单写
- 通过 `settings_store()` 函数访问（`settings.rs:521`）
- 读流程：`load_from_file()` 先读文件 → 反序列化 → 缓存到内存
- 写流程：`mutate_settings()`（`settings.rs:574`）→ 读 → clone → 修改 → 写文件 → 更新内存缓存
- `mutate_settings` 是私有函数（非 `pub`），参数名是 `mutator` 不是 `f`

**前端状态**（React）：

```text
App.tsx
  ├─ localStorage("currentView")     ← 当前视图状态
  ├─ useQuery(["providers"])          ← React Query 缓存 provider 列表
  ├─ useTauriEvent("provider-changed") ← 监听后端事件刷新 UI
  └─ useProxyStatus()                 ← 轮询代理状态
```

### 1.4 模块依赖全景图

```text
                    ┌─────────────┐
                    │   main.rs   │  22 行
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   lib.rs    │  1825 行，声明 36 个模块
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
   │  commands/  │  │  services/ │  │   proxy/    │
   │ 34 个子模块 │  │ 25 个子模块│  │ 35+ 个模块  │
   └──────┬──────┘  └─────┬──────┘  └──────┬──────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
   │  database/  │  │   config   │  │  settings   │
   │ SQLite+DAO  │  │ 路径/IO    │  │  全局配置   │
   └─────────────┘  └────────────┘  └─────────────┘
```

---

## 第 2 章：Tauri/Rust 基础速查

不需要学完整个 Rust，只需要理解这些在 cc-switch 里反复出现的模式。

### 2.1 你会反复遇到的 Rust 概念

| 概念 | 一句话解释 | cc-switch 里的例子 |
|------|-----------|-------------------|
| `Arc<T>` | 原子引用计数，多线程共享数据 | `AppState.db: Arc<Database>`（`store.rs:7`） |
| `Mutex<T>` | 互斥锁，同一时间只有一个线程能访问 | `Database.conn: Mutex<Connection>`（`database/mod.rs:77`） |
| `RwLock<T>` | 读写锁，多读单写 | `SETTINGS_STORE: OnceLock<RwLock<AppSettings>>`（`settings.rs:519`） |
| `OnceLock<T>` | 全局只初始化一次的值 | 同上 |
| `Result<T, E>` | 可能成功(T)也可能失败(E)的返回值 | 几乎所有函数的返回类型 |
| `?` 操作符 | 提前返回错误的语法糖 | `let config = read_json_file(path)?;` |
| `#[tauri::command]` | 标记函数为 Tauri IPC 命令 | `commands/` 目录下的所有函数 |
| `serde` | 序列化/反序列化框架 | `#[derive(Serialize, Deserialize)]` 到处都是 |
| `tokio::spawn` | 异步任务 | 代理服务器启动、后台检查等 |
| `thiserror` | 自动派生 Error trait | `error.rs:6` 的 `AppError` |
| `impl From<X> for Y` | 类型转换 | `CircuitBreakerConfig::from(&AppProxyConfig)`（`circuit_breaker.rs:51`） |
| `#[serde(rename_all)]` | JSON 字段命名风格转换 | `camelCase` vs `snake_case` |
| `matches!` | 模式匹配宏，返回 bool | `is_additive_mode()`（`app_config.rs:374`） |

### 2.2 你不需要深入的

| 概念 | 说明 |
|------|------|
| 生命周期标注 `'a` | cc-switch 里几乎不用，只在 `tauri::State<'_, AppState>` 出现 |
| trait object (`dyn Trait`) | 用得很少 |
| `unsafe` | 搜索了一下，项目里没有 |
| 泛型约束 (`where T: ...`) | 有但不复杂，跟着类型提示走就行 |
| 宏 (`macro_rules!`) | 只有 `lock_conn!` 一个自定义宏（`database/mod.rs:61`） |

### 2.3 常见模式速查

**读取配置文件并处理错误**（`config.rs`）：

```rust
let content = std::fs::read_to_string(&path)
    .map_err(|e| AppError::io(&path, e))?;
let config: MyConfig = serde_json::from_str(&content)
    .map_err(|e| AppError::json(&path, e))?;
```

**Tauri 命令的标准签名**（`commands/`）：

```rust
#[tauri::command]
async fn get_providers(
    state: tauri::State<'_, AppState>,  // 自动注入全局状态
) -> Result<Vec<Provider>, AppError> {
    // 返回 Result，自动转为 JS 的 reject
}
```

**原子写入**（`config.rs:204`）：

```rust
pub fn atomic_write(path: &Path, data: &[u8]) -> Result<(), AppError> {
    // 写入临时文件后 rename 替换，避免半写状态
}
```

**Mutex 锁获取**（`database/mod.rs:61`）：

```rust
macro_rules! lock_conn {
    ($mutex:expr) => {
        $mutex
            .lock()
            .map_err(|e| AppError::Database(format!("Mutex lock failed: {}", e)))?
    };
}
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

**enum 与 match**：

```rust
match app_type {
    AppType::Claude => "claude",
    AppType::Codex => "codex",
    _ => "unknown",
}
// 或用 matches! 宏
if matches!(app_type, AppType::OpenCode | AppType::OpenClaw | AppType::Hermes) {
    // additive mode
}
```

**所有权和借用**：

```rust
let db = Arc::new(Database::init()?);  // 创建 Arc
let db_clone = db.clone();             // 克隆 Arc（增加引用计数）
let conn = self.conn.lock()?;          // MutexGuard，离开作用域自动释放
let mut settings = settings_store().write()?; // 写锁
```

**闭包作为参数**（`settings.rs:574`）：

```rust
fn mutate_settings<F>(mutator: F) -> Result<(), AppError>  // 注意：不是 pub，参数名是 mutator
where
    F: FnOnce(&mut AppSettings),
{
    let mut guard = settings_store().write().unwrap_or_else(|e| {
        log::warn!("设置锁已毒化，使用恢复值: {e}");
        e.into_inner()  // 即使锁被 poisoned 也能恢复
    });
    let mut next = guard.clone();
    mutator(&mut next);
    next.normalize_paths();
    save_settings_file(&next)?;
    *guard = next;
    Ok(())
}
```

---

## 第 3 章：后端核心模块

按依赖顺序读，不是按文件大小。

### 3.1 config.rs — 路径解析和文件 I/O（13.9KB，424 行）

**接口**：提供所有模块需要的路径解析和文件读写工具函数。

**核心函数**：
- `get_home_dir()` → `~` 目录（支持 `CC_SWITCH_TEST_HOME` 测试覆盖）
- `get_app_config_dir()` → `~/.cc-switch/`（`config.rs:90`）
- `get_claude_config_dir()` → `~/.claude/`（`config.rs:37`）
- `get_claude_settings_path()` → `~/.claude/settings.json`（`config.rs:74`）
- `read_json_file<T>(path)` → 读文件并反序列化（`config.rs:153`）
- `write_json_file<T>(path, data)` → 序列化并写入，键按字母排序（`config.rs:181`）
- `atomic_write(path, data)` → 临时文件 + rename 的安全写入（`config.rs:204`）
- `write_text_file(path, data)` → 原子写入纯文本（`config.rs:196`）
- `copy_file(from, to)` → 复制文件（`config.rs:394`）
- `delete_file(path)` → 删除文件（`config.rs:403`）

**实现亮点**：
- 所有路径函数都支持环境变量覆盖（`CC_SWITCH_TEST_HOME`），方便测试
- `atomic_write` 用 `write_to_tmp + rename` 避免写入中断导致文件损坏
- `write_json_file` 会递归排序 JSON 键（`sort_json_keys`，`config.rs:164`），确保确定性输出

**陷阱**：
- `get_home_dir()` 在 Windows 上使用 `dirs::home_dir()`，不使用 `HOME` 环境变量（可能被 Git/Cygwin 注入）
- 路径硬编码了 `~/.claude` 等，如果用户自定义了配置目录会出问题

### 3.2 error.rs — 错误模型（3.4KB，146 行）

**接口**：统一的错误类型 `AppError`（`error.rs:6`），所有后端函数都用它。

**AppError 枚举**（`error.rs:7-63`）：

| 变体 | 行号 | 触发场景 |
|------|------|---------|
| `Config(String)` | :8 | 配置错误 |
| `InvalidInput(String)` | :10 | 无效输入 |
| `Io { path, source }` | :12 | 文件 I/O 错误 |
| `IoContext { context, source }` | :18 | 带上下文的 I/O 错误 |
| `Json { path, source }` | :24 | JSON 解析错误 |
| `JsonSerialize { source }` | :30 | JSON 序列化失败 |
| `Toml { path, source }` | :35 | TOML 解析错误 |
| `Lock(String)` | :41 | 锁获取失败 |
| `McpValidation(String)` | :43 | MCP 校验失败 |
| `Message(String)` | :45 | 通用消息 |
| `HttpStatus { status, body }` | :47 | HTTP 错误 |
| `Localized { key, zh, en }` | :50 | 中英双语错误 |
| `Database(String)` | :56 | 数据库错误 |
| `OmoConfigNotFound` | :58 | OMO 配置不存在 |
| `AllProvidersCircuitOpen` | :60 | 所有供应商已熔断 |
| `NoProvidersConfigured` | :62 | 未配置供应商 |

**亮点**：
- `Localized` 变体支持中英双语错误消息（`error.rs:50`），前端根据语言选择显示
- `Io` 变体包含文件路径，方便调试
- `From<PoisonError<T>>` 自动转换（`error.rs:96`）
- `From<rusqlite::Error>` 自动转换（`error.rs:102`）
- `impl Serialize` 支持 JSON 序列化给前端（`error.rs:114`）

**陷阱**：
- `Config(String)` 太宽泛，很多不同类型的错误都往这里塞
- 错误消息不一致，有的用英文有的用中文

### 3.3 app_config.rs — 多应用配置模型（41.0KB，1183 行）

**接口**：定义 cc-switch 管理的 7 个 AI 工具的抽象。

**AppType 枚举**（`app_config.rs:341`）：

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AppType {
    Claude,
    #[serde(rename = "claude-desktop", alias = "claude_desktop", alias = "claudeDesktop")]
    ClaudeDesktop,
    Codex,
    Gemini,
    OpenCode,
    OpenClaw,
    Hermes,
}
```

**关键设计决策 — `is_additive_mode()`**（`app_config.rs:373`）：

```rust
pub fn is_additive_mode(&self) -> bool {
    matches!(self, AppType::OpenCode | AppType::OpenClaw | AppType::Hermes)
}
```

这个分类影响整个架构：
- Switch 模式（4 个工具）：同一时间只有一个 provider 生效
- Additive 模式（3 个工具）：所有 provider 同时写入

**其他重要类型**：
- `McpApps`（`app_config.rs:9`）— 哪些工具支持 MCP server 配置
- `SkillApps`（`app_config.rs:78`）— 哪些工具支持 skills
- `CommonConfigSnippets`（`app_config.rs:419`）— 跨工具共享的配置片段
- `MultiAppConfig`（`app_config.rs:469`）— 旧版 JSON 配置格式（用于迁移）
- `McpServer`（`app_config.rs:222`）— MCP 服务器定义
- `McpRoot`（`app_config.rs:254`）— MCP 根配置（新旧结构并存）

**陷阱**：
- 41KB 太大，包含了太多职责
- `AppType` 的 match 到处都是（`McpApps:24`、`VisibleApps:66`、`CommonConfigSnippets:439`），加新工具需要改 10+ 处

### 3.4 provider.rs — 核心数据模型（40.5KB，1153 行）

**接口**：Provider 是 cc-switch 的核心数据单元（`provider.rs:10`）。

**Provider 结构体**（`provider.rs:10-43`）：

```rust
pub struct Provider {
    pub id: String,                    // 唯一标识
    pub name: String,                  // 显示名称
    #[serde(rename = "settingsConfig")]
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

**Provider 方法**（`provider.rs:45+`）：
- `with_id()` — 从现有 ID 创建 provider
- `is_codex_oauth()` — 检测是否为 Codex OAuth
- `is_github_copilot()` — 检测是否为 GitHub Copilot
- `uses_managed_account_auth()` — 检测是否使用托管账户认证

**陷阱**：
- `settings_config` 是 `serde_json::Value`（动态类型），不是强类型的，容易出错
- Provider 和 AppType 的关系是 N:1，但代码里很多地方假设 1:1
- `ProviderMeta` 的类型定义很深，阅读困难

### 3.5 settings.rs — 设置管理（28.8KB，877 行）

**接口**：全局应用设置的读写（`settings.rs:5`）。

**核心机制**：
- `SETTINGS_STORE: OnceLock<RwLock<AppSettings>>`（`settings.rs:519`）— 全局设置缓存
- `settings_store()` 函数（`settings.rs:521`）— 获取缓存的入口
- `mutate_settings(mutator)`（`settings.rs:574`）— 修改设置的唯一入口（私有函数）

**VisibleApps**（`settings.rs:28`）：

```rust
pub struct VisibleApps {
    pub claude: bool,           // 默认 true
    pub claude_desktop: bool,   // 默认 true
    pub codex: bool,            // 默认 true
    pub gemini: bool,           // 默认 true
    pub opencode: bool,         // 默认 true
    pub openclaw: bool,         // 默认 true
    pub hermes: bool,           // 默认 false，需用户手动启用
}
```

**陷阱**：
- `mutate_settings` 是私有函数，外部模块不能直接调用
- `unwrap_or_else` 处理锁中毒（`settings.rs:578`），但仍然可能 panic
- 写入失败时内存缓存和文件可能不一致

### 3.6 各工具 config 模块对比

| 工具 | 文件 | 实际大小 | 配置路径 |
|------|------|---------|---------|
| Claude Code | services/provider/mod.rs | 105.5KB | `~/.claude/settings.json` |
| Claude Desktop | claude_desktop_config.rs | 61.4KB | 平台相关 |
| Codex CLI | codex_config.rs | 66.4KB | `~/.codex/config.json` |
| Gemini CLI | gemini_config.rs | 20.4KB | `~/.gemini/settings.json` |
| OpenCode | opencode_config.rs | 6.9KB | `~/.opencode/config.json` |
| OpenClaw | openclaw_config.rs | 34.9KB | `~/.openclaw/config.json` |
| Hermes | hermes_config.rs | 69.0KB | `~/.hermes/config.yaml` |

**注意**：Claude Code 没有独立的 `claude_config.rs` 文件！它的配置管理在 `services/provider/mod.rs`（105.5KB）中。

**共同模式（每个模块都有）**：
1. `read_xxx_config()` — 读取工具的配置文件
2. `write_xxx_config()` — 写入工具的配置文件
3. `build_live_config()` — 构建当前生效的配置
4. `switch_provider()` — 切换 provider 的核心逻辑
5. `import_from_live()` — 从工具的 live 配置导入 provider

**AI Slop 特征**：
- 每个模块的 `switch_provider()` 逻辑高度相似，但没有抽取公共函数
- `codex_config.rs`（66.4KB）和 `hermes_config.rs`（69.0KB）明显过大
- 没有统一的 config trait 或接口

### 3.7 database/ — 数据持久化（SQLite）

**核心结构**（`database/mod.rs:76`）：

```rust
pub struct Database {
    pub(crate) conn: Mutex<Connection>,
}
```

**模块结构**：
- `mod.rs`（9.1KB）— Database 结构体 + 初始化
- `schema.rs`（79.7KB）— 表结构定义 + Schema 迁移（当前版本 `SCHEMA_VERSION = 10`，`mod.rs:52`）
- `backup.rs`（32.5KB）— SQL 导入导出 + 快照备份
- `migration.rs`（9.5KB）— JSON → SQLite 数据迁移
- `dao/` — 数据访问对象（12 个文件）：
  - `providers.rs`（786 行）— Provider CRUD
  - `proxy.rs`（952 行）— 代理配置
  - `usage_rollup.rs`（377 行）— 用量统计
  - `settings.rs`（327 行）— 通用设置
  - `skills.rs`（263 行）— Skills 管理
  - `failover.rs`（149 行）— 故障转移队列
  - `mcp.rs`（106 行）— MCP 服务器配置
  - `prompts.rs`（88 行）— Prompt 管理
  - `providers_seed.rs`（94 行）— 官方预设种子数据
  - `stream_check.rs`（74 行）— 流式检查配置
  - `universal_providers.rs`（74 行）— 通用 Provider
  - `mod.rs`（19 行）— 模块声明

**关键设计**：
- `lock_conn!` 宏（`mod.rs:61`）安全获取 Mutex 锁，避免 unwrap panic
- `to_json_string()`（`mod.rs:55`）安全序列化 JSON
- 数据库变更钩子（`mod.rs:80`）通知 WebDAV 自动同步

**DAO 模式**：
- 每个 DAO 模块负责一个表的 CRUD 操作
- 通过 `impl Database` 添加方法，不暴露内部连接
- 所有数据库操作都通过 `lock_conn!` 宏获取锁

**陷阱**：
- `Mutex<Connection>` 意味着同一时间只有一个线程能访问数据库
- Schema 迁移是线性的（`schema.rs` 2050 行），如果迁移失败可能导致数据库损坏
- 没有连接池，每次操作都用同一个连接

### 3.8 services/ — 业务逻辑层

**模块结构**（`services/mod.rs`，25 个子模块）：

| 模块 | 实际大小 | 职责 |
|------|---------|------|
| provider/mod.rs | 105.5KB | Provider 业务逻辑（CRUD、切换、导入导出） |
| proxy.rs | 141.3KB | ProxyService（启动、停止、接管、热切换） |
| usage_stats.rs | 114.6KB | 用量统计 |
| skill.rs | 104.7KB | Skills 管理 |
| stream_check.rs | 80.9KB | 流式检查 |
| subscription.rs | 1.3KB | 订阅管理 |
| coding_plan.rs | 607B | Coding Plan |
| mcp.rs | 16.4KB | MCP 服务器管理 |
| prompt.rs | 8.6KB | Prompt 管理 |
| config.rs | 9.7KB | ConfigService（配置文件读写） |
| speedtest.rs | 5.9KB | 端点速度测试 |
| balance.rs | 418B | 余额查询 |
| model_fetch.rs | 414B | 模型列表获取 |
| env_checker.rs | 168B | 环境变量检查 |
| env_manager.rs | 240B | 环境变量管理 |
| webdav.rs | 554B | WebDAV 客户端 |
| webdav_sync.rs | 884B | WebDAV 同步逻辑 |
| webdav_auto_sync.rs | 274B | 自动同步 |
| session_usage.rs | 682B | Claude 会话用量同步 |
| session_usage_codex.rs | 787B | Codex 会话用量同步 |
| session_usage_gemini.rs | 494B | Gemini 会话用量同步 |
| omo.rs | 560B | OMO 集成 |

**陷阱**：
- `provider/mod.rs`（105.5KB）和 `proxy.rs`（141.3KB）太大，应该拆分
- 有些逻辑直接放在 `commands/` 里，没有经过 services 层
- 没有统一的 service trait 或接口

---

## 第 4 章：本地代理子系统

这是项目里最复杂的部分。

### 4.1 proxy/ 目录结构

```text
src-tauri/src/proxy/
├── server.rs           # 388 行，HTTP 服务器（Axum）
├── forwarder.rs        # 3100 行，请求转发（122.1KB）
├── circuit_breaker.rs  # 495 行，熔断器
├── provider_router.rs  # 523 行，多 provider 路由
├── failover_switch.rs  # 故障转移切换
├── switch_lock.rs      # 切换锁（防止并发切换）
├── handlers/           # 请求处理器
├── providers/          # 格式转换器
│   ├── claude.rs       # Anthropic API 格式
│   ├── codex_chat_history.rs
│   ├── copilot_auth.rs
│   ├── codex_oauth_auth.rs
│   ├── gemini_shadow.rs
│   └── ...
├── providers/transform_codex_chat.rs  # 71.1KB，Codex Chat 格式转换
├── providers/transform_gemini.rs      # 78.1KB，Gemini 格式转换
├── providers/transform_responses.rs   # 61.5KB，通用响应转换
├── providers/transform.rs             # 58.3KB，通用请求转换
├── copilot_optimizer.rs               # 57.9KB，Copilot 优化器
├── thinking_rectifier.rs              # 23.0KB，思维整流器
├── thinking_budget_rectifier.rs       # 11.1KB，思维预算整流
├── body_filter.rs                     # 10.5KB，请求体过滤
├── model_mapper.rs                    # 10.4KB，模型映射
├── types.rs                           # 共享类型定义
├── log_codes.rs                       # 日志代码常量
└── http_client.rs                     # 全局 HTTP 客户端
```

**技术栈**：Axum（HTTP）+ Tower（中间件）+ Hyper（底层）+ Tokio（异步）
**RequestForwarder**（`proxy/forwarder.rs:89`）— 核心转发器：
```rust
pub struct RequestForwarder {  // proxy/forwarder.rs:89
    router: Arc<ProviderRouter>,
    status: Arc<RwLock<ProxyStatus>>,
    current_providers: Arc<RwLock<HashMap<String, (String, String)>>>,
    max_attempts: usize,  // max_retries + 1
}
```
**ActiveConnectionGuard RAII 模式**（`proxy/forwarder.rs:61`）：
```rust
pub(crate) struct ActiveConnectionGuard {  // proxy/forwarder.rs:61
    status: Arc<RwLock<ProxyStatus>>,
}
impl Drop for ActiveConnectionGuard {
    fn drop(&mut self) {
        // Drop 不能 await：用 tokio::spawn 调度异步减量
        let status = self.status.clone();
        if let Ok(handle) = tokio::runtime::Handle::try_current() {
            handle.spawn(async move {
                let mut s = status.write().await;
                s.active_connections = s.active_connections.saturating_sub(1);
            });
        }
    }
}
```
**命名不一致的 AI Slop**：
- `PROXY_AUTH_PLACEHOLDER`（`forwarder.rs:35`）和 `PROXY_TOKEN_PLACEHOLDER`（`services/proxy.rs:22`）值都是 `"PROXY_MANAGED"`，但常量名不同
### 4.2 ProxyState 和 ProxyServer

**ProxyState**（`proxy/server.rs:34`）：

```rust
pub struct ProxyState {
    pub db: Arc<Database>,
    pub config: Arc<RwLock<ProxyConfig>>,
    pub status: Arc<RwLock<ProxyStatus>>,
    pub start_time: Arc<RwLock<Option<std::time::Instant>>>,
    pub current_providers: Arc<RwLock<HashMap<String, (String, String)>>>,
    pub provider_router: Arc<ProviderRouter>,
    pub gemini_shadow: Arc<GeminiShadowStore>,
    pub codex_chat_history: Arc<CodexChatHistoryStore>,
    pub app_handle: Option<tauri::AppHandle>,
    pub failover_manager: Arc<FailoverSwitchManager>,
}
```

**ProxyServer**（`proxy/server.rs:54`）：
- `ProxyServer::new()` 创建 `ProxyState` 并初始化所有共享组件
- `ProxyServer::start()` 绑定端口、启动 Axum 路由
- `ProxyServer::stop()` 发送 shutdown 信号、等待服务器关闭

### 4.3 认证和路由

**ProviderRouter**（`proxy/provider_router.rs`，523 行）：

```text
客户端请求 → ProviderRouter
  ├─ 从请求头解析 API key
  ├─ 匹配到对应的 provider
  ├─ 检查熔断器状态
  │    ├─ Closed → 正常转发
  │    ├─ Open → 拒绝，返回 503
  │    └─ HalfOpen → 尝试转发，成功则关闭熔断
  └─ 转发到 provider 的 base URL
```

### 4.4 故障转移和熔断

**CircuitBreaker**（`proxy/circuit_breaker.rs:76`）：

```rust
pub struct CircuitBreaker {
    state: Arc<RwLock<CircuitState>>,
    consecutive_failures: Arc<AtomicU32>,
    consecutive_successes: Arc<AtomicU32>,
    total_requests: Arc<AtomicU32>,
    total_failures: Arc<AtomicU32>,
    last_failure_time: Arc<RwLock<Option<Instant>>>,
    config: CircuitBreakerConfig,
}
```

**CircuitBreakerConfig 默认值**（`circuit_breaker.rs:63`）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| failure_threshold | 4 | 连续失败多少次后打开 |
| success_threshold | 2 | 半开状态下成功多少次后关闭 |
| timeout_seconds | 60 | 打开后多久尝试半开 |
| error_rate_threshold | 0.6 | 错误率超过 60% 时打开 |
| min_requests | 10 | 计算错误率前的最小请求数 |

**状态转换**：

```text
Closed（正常）
  │ 连续失败 >= 4
  ▼
Open（熔断）
  │ 等待 60 秒
  ▼
HalfOpen（半开）
  │ 连续成功 >= 2 → Closed
  │ 任何失败 → Open
```

### 4.5 代理接管（Takeover）机制

**接管流程**（`services/proxy.rs`）：

```text
1. 用户点击"启用代理"
2. 前端调用 set_proxy_takeover_for_app
3. ProxyService 读取目标工具的 live 配置
4. 备份 live 配置到数据库
5. 修改 live 配置：
   - 设置 base_url 为 http://localhost:代理端口
   - 设置 api_key 为 PROXY_TOKEN_PLACEHOLDER 占位符（services/proxy.rs:22）
   - 设置模型别名（claude-haiku-4-5, claude-sonnet-4-6, claude-opus-4-7）
6. 写入修改后的 live 配置
7. 启动代理服务器（如果还没启动）
8. 发射 Tauri 事件通知前端
```

**热切换**（`services/proxy.rs`）：
- 代理运行时切换 provider，不需要重启
- 通过 `hot_switch_provider()` 方法实现
- 使用 `SwitchLockManager` 防止并发切换

**恢复流程**：
- 应用退出时，`cleanup_before_exit()`（`lib.rs:1513`）恢复 live 配置
- 使用 `stop_with_restore_keep_state()`（`lib.rs:1531`）保留代理状态
- 下次启动时自动恢复（`restore_proxy_state_on_startup()`，`lib.rs:1558`）
- 只恢复 claude、codex、gemini 三个应用（`lib.rs:1561`）

---

## 第 5 章：前端架构

前端是 React + TypeScript，通过 Tauri IPC 与 Rust 后端通信。

### 5.1 App.tsx — 视图路由机制（1604 行）

**App.tsx** 是前端的"上帝文件"（`src/App.tsx`）。

**视图切换实现**：

```typescript
const [currentView, setCurrentView] = useState(
  localStorage.getItem("currentView") || "providers"
);
```

所有视图都在一个 switch 语句里，没有使用 React Router。

**AI Slop 特征**：
- 1604 行的单文件，应该拆分
- 所有视图都在一个 switch 里，没有用路由库
- 没有代码分割，首屏加载慢

### 5.2 hooks/ — 状态管理层

**核心 hooks**（`src/hooks/`，25 个文件，3642 行）：

| Hook | 文件 | 行数 | 职责 |
|------|------|------|------|
| useSettings | useSettings.ts | 505 | 设置的读写 |
| useProviderActions | useProviderActions.ts | 385 | Provider CRUD（React Query mutations） |
| useDirectorySettings | useDirectorySettings.ts | 373 | 工具目录配置 |
| useSkills | useSkills.ts | 358 | Skills 管理 |
| useProxyStatus | useProxyStatus.ts | 245 | 代理状态轮询（每 2 秒） |
| useSettingsForm | useSettingsForm.ts | 203 | 设置表单状态 |
| useImportExport | useImportExport.ts | 203 | 导入导出 |
| useHermes | useHermes.ts | 174 | Hermes 特定功能 |
| usePromptActions | usePromptActions.ts | 152 | Prompt CRUD |
| useOpenClaw | useOpenClaw.ts | 144 | OpenClaw 特定功能 |
| useStreamCheck | useStreamCheck.ts | 140 | 流式检查 |
| useDragSort | useDragSort.ts | 119 | 拖拽排序 |
| useGlobalProxy | useGlobalProxy.ts | 109 | 全局代理 |
| useMcp | useMcp.ts | 74 | MCP 管理 |
| useSessionSearch | useSessionSearch.ts | 72 | 会话搜索 |
| useSettingsMetadata | useSettingsMetadata.ts | 61 | 设置元数据 |
| useBackupManager | useBackupManager.ts | 59 | 备份管理 |
| useAutoCompact | useAutoCompact.ts | 52 | 自动压缩 |
| useProxyConfig | useProxyConfig.ts | 48 | 代理配置 |
| useUsageCacheBridge | useUsageCacheBridge.ts | 43 | 用量缓存桥接 |
| useTauriEvent | useTauriEvent.ts | 39 | 监听 Tauri 后端事件 |
| useDarkMode | useDarkMode.ts | 29 | 暗色模式 |
| useLastValidValue | useLastValidValue.ts | 20 | 上次有效值 |
| useSkills.helpers | useSkills.helpers.ts | 19 | Skills 辅助函数 |
| useDebouncedValue | useDebouncedValue.ts | 16 | 防抖值 |
**useProviderActions 内部实现**（`src/hooks/useProviderActions.ts:31`）：
```typescript
export function useProviderActions(
    activeApp: AppId,
    isProxyRunning?: boolean,
    isProxyTakeover?: boolean,
) {
    const addProviderMutation = useAddProviderMutation(activeApp);
    const updateProviderMutation = useUpdateProviderMutation(activeApp);
    const deleteProviderMutation = useDeleteProviderMutation(activeApp);
    const switchProviderMutation = useSwitchProviderMutation(activeApp);
}
```
**AI Slop 特征**：
- `useProviderActions` 有 385 行，但大部分是 Claude 插件同步逻辑（`syncClaudePlugin`，`useProviderActions.ts:45`）
- Claude 插件同步逻辑应该抽到独立 hook

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

### 5.3 config/ — preset 数据

| 文件 | 实际大小 |
|------|---------|
| openclawProviderPresets.ts | 52.4KB |
| opencodeProviderPresets.ts | 42.6KB |
| codexProviderPresets.ts | 32.5KB |
| claudeProviderPresets.ts | 35.6KB |
| claudeDesktopProviderPresets.ts | 26.9KB |
| hermesProviderPresets.ts | 35.1KB |
| geminiProviderPresets.ts | 9.2KB |
| universalProviderPresets.ts | 3.0KB |
| **合计** | **237.3KB** |

**AI Slop 特征**：
- 8 个文件结构几乎一样，但没有抽取公共模板
- 237KB 的 TypeScript 数据，可以移到 JSON 文件
- 没有类型检查，preset 数据的结构没有 TypeScript 类型定义

### 5.4 前端组件结构

**组件统计**：186 个文件（`.tsx` + `.ts`）

主要组件目录：
- `settings/` — 设置页面组件
- `providers/` — Provider 管理组件
- `proxy/` — 代理状态组件
- `mcp/` — MCP 配置组件
- `skills/` — Skills 管理组件
- `prompts/` — Prompt 管理组件
- `sessions/` — 会话管理组件
- `ui/` — 通用 UI 组件

---

## 第 6 章：AI Slop 特征模式识别

### 6.1 代码膨胀模式

**过大的单文件**：

| 文件 | 行数/大小 | 问题 |
|------|----------|------|
| `lib.rs` | 1825 行 | 模块声明 + 插件注册 + 命令注册 + 初始化逻辑全混在一起 |
| `services/proxy.rs` | 141.3KB (3909 行) | ProxyService 所有方法全在一个文件 |
| `proxy/forwarder.rs` | 122.1KB (3100 行) | 请求转发 + 格式转换 + 错误处理全在一起 |
| `provider/mod.rs` (services) | 105.5KB (2766 行) | ProviderService 所有方法 |
| `skill.rs` (services) | 104.7KB (3127 行) | SkillService 所有方法 |
| `usage_stats.rs` (services) | 114.6KB (3250 行) | UsageStatsService 所有方法 |
| `stream_check.rs` (services) | 80.9KB (2166 行) | StreamCheckService 所有方法 |
| `hermes_config.rs` | 69.0KB | Hermes 配置读写 |
| `codex_config.rs` | 66.4KB | Codex 配置读写 |
| `claude_desktop_config.rs` | 61.4KB | Claude Desktop 配置读写 |
| `App.tsx` | 1604 行 | 14 个视图 + 事件处理 + 状态管理全在一个文件 |

**复制粘贴的 config 模块**：
- 7 个工具的 config 模块结构几乎一样
- 每个都自己实现了一遍 `read → parse → modify → write` 流程
- 没有公共的 config trait 或接口

**冗余的 match 分支**：
- `AppType` 的 match 在 `McpApps`（`app_config.rs:24`）、`VisibleApps`（`settings.rs:66`）、`CommonConfigSnippets`（`app_config.rs:439`）里重复出现
- 每次加新工具都要改 10+ 个 match

### 6.2 过度抽象模式

**动态类型滥用**：
- `Provider.settings_config: Value`（`provider.rs:14`）是 `serde_json::Value`，不是强类型
- 运行时才知道配置是否合法，编译器帮不上忙

**过度的 Option 包装**：
- `Provider` 结构体里很多字段都是 `Option<T>`（`provider.rs:15-38`）
- 有些字段（如 `icon`、`icon_color`）实际上总是有值的

### 6.3 命名和组织问题

**不一致的命名约定**：
- 有的用 `xxx_config`，有的用 `xxx_settings`
- 有的函数叫 `get_xxx`，有的叫 `read_xxx`，有的叫 `fetch_xxx`
- 错误消息有的中文有的英文（`error.rs:50` 的 `Localized` 变体试图解决这个问题，但不彻底）

**模糊的模块边界**：
- `services/` 和 `commands/` 的职责划分不清晰
- `lib.rs` 里的 `initialize_common_config_snippets()`（`lib.rs:1601`）应该在 services 层

**放错地方的代码**：
- `cleanup_before_exit()`（`lib.rs:1513`）是代理相关的逻辑，但放在 lib.rs
- `restore_proxy_state_on_startup()`（`lib.rs:1558`）同理
- `is_chinese_locale()`（`lib.rs:1685`）是通用工具函数，但放在 lib.rs

### 6.4 具体案例清单

| 文件 | 问题 | 建议 |
|------|------|------|
| `lib.rs:1-36` | 36 个 `mod` 声明 | 按功能分组 |
| `lib.rs:284-1070` | `.setup()` 闭包 786 行 | 拆分成 `init_database()`, `init_plugins()`, `seed_data()` |
| `lib.rs:1072-1377` | 271 个命令注册 | 按模块分组 |
| `services/proxy.rs:55` | ProxyService 3909 行 | 拆分成 `takeover.rs`, `hot_switch.rs`, `config.rs` |
| 7 个 config 模块 | 重复的读写逻辑 | 抽取 `ToolConfig` trait |
| 8 个 preset 文件 | 237KB TypeScript 数据 | 移到 JSON 文件 |
| `provider.rs:14` | `settings_config: Value` 动态类型 | 考虑用强类型 enum |
| `error.rs:8` | `Config(String)` 太宽泛 | 拆分成更具体的变体 |
| `settings.rs:519` | `OnceLock<RwLock<>>` + `unwrap_or_else` | 用 `parking_lot::RwLock` 避免 poisoned panic |

---

## 第 7 章：重构路线图

### 7.1 低风险清理（先做，1-2 天）

**删除死代码**：
- 搜索 `#[allow(dead_code)]` 和未使用的函数
- 删除注释掉的代码块
- 删除 `lib.rs:38` 里重复的 `pub use` 导出

**统一命名**：
- `get_xxx` / `read_xxx` / `fetch_xxx` 统一为 `read_xxx`
- 错误消息统一为英文（或统一为中文）

**提取重复模式**：
- 7 个 config 模块的 `read → parse → modify → write` 骨架抽取为公共函数
- 8 个 preset 文件的结构抽取为公共模板
- `AppType` 的 match 分支抽取为 trait 方法

### 7.2 中等重构（3-5 天）

**拆分过大的文件**：
- `lib.rs`（1825 行）→ `init.rs`（初始化逻辑 `lib.rs:284-1070`）+ `lib.rs`（仅模块声明 `lib.rs:1-36`）
- `services/proxy.rs`（141.3KB）→ 拆分成 `takeover.rs`, `hot_switch.rs`, `config.rs`
- `provider/mod.rs`（105.5KB）→ 拆分成多个子模块
- `App.tsx`（1604 行）→ 每个视图一个文件 + `AppRouter.tsx`
- `codex_config.rs`（66.4KB）→ `codex/` 目录
- `hermes_config.rs`（69.0KB）→ `hermes/` 目录
- `claude_desktop_config.rs`（61.4KB）→ `claude_desktop/` 目录

**统一 config 模块的结构**：

```rust
trait ToolConfig {
    fn read_config(&self) -> Result<Value, AppError>;
    fn write_config(&self, config: &Value) -> Result<(), AppError>;
    fn switch_provider(&self, provider: &Provider) -> Result<(), AppError>;
}
```

### 7.3 架构级重构（最后做，慎重，1-2 周）

**Provider 管理的统一抽象**：
- 定义 `ProviderManager` trait
- 每个工具有自己的 `ProviderManager` 实现
- 切换逻辑统一处理，不再分散在各个 config 模块

**代理子系统的简化**：
- `forwarder.rs`（122.1KB）拆分成多个职责单一的模块
- 抽取公共的 API 格式转换框架
- 统一错误处理和日志记录

---

## 附录：文件大小速查表（已验证，2026-05-27）

### Rust 后端

| 文件 | 实际大小 | 行数 |
|------|---------|------|
| lib.rs | — | 1825 |
| main.rs | — | 22 |
| store.rs | — | 23 |
| error.rs | 3.4KB | 146 |
| config.rs | 13.9KB | 424 |
| settings.rs | 28.8KB | 877 |
| provider.rs | 40.5KB | 1153 |
| app_config.rs | 41.0KB | 1183 |
| services/proxy.rs | 141.3KB | 3909 |
| services/provider/mod.rs | 105.5KB | 2766 |
| services/usage_stats.rs | 114.6KB | 3250 |
| services/skill.rs | 104.7KB | 3127 |
| services/stream_check.rs | 80.9KB | 2166 |
| proxy/forwarder.rs | 122.1KB | 3100 |
| proxy/circuit_breaker.rs | — | 495 |
| proxy/provider_router.rs | — | 523 |
| proxy/server.rs | — | 388 |
| database/mod.rs | 9.1KB | 271 |
| database/schema.rs | 79.7KB | 2050 |
| database/backup.rs | 32.5KB | 860 |
| database/migration.rs | 9.5KB | 245 |
| claude_desktop_config.rs | 61.4KB | 1826 |
| codex_config.rs | 66.4KB | 2024 |
| hermes_config.rs | 69.0KB | 1947 |
| openclaw_config.rs | 34.9KB | 1089 |
| gemini_config.rs | 20.4KB | 654 |
| opencode_config.rs | 6.9KB | 233 |

### 前端

| 文件 | 实际大小 |
|------|---------|
| App.tsx | 1604 行 |
| hooks/ 合计 | 3642 行（25 个文件） |
| components/ 合计 | 186 个文件 |
| config/ presets 合计 | 237.3KB（8 个文件） |
