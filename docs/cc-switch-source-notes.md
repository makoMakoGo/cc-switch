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
**Rust derive 宏**：
- `#[derive(Debug)]` — 自动派生 Debug trait，允许 `{:?}` 打印
- `#[derive(Clone)]` — 自动派生 Clone trait，允许 `.clone()`
- `#[derive(Serialize, Deserialize)]` — 自动派生 serde 序列化
- `#[derive(PartialEq, Eq)]` — 自动派生比较操作
- `#[derive(Hash)]` — 自动派生 Hash trait，允许用作 HashMap 键
**cc-switch 中的 derive 使用**：
- `Provider` 使用 `Debug, Clone, Serialize, Deserialize`（`src-tauri/src/provider.rs:9`）
- `AppType` 使用 `Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize`（`src-tauri/src/app_config.rs:339`）
- `AppError` 使用 `Debug, Error`（通过 thiserror）（`src-tauri/src/error.rs:6`）
- `CircuitState` 使用 `Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize`（`src-tauri/src/proxy/circuit_breaker.rs:14`）
- JSON 配置文件读写（`read_json_file`, `write_json_file`）
- Tauri IPC 参数传递（`#[tauri::command]` 自动序列化）
- 数据库存储（`to_json_string()`）
- 前端数据传递（`invoke()` 返回值）
**Rust 同步原语**：
- `Mutex<T>` — 互斥锁，同一时间只有一个线程能访问
- `RwLock<T>` — 读写锁，多读单写
- `Arc<T>` — 原子引用计数，多线程共享数据
- `AtomicU32` — 原子计数器，无锁操作
**cc-switch 中的同步模式**：
- `Database` 使用 `Mutex<Connection>` 保护 SQLite 连接
- `APP_SETTINGS` 使用 `OnceLock<RwLock<AppSettings>>` 保护设置缓存
- `ProxyState` 使用 `Arc<RwLock<>>` 共享代理状态
- `CircuitBreaker` 使用 `AtomicU32` 跟踪连续失败次数
**为什么用这些同步原语**：
- `Mutex` 用于写多读少的场景（数据库连接）
- `RwLock` 用于读多写少的场景（设置缓存）
- `Arc` 用于多线程共享数据（代理状态）
- `AtomicU32` 用于简单的计数器（熔断器）
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
**错误处理最佳实践**：
- 使用 `?` 操作符传播错误，不要手动 match
- 使用 `map_err` 转换错误类型，保留上下文
- 使用 `unwrap_or_default` 提供默认值，避免 panic
- Tauri 命令返回 `Result<T, AppError>`，自动转为 JS reject
**错误处理反模式**：
- 使用 `unwrap()` 可能 panic
- 使用 `expect()` 可能 panic
- 忽略错误（`let _ = ...`）
- 返回 `String` 错误而不是 `AppError`
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
- `get_providers(app_type)` — 获取 provider 列表
- `get_provider_by_id(id)` — 获取单个 provider
- `add_provider(provider)` — 添加 provider
- `update_provider(provider)` — 更新 provider
- `delete_provider(id)` — 删除 provider
- `get_current_provider(app_type)` — 获取当前 provider
- `set_current_provider(app_type, provider_id)` — 设置当前 provider
- `get_settings()` — 获取所有设置
- `get_setting(key)` — 获取单个设置
- `set_setting(key, value)` — 设置单个配置项
**DAO CRUD 模式**：
```rust
// 添加 provider
pub fn add_provider(&self, provider: &Provider) -> Result<(), AppError> {
    let conn = lock_conn!(self.conn);
    conn.execute(
        "INSERT INTO providers (id, name, app_type, settings_config) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![provider.id, provider.name, provider.app_type, to_json_string(&provider.settings_config)?],
    )?;
    Ok(())
}
```
**DAO 查询模式**：
```rust
// 查询 provider 列表
pub fn get_providers(&self, app_type: &str) -> Result<Vec<Provider>, AppError> {
    let conn = lock_conn!(self.conn);
    let mut stmt = conn.prepare("SELECT * FROM providers WHERE app_type = ?1")?;
    let providers = stmt.query_map([app_type], |row| {
        Ok(Provider {
            id: row.get(0)?,
            name: row.get(1)?,
            app_type: row.get(2)?,
            settings_config: serde_json::from_str(&row.get::<_, String>(3)?)?,
            // ... 其他字段
        })
    })?.collect();
    Ok(providers)
}
```
**Schema 迁移示例**（`src-tauri/src/database/schema.rs`）：
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
**PromptService 详解**（`src-tauri/src/services/prompt.rs`）：
- Prompt 是 AI 工具的系统提示词
- cc-switch 管理 Prompt 配置，支持多工具共享
- 每个 Prompt 有独立的配置（name、content、app_type 等）
- 支持启用/禁用单个 Prompt
**PromptService 方法列表**：
- `get_prompts()` — 获取 Prompt 列表
- `upsert_prompt()` — 添加/更新 Prompt
- `delete_prompt()` — 删除 Prompt
- `enable_prompt()` — 启用/禁用 Prompt
- `import_prompt_from_file()` — 从文件导入 Prompt
**McpService 详解**（`src-tauri/src/services/mcp.rs`）：
**UsageStatsService 详解**（`src-tauri/src/services/usage_stats.rs`）：
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
**为什么需要格式转换**：
- 不同 AI 工具使用不同的 API 格式
- Claude 使用 Anthropic API（`/v1/messages`）
- Codex 使用 OpenAI API（`/v1/chat/completions`）
- Gemini 使用 Gemini API（`/v1beta/models/`）
- 代理层需要将请求转换为目标 provider 的格式
**格式转换流程**：
1. 接收客户端请求（统一格式）
2. 解析请求体，提取消息内容
3. 转换为目标 provider 的 API 格式
4. 转发到 provider 的 base URL
5. 接收响应，转换回统一格式
6. 返回给客户端
**多 provider 路由逻辑**（`src-tauri/src/proxy/provider_router.rs`）：
- 每个 provider 有自己的 API key
- 代理服务器根据请求中的 API key 判断转发到哪个 provider
- 支持故障转移：主 provider 挂了自动切换到备选
- `ProviderRouter` 持有熔断器状态，跨请求保持
**路由匹配流程**：
1. 从请求头提取 `Authorization: Bearer <api_key>`
2. 在数据库中查找匹配的 provider
3. 检查 provider 的熔断器状态
4. 如果熔断器打开，尝试故障转移
5. 转发到 provider 的 base URL
  - 等待响应
  - 转换响应格式（如果需要）
  - 返回给客户端
