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
**Rust 生命周期在 cc-switch 中的使用**：
```rust
// 生命周期标注 'a 表示引用的有效期
// cc-switch 里几乎不用，因为大部分数据是 Arc 或 owned
// 唯一的例子：Tauri State
#[tauri::command]
async fn my_command(
    state: tauri::State<'_, AppState>,  // '_ 是生命周期标注
) -> Result<String, AppError> {
    // state 的生命周期由 Tauri 管理
}
```
**为什么 cc-switch 很少用生命周期**：
- 大部分数据是 `Arc<T>`（引用计数），不需要生命周期
- 配置文件读取后立即 clone，不持有引用
- Tauri 框架管理 `State` 的生命周期，开发者不需要关心
**Rust 闭包在 cc-switch 中的使用**：
```rust
// 闭包（匿名函数）
// cc-switch 里到处都是，特别是配置修改和数据库操作
let mutate_settings = |settings: &mut AppSettings| {
    settings.proxy_port = 8080;
};
// 异步闭包
tokio::spawn(async move {
    // 异步任务
});
// 闭包作为参数
pub fn mutate_settings<F>(f: F) -> Result<(), AppError>
where
    F: FnOnce(&mut AppSettings),
{
    let mut settings = APP_SETTINGS.get().unwrap().write().unwrap();
    f(&mut settings);
    Ok(())
}
```
**闭包 vs 函数**：
- 闭包可以捕获外部变量，函数不能
- 闭包可以作为参数传递，更灵活
- cc-switch 里大部分配置修改都用闭包
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
**Rust enum 在 cc-switch 中的使用**：
- `AppType` — 7 个 AI 工具的枚举（`src-tauri/src/app_config.rs:341`）
- `AppError` — 错误类型枚举（`src-tauri/src/error.rs:6`）
- `CircuitState` — 熔断器状态枚举（`src-tauri/src/proxy/circuit_breaker.rs:14`）
- `Action` — SQLite 操作类型枚举（rusqlite）
**enum 的两种形式**：
```rust
// 简单枚举（C-like）
enum CircuitState {
    Closed,
    Open,
    HalfOpen,
}
// 带数据的枚举（类似 TypeScript 的 discriminated union）
enum AppError {
    Config(String),
    Io { path: String, source: std::io::Error },
    Json { path: String, source: serde_json::Error },
}
```
**enum 与 match 配合**：
```rust
match app_type {
    AppType::Claude => "claude",
    AppType::Codex => "codex",
    AppType::Gemini => "gemini",
    _ => "unknown",
}
```
**Rust 模式匹配进阶**：
```rust
// 解构结构体
let Provider { id, name, .. } = provider;
// 解构枚举
match error {
    AppError::Io { path, source } => println!("IO error at {}: {}", path, source),
    AppError::Config(msg) => println!("Config error: {}", msg),
    _ => println!("Other error"),
}
// matches! 宏
if matches!(app_type, AppType::OpenCode | AppType::OpenClaw | AppType::Hermes) {
    // additive mode
}
```
**serde 枚举序列化**：
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
    const [removed] = newItems.splice(dragIndex, 1);
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
**DAO 更新模式**：
```rust
// 更新 provider
pub fn update_provider(&self, provider: &Provider) -> Result<(), AppError> {
    let conn = lock_conn!(self.conn);
    conn.execute(
        "UPDATE providers SET name = ?1, settings_config = ?2 WHERE id = ?3",
        rusqlite::params![provider.name, to_json_string(&provider.settings_config)?, provider.id],
    )?;
    Ok(())
}
```
**DAO 删除模式**：
```rust
// 删除 provider
pub fn delete_provider(&self, id: &str) -> Result<(), AppError> {
    let conn = lock_conn!(self.conn);
    conn.execute("DELETE FROM providers WHERE id = ?1", [id])?;
    Ok(())
}
```
**DAO 插入模式**：
```rust
// 插入设置
pub fn set_setting(&self, key: &str, value: &str) -> Result<(), AppError> {
    let conn = lock_conn!(self.conn);
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?1, ?2)",
        rusqlite::params![key, value],
    )?;
    Ok(())
}
```
**DAO 批量操作**：
```rust
// 批量插入 providers
pub fn add_providers(&self, providers: &[Provider]) -> Result<(), AppError> {
    let conn = lock_conn!(self.conn);
    for provider in providers {
        conn.execute(
            "INSERT INTO providers (id, name, app_type, settings_config) VALUES (?1, ?2, ?3, ?4)",
            rusqlite::params![provider.id, provider.name, provider.app_type, to_json_string(&provider.settings_config)?],
        )?;
    }
    Ok(())
}
```
- `skill.rs`（~2600 行）— SkillService（Skills 管理）
**DAO 设置模式**：
```rust
// 获取设置
pub fn get_setting(&self, key: &str) -> Result<Option<String>, AppError> {
    let conn = lock_conn!(self.conn);
    let mut stmt = conn.prepare("SELECT value FROM settings WHERE key = ?1")?;
    let mut rows = stmt.query_map([key], |row| row.get(0))?;
    Ok(rows.next().transpose()?)
}
```
**DAO 批量设置**：
```rust
// 批量设置
pub fn set_settings(&self, settings: &[(String, String)]) -> Result<(), AppError> {
    let conn = lock_conn!(self.conn);
    for (key, value) in settings {
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?1, ?2)",
            rusqlite::params![key, value],
        )?;
    }
    Ok(())
}
```
**DAO 代理配置模式**：
```rust
// 获取代理配置
pub async fn get_proxy_config_for_app(&self, app_type: &str) -> Result<ProxyConfig, AppError> {
    let conn = lock_conn!(self.conn);
    let mut stmt = conn.prepare("SELECT config FROM proxy_config WHERE app_type = ?1")?;
    let mut rows = stmt.query_map([app_type], |row| {
        let config_str: String = row.get(0)?;
        serde_json::from_str(&config_str).map_err(|e| AppError::Json(e.to_string()))
    })?;
    Ok(rows.next().transpose()?.unwrap_or_default())
}
```
**DAO 故障转移队列模式**：
```rust
// 获取故障转移队列
pub fn get_failover_queue(&self, app_type: &str) -> Result<Vec<FailoverQueueItem>, AppError> {
    let conn = lock_conn!(self.conn);
    let mut stmt = conn.prepare("SELECT * FROM failover_queue WHERE app_type = ?1 ORDER BY priority")?;
    let items = stmt.query_map([app_type], |row| {
        Ok(FailoverQueueItem {
            provider_id: row.get(0)?,
            priority: row.get(1)?,
        })
    })?.collect();
    Ok(items)
}
```
**SpeedtestService 详解**（`src-tauri/src/services/speedtest.rs`）：
**ModelFetchService 详解**（`src-tauri/src/services/model_fetch.rs`）：
- 从 AI 工具的 API 获取可用模型列表
- 支持 OpenAI 兼容的 `/v1/models` 端点
- 返回模型名称、ID、能力等信息
**ModelFetchService 方法列表**：
- `fetch_models_for_config()` — 获取模型列表
- 支持缓存，避免频繁请求
- 支持超时和重试
## 第 4 章：本地代理子系统
这是项目里最复杂的部分，单独拎出来。代理子系统实现了本地 HTTP 代理，支持 API 格式转换（Anthropic ↔ OpenAI ↔ Gemini）、多 provider 路由、故障转移和熔断。
### 4.1 proxy/ 目录结构
**ProxyServer**（`src-tauri/src/proxy/server.rs:54`）：
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
**余额查询**（`src-tauri/src/services/balance.rs`）：
- 查询 AI 工具的账户余额
- 支持多种认证方式（API key、OAuth）
- 返回余额、额度、过期时间等信息
**余额查询方法列表**：
- `get_balance()` — 获取余额
- `get_subscription_quota()` — 获取订阅配额
- `get_codex_oauth_quota()` — 获取 Codex OAuth 配额
**会话用量同步**（`src-tauri/src/services/session_usage.rs`）：
4. 写入数据库的 `request_logs` 表
5. 更新用量统计缓存
**SwitchLock 详解**（`src-tauri/src/proxy/switch_lock.rs`）：
    pub async fn acquire(&self, app_type: &str) -> MutexGuard<()> {
        let lock = self.locks.get(app_type).unwrap();
        lock.lock().await
    }
}
```
**SwitchLock 问题**：
- 没有超时机制，死锁时会永远等待
- 没有优先级，先到先得
- 锁粒度太粗，整个切换过程都持有锁
## 第 5 章：前端架构
前端是 React + TypeScript，通过 Tauri IPC 与 Rust 后端通信。前端代码在 `src/` 目录下。
### 5.1 App.tsx — 14 个视图的路由机制
**App.tsx**（1605 行）是前端的"上帝文件"（`src/App.tsx`）。
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
**useDarkMode 详解**（`src/hooks/useDarkMode.ts`）：
- 监听系统主题变化
- 提供 `isDarkMode` 状态
- 自动切换 CSS 类名
**useDarkMode 代码示例**：
```typescript
// src/hooks/useDarkMode.ts
export function useDarkMode() {
  const [isDark, setIsDark] = useState(
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => setIsDark(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);
  return isDark;
}
```
**useStreamCheck 详解**（`src/hooks/useStreamCheck.ts`）：
- 检查 API 端点的流式响应支持
- 测试 SSE（Server-Sent Events）连接
- 返回流式响应的延迟和状态
**useStreamCheck 代码示例**：
```typescript
// src/hooks/useStreamCheck.ts
export function useStreamCheck() {
  const [results, setResults] = useState<StreamCheckResult[]>([]);
  const checkStream = async (url: string) => {
    const result = await invoke("stream_check_provider", { url });
    setResults(prev => [...prev, result]);
  };
  return { results, checkStream };
}
```
**useDragSort 详解**（`src/hooks/useDragSort.ts`）：
    setDragIndex(null);
  };
  return { handleDragStart, handleDragOver, handleDrop };
}
```
// 直接调用
## 第 6 章：AI Slop 特征模式识别
这是你重构的弹药库。这些模式不是"代码风格偏好"，而是实实在在的维护负担。
### 6.1 代码膨胀模式
**过大的单文件**：
**复制粘贴的 config 模块**：
- 7 个工具的 config 模块结构几乎一样，但没有抽取公共函数
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