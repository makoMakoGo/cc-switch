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
**初始化流程详解**：
1. **Panic Hook 设置**（`lib.rs:205`）— 崩溃时记录日志到 `~/.cc-switch/crash.log`
2. **单实例检查**（`lib.rs:211`）— 防止多个 cc-switch 实例同时运行
3. **深度链接处理**（`lib.rs:252`）— 处理 `ccs://` 协议的 URL
4. **窗口关闭拦截**（`lib.rs:254`）— 根据设置决定最小化到托盘还是退出
5. **Store 插件初始化**（`lib.rs:278`）— 前端持久化存储
6. **数据库初始化**（`lib.rs:383`）— SQLite + Schema 迁移
7. **JSON → SQLite 迁移**（`lib.rs:403`）— 从旧版本平滑升级
8. **AppState 创建**（`lib.rs:423`）— 组装全局状态
  ▼
Tauri IPC 层
  │  lib.rs 中 invoke_handler 注册的命令
  │
  ▼
9. **默认 Skills 仓库初始化**（`lib.rs:433`）— 首次运行时插入官方 Skills
10. **Provider 种子数据**（`lib.rs:496`）— 遍历 `AppType::all()` 导入默认配置
11. **公共配置片段提取**（`lib.rs:1601`）— 从 live 配置提取公共字段
12. **代理状态恢复**（`lib.rs:1558`）— 启动时恢复上次的代理接管状态
13. **系统托盘创建**（`tray.rs`）— 创建托盘菜单
14. **命令注册**（`lib.rs:1072`）— 注册 ~300 个 Tauri 命令
15. **窗口显示**（`lib.rs:1041`）— 根据设置决定静默启动还是显示窗口
**退出流程**（`lib.rs:1383`）：
- 用户主动退出时，先保存窗口状态（`lib.rs:1401`）
- 然后清理代理状态（`lib.rs:1402`）— 恢复 live 配置，停止代理服务器
- 最后退出应用
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
| `Arc<T>` | 原子引用计数，多线程共享数据 | `AppState.db: Arc<Database>`（`src-tauri/src/store.rs:3`） |
| `Mutex<T>` | 互斥锁，同一时间只有一个线程能访问 | `Database.conn: Mutex<Connection>`（`src-tauri/src/database/mod.rs:76`） |
| `RwLock<T>` | 读写锁，多读单写 | `settings.rs` 的 `APP_SETTINGS: OnceLock<RwLock<AppSettings>>`（`src-tauri/src/settings.rs:5`） |
| `OnceLock<T>` | 全局只初始化一次的值 | 同上，设置缓存 |
| `Result<T, E>` | 可能成功(T)也可能失败(E)的返回值 | 几乎所有函数的返回类型 |
| `?` 操作符 | 提前返回错误的语法糖 | `let config = read_json_file(path)?;`（`src-tauri/src/config.rs`） |
| `#[tauri::command]` | 标记函数为 Tauri IPC 命令 | `commands/` 目录下的所有函数（`src-tauri/src/commands/`） |
| `serde` | 序列化/反序列化框架 | `#[derive(Serialize, Deserialize)]` 到处都是 |
| `tokio::spawn` | 异步任务 | 代理服务器启动（`src-tauri/src/proxy/server.rs`）、后台检查等 |
| `thiserror` | 自动派生 Error trait | `error.rs` 里的 `AppError`（`src-tauri/src/error.rs:6`） |
| `impl From<X> for Y` | 类型转换 | `CircuitBreakerConfig::from(&AppProxyConfig)`（`src-tauri/src/proxy/circuit_breaker.rs:51`） |
| `#[serde(rename_all)]` | JSON 字段命名风格转换 | `camelCase` vs `snake_case`（`src-tauri/src/provider.rs:13`） |
| `impl Default` | 默认值实现 | `CircuitBreakerConfig::default()`（`src-tauri/src/proxy/circuit_breaker.rs:63`） |
| `#[serde(skip_serializing_if)]` | 条件序列化 | `Option::is_none` 时不序列化（`src-tauri/src/provider.rs:15`） |
| `#[serde(alias)]` | 字段别名 | `claude-desktop` 和 `claudeDesktop` 都能反序列化（`src-tauri/src/app_config.rs:344`） |
| `impl Display` | 格式化输出 | `CircuitState::fmt()`（`src-tauri/src/proxy/circuit_breaker.rs:25`） |
### 2.2 你不需要深入的
| 概念 | 说明 |
|------|------|
| 生命周期标注 `'a` | cc-switch 里几乎不用，遇到再查 |
| trait object (`dyn Trait`) | 用得很少 |
| `unsafe` | 搜索了一下，项目里没有 |
| 泛型约束 (`where T: ...`) | 有但不复杂，跟着类型提示走就行 |
| 宏 (`macro_rules!`) | 只有 `lock_conn!` 一个自定义宏 |
**trait 在 cc-switch 中的使用**：
- `Serialize` / `Deserialize` — serde 自动派生，到处都是
- `Display` — 格式化输出（`CircuitState::fmt()`）
- `From` / `Into` — 类型转换（`CircuitBreakerConfig::from()`）
- `Default` — 默认值（`CircuitBreakerConfig::default()`）
- `Error` — 错误类型（`AppError` 通过 `thiserror` 派生）
**为什么 cc-switch 很少用 trait**：
- 大部分逻辑是具体的，不需要抽象
- 没有插件系统，不需要 trait object
- 泛型已经够用，不需要 trait bound
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
**宏的工作原理**：
- `macro_rules!` 定义宏
- `$mutex:expr` 匹配一个表达式
- `.map_err(...)` 转换错误类型
- `?` 提前返回错误
**为什么用宏而不是函数**：
- 宏可以在调用处展开，避免额外的函数调用开销
- 宏可以捕获表达式类型，避免泛型约束
- 宏可以生成代码，减少重复
**其他常用宏**：
- `vec![]` — 创建 Vec
- `format!()` — 格式化字符串
- `println!()` — 打印到标准输出
- `json!()` — 创建 JSON 值（serde_json）
    pub id: String,
    pub name: String,
    #[serde(rename = "settingsConfig")]  // JSON 字段用 camelCase
    pub settings_config: Value,
    #[serde(skip_serializing_if = "Option::is_none")]  // None 时不序列化
    pub website_url: Option<String>,
    #[serde(default)]  // 反序列化时缺失字段用默认值
    pub in_failover_queue: bool,
}
```
**serde 常用场景**：
- JSON 配置文件读写（`read_json_file`, `write_json_file`）
- Tauri IPC 参数传递（`#[tauri::command]` 自动序列化）
- 数据库存储（`to_json_string()`）
- 前端数据传递（`invoke()` 返回值）
        tokio::time::sleep(Duration::from_secs(60)).await;
        // 定期执行的任务
    }
});
// 在 cc-switch 中的使用：
- 代理服务器启动（`src-tauri/src/proxy/server.rs`）
- 后台会话用量同步（`src-tauri/src/lib.rs:1000`）
- 定期检查代理状态
```
**异步错误处理**：
```rust
// 异步函数中的错误传播
async fn fetch_data() -> Result<Data, AppError> {
    let response = reqwest::get(url).await
        .map_err(|e| AppError::Http(e.to_string()))?;
    let data = response.json().await
        .map_err(|e| AppError::Json(e.to_string()))?;
    Ok(data)
}
```
```
**错误处理模式**：
```rust
// 使用 ? 操作符传播错误
fn read_config(path: &Path) -> Result<Config, AppError> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| AppError::io(path, e))?;  // 转换错误类型
    let config: Config = serde_json::from_str(&content)
        .map_err(|e| AppError::json(path, e))?;  // 转换错误类型
    Ok(config)
}
// 使用 map_err 转换错误类型
let conn = self.conn.lock()
    .map_err(|e| AppError::Lock(e.to_string()))?;
// 使用 unwrap_or_default 提供默认值
let settings = APP_SETTINGS.read().unwrap_or_default();
```
**Tauri 命令错误处理**：
```rust
#[tauri::command]
async fn my_command(state: tauri::State<'_, AppState>) -> Result<String, AppError> {
    // 错误会自动转换为 JS 的 reject
    let result = do_something()?;
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
- `mod.rs` — Database 结构体 + 初始化（`src-tauri/src/database/mod.rs:91`）
- `schema.rs` — 表结构定义 + Schema 迁移（当前版本 `SCHEMA_VERSION = 10`，`src-tauri/src/database/mod.rs:52`）
- `backup.rs` — SQL 导入导出 + 快照备份
- `migration.rs` — JSON → SQLite 数据迁移（`src-tauri/src/database/migration.rs`）
- `dao/` — 数据访问对象
  - `providers.rs` — Provider CRUD
  - `mcp.rs` — MCP 服务器配置
  - `prompts.rs` — Prompt 管理
  - `skills.rs` — Skills 管理
  - `settings.rs` — 通用设置存储
**数据库表结构**（`src-tauri/src/database/schema.rs`）：
- `providers` — Provider 数据（id, name, app_type, settings_config, meta, icon 等）
- `mcp_servers` — MCP 服务器配置（id, name, server_config, apps 等）
- `prompts` — Prompt 管理（id, name, content, app_type 等）
- `skills` — Skills 管理（id, name, description, app_type 等）
- `settings` — 通用设置（key, value）
- `failover_queue` — 故障转移队列（provider_id, app_type, priority）
- `proxy_config` — 代理配置（app_type, enabled, config）
- `model_pricing` — 模型定价（model, input_price, output_price）
- `request_logs` — 请求日志（timestamp, provider, model, status 等）
**DAO 模式示例**（`src-tauri/src/database/dao/providers.rs`）：
```rust
// 通过 impl Database 添加方法
impl Database {
    pub fn get_providers(&self, app_type: &str) -> Result<Vec<Provider>, AppError> {
        let conn = lock_conn!(self.conn);
        let mut stmt = conn.prepare("SELECT * FROM providers WHERE app_type = ?1")?;
        let providers = stmt.query_map([app_type], |row| {
            // 从行数据构建 Provider 结构体
            Ok(Provider { ... })
        })?.collect();
        Ok(providers)
    }
}
```
**DAO 模式优点**：
- 封装数据库操作，不暴露 SQL 给业务层
- 通过 `impl Database` 添加方法，不破坏封装
- 使用 `lock_conn!` 宏安全获取锁
- 返回 `Result<T, AppError>`，统一错误处理
**DAO 模式缺点**：
- 没有事务支持，多个相关操作可能部分成功
- 没有连接池，高并发场景可能成为瓶颈
- SQL 字符串硬编码，没有类型安全
**DAO 方法列表**：
**Schema 迁移示例**（`src-tauri/src/database/schema.rs`）：
```rust
// 迁移逻辑示例
fn migrate_v9_to_v10(conn: &Connection) -> Result<(), AppError> {
    // 添加新列
    conn.execute("ALTER TABLE providers ADD COLUMN notes TEXT", [])?;
    // 更新版本号
    conn.execute("PRAGMA user_version = 10", [])?;
    Ok(())
}
```
**Schema 版本控制**：
- 当前版本 `SCHEMA_VERSION = 10`（`src-tauri/src/database/mod.rs:52`）
- 每次修改表结构时递增版本号
- 迁移逻辑在 `schema.rs` 中，按版本顺序执行
- 支持从 JSON 配置文件迁移到 SQLite（`migration.rs`）
**备份触发时机**：
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
### 3.5.5 services/ — 业务逻辑层
**接口**：业务逻辑层，连接 commands/ 和 database/（`src-tauri/src/services/mod.rs`）。
**模块结构**（`src-tauri/src/services/`）：
- `provider/mod.rs`（~2600 行）— Provider 业务逻辑（CRUD、切换、导入导出）
- `proxy.rs`（3910 行）— ProxyService 业务逻辑（启动、停止、接管、热切换）
- `config.rs` — ConfigService（配置文件读写）
- `skill.rs`（~2600 行）— SkillService（Skills 管理）
- `usage_stats.rs`（~2800 行）— UsageStatsService（用量统计）
- `stream_check.rs`（~2000 行）— StreamCheckService（流式检查）
- `mcp.rs` — McpService（MCP 服务器管理）
- `prompt.rs` — PromptService（Prompt 管理）
- `webdav.rs` / `webdav_sync.rs` / `webdav_auto_sync.rs` — WebDAV 同步
- `session_usage.rs` / `session_usage_codex.rs` / `session_usage_gemini.rs` — 会话用量同步
- `balance.rs` — 余额查询
- `subscription.rs` — 订阅管理
- `coding_plan.rs` — Coding Plan 管理
- `env_checker.rs` / `env_manager.rs` — 环境变量检查和管理
- `model_fetch.rs` — 模型列表获取
- `speedtest.rs` — 端点速度测试
**UsageStatsService 详解**（`src-tauri/src/services/usage_stats.rs`）：
- 这是用量统计的核心服务
- 从代理层收集请求日志
- 按 provider、model、时间维度聚合数据
- 提供 `get_usage_summary()`、`get_usage_trends()` 等方法
**UsageStatsService 方法列表**：
- `get_usage_summary()` — 获取用量摘要
- `get_usage_summary_by_app()` — 按应用获取用量
- `get_usage_trends()` — 获取用量趋势
- `get_provider_stats()` — 获取 provider 统计
- `get_model_stats()` — 获取模型统计
- `get_request_logs()` — 获取请求日志
**services 层的职责**：
        // 从数据库获取 providers
        self.db.get_providers(app_type)
    }
    pub fn switch_provider(&self, app_type: &str, provider_id: &str) -> Result<(), AppError> {
        // 切换 provider 的业务逻辑
        // 1. 验证 provider 是否存在
        // 2. 更新数据库中的 current_provider
        // 3. 写入目标工具的配置文件
        Ok(())
    }
}
```
**ProviderService 方法列表**：
- `get_providers()` — 获取 provider 列表
- `get_current_provider()` — 获取当前 provider
- `add_provider()` — 添加 provider
- `update_provider()` — 更新 provider
- `delete_provider()` — 删除 provider
- `switch_provider()` — 切换 provider
- `import_default_config()` — 导入默认配置
- `export_config()` — 导出配置
- `import_config()` — 导入配置
**陷阱**：
- `provider/mod.rs`（~2600 行）和 `proxy.rs`（3910 行）太大，应该拆分
- 有些逻辑直接放在 `commands/` 里，没有经过 services 层
- 没有统一的 service trait 或接口
**ConfigService**（`src-tauri/src/services/config.rs`）：
- 负责配置文件的读写
- 封装了 `read_json_file` 和 `write_json_file`
- 提供 `read_xxx_config()` 和 `write_xxx_config()` 方法
- 与数据库交互，读取/更新配置
**ConfigService 方法列表**：
- `read_claude_config()` — 读取 Claude 配置
- `write_claude_config()` — 写入 Claude 配置
- `read_codex_config()` — 读取 Codex 配置
- `write_codex_config()` — 写入 Codex 配置
- `read_gemini_config()` — 读取 Gemini 配置
- `write_gemini_config()` — 写入 Gemini 配置
**config 模块代码模式**：
pub fn build_live_config(provider: &Provider) -> Result<Value, AppError> {
    let mut config = read_xxx_config()?;
    // 合并 provider 配置
    config["apiKey"] = json!(provider.settings_config["apiKey"]);
    config["baseUrl"] = json!(provider.settings_config["baseUrl"]);
    Ok(config)
}
```
## 第 4 章：本地代理子系统
这是项目里最复杂的部分，单独拎出来。代理子系统实现了本地 HTTP 代理，支持 API 格式转换（Anthropic ↔ OpenAI ↔ Gemini）、多 provider 路由、故障转移和熔断。
### 4.1 proxy/ 目录结构
**ProxyServer**（`src-tauri/src/proxy/server.rs:54`）：
- `ProxyServer::new()` 创建 `ProxyState` 并初始化所有共享组件
- `ProxyServer::start()` 绑定端口、启动 Axum 路由
- `ProxyServer::stop()` 发送 shutdown 信号、等待服务器关闭
**技术栈**：
- 中间件按添加顺序执行（请求从外到内，响应从内到外）
- 常用中间件：`tower_http::cors::CorsLayer`（CORS）、`tower_http::trace::TraceLayer`（日志）
**Axum 路由**（`src-tauri/src/proxy/server.rs`）：
- `Router::new()` 创建路由
- `.route("/v1/chat/completions", post(handler))` 注册路由
- `.route("/v1/messages", post(handler))` 注册路由
- `.layer(middleware)` 添加中间件
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
**请求处理流程**：
  ├─ 等待响应
  ├─ 转换响应格式（如果需要）
  └─ 返回给客户端
```
**Gemini Shadow Store**（`src-tauri/src/proxy/providers/gemini_shadow.rs`）：
- 用于 thoughtSignature / tool call 回放
- 存储 Gemini API 的中间状态，支持流式响应
**Codex Chat History Store**（`src-tauri/src/proxy/providers/codex_chat_history.rs`）：
- 用于恢复 previous_response_id 指向的 tool call
- 存储 Codex Chat API 的历史记录
**forwarder.rs 详解**（`src-tauri/src/proxy/forwarder.rs`，122KB）：
- 这是代理子系统最大的文件，包含了请求转发的核心逻辑
- 主要职责：
  - 接收客户端请求
  - 解析请求头，提取 API key
  - 匹配到对应的 provider
  - 转换请求格式（如果需要）
  - 转发到 provider 的 base URL
  - 等待响应
  - 转换响应格式（如果需要）
  - 返回给客户端