**forwarder 设计问题**：
- 122KB 太大，包含了太多职责
**路由问题**：
- API key 匹配是线性扫描，没有索引
- 没有缓存路由结果，每次请求都查数据库
- 故障转移逻辑和路由逻辑耦合在一起
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
- 定义了所有日志代码常量
- 每个日志代码对应一个特定的事件或错误
- 方便过滤和分析日志
- 支持结构化日志（JSON 格式）
**日志代码示例**：
- `SRV_START` — 服务器启动
- `SRV_STOP` — 服务器停止
- `REQ_FORWARD` — 请求转发
- `REQ_ERROR` — 请求错误
- `CB_STATE_CHANGE` — 熔断器状态变化
- `FAILOVER_SWITCH` — 故障转移切换
- `TAKEOVER_ENABLE` — 接管启用
- `TAKEOVER_DISABLE` — 接管禁用
**热切换 vs 冷切换**：
## 第 5 章：前端架构
前端是 React + TypeScript，通过 Tauri IPC 与 Rust 后端通信。前端代码在 `src/` 目录下。
### 5.1 App.tsx — 14 个视图的路由机制
**App.tsx**（1605 行）是前端的"上帝文件"（`src/App.tsx`）。
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
**useSettings 详解**（`src/hooks/useSettings.ts`）：
- 封装了 `get_settings` 和 `save_settings` Tauri 命令
- 使用 React Query 缓存设置数据
- 提供 `mutateSettings` 方法用于修改设置
**useSettings 代码示例**：
```typescript
// src/hooks/useSettings.ts
export function useSettings() {
  const { data: settings, isLoading } = useQuery(
    ["settings"],
    () => invoke("get_settings")
  );
  const mutation = useMutation({
    mutationFn: (newSettings) => invoke("save_settings", { settings: newSettings }),
    onSuccess: () => {
      queryClient.invalidateQueries(["settings"]);
    },
  });
  return { settings, isLoading, mutateSettings: mutation.mutate };
}
```
**useSettings 问题**：
- 没有乐观更新，修改设置后需要等待服务器响应
- 没有错误处理，失败时没有提示
- 设置结构是动态的，没有类型检查
**useProxyStatus 详解**（`src/hooks/useProxyStatus.ts`）：
- 轮询代理服务器状态（每 2 秒）
- 提供 `isRunning`, `currentProviders`, `uptime` 等状态
- 使用 `useTauriEvent` 监听代理状态变化事件
**useProxyStatus 代码示例**：
```typescript
// src/hooks/useProxyStatus.ts
export function useProxyStatus() {
  const [status, setStatus] = useState<ProxyStatus | null>(null);
  useEffect(() => {
    const interval = setInterval(async () => {
      const s = await invoke("get_proxy_status");
      setStatus(s);
    }, 2000);
    return () => clearInterval(interval);
  }, []);
  return status;
}
```
**useProxyStatus 问题**：
- 使用 `setInterval` 轮询，不是事件驱动
- 没有错误处理，invoke 失败时没有提示
- 没有缓存，每次轮询都调用 Tauri 命令
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
**前端组件设计问题**：
- 没有统一的组件库，每个组件自己实现样式
- 没有组件文档，难以复用
- 没有组件测试，难以验证正确性
- 组件之间耦合度高，修改一个组件可能影响其他组件
**前端路由**（`src/App.tsx`）：
## 第 6 章：AI Slop 特征模式识别
这是你重构的弹药库。这些模式不是"代码风格偏好"，而是实实在在的维护负担。
### 6.1 代码膨胀模式
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