**forwarder 设计问题**：
- 122KB 太大，包含了太多职责
- 请求转发、格式转换、错误处理全在一起
- 应该拆分成多个职责单一的模块
- 没有单元测试，难以验证正确性
**CircuitBreaker 详解**（`src-tauri/src/proxy/circuit_breaker.rs:76`）：
- 熔断器是代理子系统的核心组件
- 防止向不健康的 provider 发送请求
- 支持三种状态：Closed（正常）、Open（熔断）、HalfOpen（半开）
- 使用原子计数器跟踪连续失败/成功次数
- 使用 `Arc<RwLock<>>` 共享状态
**CircuitBreakerConfig 默认值**：
- `failure_threshold`: 4（连续失败 4 次后打开熔断器）
- `success_threshold`: 2（半开状态下成功 2 次后关闭）
- `timeout_seconds`: 60（熔断器打开后 60 秒尝试半开）
- `error_rate_threshold`: 0.6（错误率超过 60% 时打开）
- `min_requests`: 10（计算错误率前的最小请求数）
**FailoverSwitchManager**（`src-tauri/src/proxy/failover_switch.rs`）：
- 管理故障转移切换逻辑
- 与数据库交互，读取/更新 failover_queue
- 发射 Tauri 事件通知前端
**故障转移流程**：
1. 主 provider 熔断器打开（连续失败 >= 4 次）
2. `FailoverSwitchManager` 从 `failover_queue` 表读取备选 provider 列表
3. 按优先级尝试备选 provider
4. 如果备选 provider 成功，切换到该 provider
5. 如果所有备选都失败，返回 `AllProvidersCircuitOpen` 错误
**故障转移 vs 熔断器**：
- **熔断器**：单个 provider 的健康检查
- **故障转移**：多个 provider 之间的切换
- 两者配合使用，实现高可用
**代理日志系统**（`src-tauri/src/proxy/log_codes.rs`）：
   - 更新 `PROXY_MANAGED` 占位符
6. 发射 Tauri 事件通知前端
7. 释放 `SwitchLock`
**热切换 vs 冷切换**：
- **热切换**：代理运行时切换 provider，不需要重启代理
- **冷切换**：停止代理 → 切换 provider → 重新启动代理
- cc-switch 默认使用热切换，用户体验更好
**恢复流程**（`src-tauri/src/lib.rs:1513`）：
- 应用退出时，`cleanup_before_exit()` 恢复 live 配置
- 使用 `stop_with_restore_keep_state()` 保留代理状态
- 下次启动时自动恢复代理接管状态（`restore_proxy_state_on_startup()`，`lib.rs:1558`）
## 第 5 章：前端架构
前端是 React + TypeScript，通过 Tauri IPC 与 Rust 后端通信。前端代码在 `src/` 目录下。
### 5.1 App.tsx — 14 个视图的路由机制
**App.tsx**（1605 行）是前端的"上帝文件"（`src/App.tsx`）。
**视图切换机制**（`src/App.tsx`）：
- 所有视图都在一个 switch 里，没有用路由库（React Router）
- 大量内联的事件处理逻辑，应该抽取到 hooks
- 没有代码分割（code splitting），所有视图都打包在一个 chunk 里
**视图切换实现**：
```typescript
// src/App.tsx
const [currentView, setCurrentView] = useState(
  localStorage.getItem("currentView") || "providers"
);
// 14 个视图
switch (currentView) {
  case "providers":    return <ProviderList />;
  case "settings":     return <Settings />;
  case "proxy":        return <ProxyStatus />;
  // ... 其他 11 个视图
}
```
**视图切换问题**：
- 没有 URL 路由，无法通过 URL 直接访问特定视图
- 没有浏览器前进/后退支持
- 所有视图都在一个文件里，难以维护
- 没有代码分割，首屏加载慢
// 切换 provider
const switchMutation = useMutation({
  mutationFn: (providerId: string) =>
    invoke("switch_claude_provider", { providerId }),
  onSuccess: () => {
    queryClient.invalidateQueries(["providers"]);
  },
});
// 添加 provider
const addMutation = useMutation({
  mutationFn: (data: CreateProviderInput) =>
    invoke("add_provider", { appType: currentApp, ...data }),
  onSuccess: () => {
    queryClient.invalidateQueries(["providers"]);
  },
});
// 删除 provider
const deleteMutation = useMutation({
  mutationFn: (providerId: string) =>
    invoke("delete_provider", { providerId }),
  onSuccess: () => {
    queryClient.invalidateQueries(["providers"]);
  },
});
```
  useEffect(() => {
    const unlisten = listen(event, (e) => handler(e.payload));
    return () => { unlisten.then(fn => fn()); };
  }, [event, handler]);
}
```
**前端 hooks 设计模式总结**：
- **数据获取**：`useQuery` + `invoke` 组合
- **数据修改**：`useMutation` + `invoke` 组合
- **事件监听**：`useTauriEvent` hook
- **轮询**：`useProxyStatus` 使用 `setInterval`
- **缓存失效**：`queryClient.invalidateQueries()` 刷新 React Query 缓存
**React Query 使用模式**：
```typescript
// 查询数据
const { data, isLoading, error } = useQuery(
  ["key", param],
  () => invoke("command", { param })
);
// 修改数据
const mutation = useMutation({
  mutationFn: (data) => invoke("command", { data }),
  onSuccess: () => {
    queryClient.invalidateQueries(["key"]);
  },
});
```
**React Query 配置**：
- `staleTime`: 数据过期时间（默认 0，立即重新获取）
- `cacheTime`: 缓存时间（默认 5 分钟）
- `refetchOnWindowFocus`: 窗口聚焦时重新获取（默认 true）
- `retry`: 失败重试次数（默认 3）
**React Query 最佳实践**：
- 使用 `queryKey` 数组作为缓存键
- 使用 `invalidateQueries` 刷新相关缓存
- 使用 `setQueryData` 乐观更新
- 使用 `onSuccess` / `onError` 处理副作用
**前端错误处理**：
- Tauri 命令返回 `Result<T, String>`，前端通过 `try/catch` 捕获
- React Query 的 `error` 状态用于显示错误信息
- 没有统一的错误处理组件，每个组件自己处理错误
];
- `src/config/codingPlanProviders.ts`（2.6KB）— Coding Plan provider 列表
```
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
**前端组件结构**（`src/components/`）：
- `settings/` — 设置页面组件（代理配置、UI 偏好、WebDAV 同步等）
- `providers/` — Provider 管理组件（列表、添加、编辑、删除、排序等）
- `proxy/` — 代理状态组件（状态显示、启停控制、故障转移配置等）
- `mcp/` — MCP 配置组件（服务器列表、添加、编辑、删除等）
- `skills/` — Skills 管理组件（列表、安装、卸载、更新等）
- `prompts/` — Prompt 管理组件（列表、添加、编辑、删除等）
- `usage/` — 用量统计组件（图表、筛选、导出等）
- `common/` — 通用组件（按钮、输入框、模态框、Toast 等）
**前端组件示例**（`src/components/providers/`）：
- `ProviderList.tsx` — Provider 列表组件
- `ProviderCard.tsx` — Provider 卡片组件
- `ProviderForm.tsx` — Provider 表单组件
- `ProviderSort.tsx` — Provider 排序组件
**前端路由**（`src/App.tsx`）：
- 没有使用 React Router
- 使用 `localStorage` 持久化当前视图
- 使用 `switch` 语句切换视图
- 所有视图都在一个文件里，没有代码分割
## 第 6 章：AI Slop 特征模式识别
这是你重构的弹药库。这些模式不是"代码风格偏好"，而是实实在在的维护负担。
### 6.1 代码膨胀模式
**过大的单文件**：
- `lib.rs`（1826 行）— 模块声明 + 插件注册 + 命令注册 + 初始化逻辑全混在一起
- `App.tsx`（1605 行）— 14 个视图 + 事件处理 + 状态管理全在一个文件
- `forwarder.rs`（~3000 行）— 请求转发 + 格式转换 + 错误处理全在一起
- `codex_config.rs`（~1600 行）— 配置读写 + 迁移 + 验证全在一起
- `claude_desktop_config.rs`（~1500 行）— 同上
- `proxy.rs`（services，3910 行）— `ProxyService` 的所有方法全在一个文件
- `provider/mod.rs`（services，~2600 行）— `ProviderService` 的所有方法全在一个文件
**复制粘贴的 config 模块**：
- 7 个工具的 config 模块结构几乎一样，但没有抽取公共函数
- `AppType` 的 match 在 `McpApps`（`src-tauri/src/app_config.rs:24`）、`VisibleApps`（`src-tauri/src/settings.rs:66`）、`CommonConfigSnippets`（`src-tauri/src/app_config.rs:441`）里重复出现
- 每次加新工具都要改 10+ 个 match
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
**预期收益**：
- 减少代码量 10-15%
- 提高可读性和一致性
- 为后续重构打下基础
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
**预期收益**：
- 文件大小减少 50-70%
- 模块职责更清晰
- 新功能开发更容易
### 7.3 架构级重构（最后做，慎重，1-2 周）