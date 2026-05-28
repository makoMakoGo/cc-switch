# Chapter 1 Source Trace Findings

## Setup & Startup Chain

### F01: app_store function name is wrong
- **note location**: 1.1, startup chain diagram line 30
- **quoted claim**: `app_store::refresh()       // lib.rs:288`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/lib.rs:288` shows `app_store::refresh_app_config_dir_override(app.handle());`
- **exact replacement**: `app_store::refresh_app_config_dir_override()  // lib.rs:288`
- **severity**: medium

### F02: settings::init() does not exist
- **note location**: 1.1.1, item 6 under Setup closure
- **quoted claim**: `初始化设置（settings::init()）`
- **verdict**: hallucination
- **source evidence**: `grep -n 'fn init\b' src-tauri/src/settings.rs` returns 0 matches. Settings are lazily initialized via `OnceLock` at `settings.rs:519` (`static SETTINGS_STORE: OnceLock<RwLock<AppSettings>> = OnceLock::new();`) and accessed via `settings_store()` at line 521.
- **exact replacement**: `初始化设置缓存（settings.rs:519, OnceLock 惰性初始化）`
- **severity**: high

### F03: initialize_common_config_snippets line reference is misleading
- **note location**: 1.1, startup chain diagram line 51
- **quoted claim**: `initialize_common_config_snippets() // lib.rs:1601`
- **verdict**: ambiguous
- **source evidence**: The function is *defined* at `lib.rs:1601`, but it is *called* at `lib.rs:944` inside the spawned async block in setup. In the setup call-chain diagram, the line reference should point to the call site, not the definition.
- **exact replacement**: `initialize_common_config_snippets() // lib.rs:944 (定义 lib.rs:1601)`
- **severity**: low

### F04: restore_proxy_state_on_startup line reference is misleading
- **note location**: 1.1, startup chain diagram line 52
- **quoted claim**: `restore_proxy_state_on_startup()    // lib.rs:1558`
- **verdict**: ambiguous
- **source evidence**: The function is *defined* at `lib.rs:1558`, but it is *called* at `lib.rs:947` inside the spawned async block in setup.
- **exact replacement**: `restore_proxy_state_on_startup()    // lib.rs:947 (定义 lib.rs:1558)`
- **severity**: low

### F05: session usage sync loop line reference is off
- **note location**: 1.1, startup chain diagram line 53
- **quoted claim**: `session usage sync loop        // lib.rs:999`
- **verdict**: wrong
- **source evidence**: The initial sync calls span `lib.rs:984-999`. The actual `loop { interval.tick().await; ... }` starts at `lib.rs:1006`. Line 999 is the last initial sync call (`sync_gemini_usage`), not the loop.
- **exact replacement**: `session usage sync loop        // lib.rs:1006 (初始同步 lib.rs:984-999)`
- **severity**: low

---

## Invoke Handler & Module Counts

### F06: invoke_handler command count is inconsistent and partially wrong
- **note location**: 1.1 key points line 63, and 1.1.1 item 6
- **quoted claim**: `.invoke_handler() 注册约 271 个 Tauri 命令（1072-1377）` (appears twice, line 63 and line 86)
- **verdict**: wrong
- **source evidence**: `sed -n '1072,1377p' src-tauri/src/lib.rs | grep -c 'commands::'` returns 266. The startup diagram at line 55 correctly says "~266", but the key points section and section 1.1.1 both say "约 271".
- **exact replacement**: `注册 266 个 Tauri 命令（1072-1377）`
- **severity**: medium

### F07: commands/ submodule count is wrong
- **note location**: 1.4, module dependency diagram
- **quoted claim**: `commands/ │ 34 个子模块`
- **verdict**: wrong
- **source evidence**: `grep -E '^\s*pub mod |^\s*mod ' src-tauri/src/commands/mod.rs | wc -l` returns 31. `ls src-tauri/src/commands/*.rs | wc -l` returns 32 (including mod.rs itself, so 31 submodules).
- **exact replacement**: `commands/ │ 31 个子模块`
- **severity**: medium

### F08: proxy/ module count is wrong
- **note location**: 1.4, module dependency diagram
- **quoted claim**: `proxy/ │ 35+ 个模块`
- **verdict**: wrong
- **source evidence**: `grep -E '^\s*pub mod |^\s*mod |^\s*pub\(crate\) mod ' src-tauri/src/proxy/mod.rs | wc -l` returns 31.
- **exact replacement**: `proxy/ │ 31 个模块`
- **severity**: medium

### F09: services/ submodule count is correct
- **note location**: 1.4, module dependency diagram
- **quoted claim**: `services/ │ 25 个子模块`
- **verdict**: ok
- **source evidence**: `grep -E '^\s*pub mod |^\s*mod ' src-tauri/src/services/mod.rs | wc -l` returns 25.
- **severity**: n/a

### F10: lib.rs module declaration count is correct
- **note location**: 1.4
- **quoted claim**: `lib.rs │ 1825 行，声明 34 个模块`
- **verdict**: ok
- **source evidence**: `grep -E '^\s*mod |^\s*pub mod ' src-tauri/src/lib.rs | wc -l` returns 34. `wc -l src-tauri/src/lib.rs` returns 1825.
- **severity**: n/a

---

## Provider Switch Data Flow

### F11: Provider switch command parameter names are wrong
- **note location**: 1.2, provider switch call chain
- **quoted claim**: `fn switch_provider(state, app_type, provider_id)`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/commands/provider.rs:102` shows `pub fn switch_provider(state: State<'_, AppState>, app: String, id: String)`. Parameters are `app` and `id`, not `app_type` and `provider_id`.
- **exact replacement**: `fn switch_provider(state, app, id)`
- **severity**: low

### F12: Provider switch service method name is wrong
- **note location**: 1.2, provider switch call chain
- **quoted claim**: `services::provider::switch_provider()    // 写配置文件`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/commands/provider.rs:89` shows `ProviderService::switch(state, app_type, id)`. The method is `ProviderService::switch()`, not `switch_provider()`. Defined at `src-tauri/src/services/provider/mod.rs:1569`.
- **exact replacement**: `ProviderService::switch()    // services/provider/mod.rs:1569`
- **severity**: medium

### F13: Provider switch DB query method is wrong
- **note location**: 1.2, provider switch call chain
- **quoted claim**: `state.db.get_provider(provider_id)      // 从 SQLite 取 provider`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/services/provider/mod.rs:1571` shows `let providers = state.db.get_all_providers(app_type.as_str())?;` followed by `providers.get(id)` at line 1573. There is no `get_provider()` call.
- **exact replacement**: `state.db.get_all_providers(app_type) → .get(id)      // 从 SQLite 取 provider`
- **severity**: medium

### F14: Provider switch flow description is oversimplified
- **note location**: 1.2, services/provider/mod.rs section
- **quoted claim**: `switch_provider() → read_live_settings() → build_effective_settings_with_common_config() → write_live_with_common_config()`
- **verdict**: ambiguous
- **source evidence**: `src-tauri/src/services/provider/mod.rs:1643` (`switch_normal`) shows: (1) backfill current provider via `read_live_settings()` (line 1684), (2) `set_current_provider` (line 1710-1713), (3) `write_live_with_common_config()` (line 1717) which internally calls `build_effective_settings_with_common_config`. The `read_live_settings` is only called during backfill, not as a direct step. The `build_effective_settings_with_common_config` is called *inside* `write_live_with_common_config`, not as a separate step.
- **exact replacement**: `switch_normal() → backfill via read_live_settings() → set_current_provider() → write_live_with_common_config()（内部调用 build_effective_settings_with_common_config）`
- **severity**: medium

---

## Proxy Switch Data Flow

### F15: Proxy switch lock method name is wrong
- **note location**: 1.2, proxy switch call chain
- **quoted claim**: `switch_locks.acquire(app_type)             // 防止并发切换`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/services/proxy.rs:1816` shows `let _guard = self.switch_locks.lock_for_app(app_type).await;`. The method is `lock_for_app`, not `acquire`. Defined at `src-tauri/src/proxy/switch_lock.rs:26`.
- **exact replacement**: `switch_locks.lock_for_app(app_type).await             // 防止并发切换`
- **severity**: low

### F16: Proxy switch command calls switch_proxy_target, not hot_switch_provider directly
- **note location**: 1.2, proxy switch call chain
- **quoted claim**: `→ ProxyService::hot_switch_provider()          // services/proxy.rs`
- **verdict**: ambiguous
- **source evidence**: `src-tauri/src/commands/proxy.rs:297` shows `state.proxy_service.switch_proxy_target(&app_type, &provider_id).await`. Then `src-tauri/src/services/proxy.rs:1951` shows `switch_proxy_target` calls `self.hot_switch_provider(app_type, provider_id).await?`. The command calls `switch_proxy_target()`, which in turn calls `hot_switch_provider()`.
- **exact replacement**: `→ ProxyService::switch_proxy_target() → hot_switch_provider()  // services/proxy.rs:1946 → 1811`
- **severity**: low

### F17: Proxy switch does not emit Tauri events
- **note location**: 1.2, proxy switch call chain
- **quoted claim**: `→ 发射 Tauri 事件通知前端`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/services/proxy.rs:1811-1877` (`hot_switch_provider`) shows no `emit()` or `emit_all()` call. The function returns `HotSwitchOutcome { logical_target_changed }`. The `Emitter` trait is imported at line 18 but not used in this function.
- **exact replacement**: Remove this line or replace with `→ 返回 HotSwitchOutcome（无前端事件发射）`
- **severity**: high

### F18: Proxy switch does not rewrite live config with PROXY_TOKEN_PLACEHOLDER
- **note location**: 1.2, proxy switch call chain
- **quoted claim**: `→ 重写 live 配置，把 API key 替换为 PROXY_TOKEN_PLACEHOLDER 占位符`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/services/proxy.rs:1811-1877` (`hot_switch_provider`) shows: (1) lock, (2) get provider, (3) update `current_providers` in DB + settings (lines 1849-1853), (4) if `should_sync_backup`: call `update_live_backup_from_provider_inner` and `sync_claude_live_from_provider_while_proxy_active` (lines 1855-1865), (5) call `server.set_active_target()` (line 1870). The PROXY_TOKEN_PLACEHOLDER is used during *initial takeover* (e.g., `take_over_claude_live_config`), not during hot switch. The hot switch only updates the routing target.
- **exact replacement**: `→ 更新 DB current_providers + settings → 同步 live backup → server.set_active_target()`
- **severity**: high

### F19: Proxy switch does not set base URL to localhost
- **note location**: 1.2, proxy switch call chain
- **quoted claim**: `→ 设置 base URL 为 localhost:代理端口`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/services/proxy.rs:1811-1877` (`hot_switch_provider`) does not set any base URL. The base URL is set during *initial takeover* when the proxy server first starts and takes over the live config. The hot switch only changes which provider the running proxy routes to.
- **exact replacement**: Remove this line from the hot switch flow.
- **severity**: high

---

## State Management

### F20: ProxyService struct field name is wrong
- **note location**: 1.3, ProxyService section
- **quoted claim**: `pub struct ProxyService { db: Arc<Database>, server: Arc<RwLock<Option<ProxyServer>>>, app_handle: Arc<RwLock<Option<tauri::AppHandle>>>, switch_locks: SwitchLockManager, }`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/services/proxy.rs:55-61` shows the actual struct has a comment `/// AppHandle，用于传递给 ProxyServer 以支持故障转移时的 UI 更新` on the `app_handle` field. The struct definition matches the notes, but the notes omit the `#[derive(Clone)]` attribute at line 54.
- **exact replacement**: Add `#[derive(Clone)]` before the struct definition in the notes.
- **severity**: low

---

## Frontend File Line Counts

### F21: useSettings.ts line count is stale
- **note location**: 1.3, frontend state management section
- **quoted claim**: `useSettings.ts (512 行)`
- **verdict**: stale
- **source evidence**: `wc -l src/hooks/useSettings.ts` returns 505.
- **exact replacement**: `useSettings.ts (505 行)`
- **severity**: low

### F22: useProxyStatus.ts line count is stale
- **note location**: 1.3, frontend state management section
- **quoted claim**: `useProxyStatus.ts (185 行)`
- **verdict**: stale
- **source evidence**: `wc -l src/hooks/useProxyStatus.ts` returns 245.
- **exact replacement**: `useProxyStatus.ts (245 行)`
- **severity**: low

### F23: useDirectorySettings.ts line count is stale
- **note location**: 1.3, frontend state management section
- **quoted claim**: `useDirectorySettings.ts (275 行)`
- **verdict**: stale
- **source evidence**: `wc -l src/hooks/useDirectorySettings.ts` returns 373.
- **exact replacement**: `useDirectorySettings.ts (373 行)`
- **severity**: low

### F24: useDragSort.ts line count is stale
- **note location**: 1.3, frontend state management section
- **quoted claim**: `useDragSort.ts (95 行)`
- **verdict**: stale
- **source evidence**: `wc -l src/hooks/useDragSort.ts` returns 119.
- **exact replacement**: `useDragSort.ts (119 行)`
- **severity**: low

### F25: lib/query file line counts are stale (batch)
- **note location**: 1.3, frontend state management section
- **quoted claim**: `queries.ts (156 行)`, `mutations.ts (357 行)`, `proxy.ts (244 行)`, `failover.ts (289 行)`, `usage.ts (320 行)`, `subscription.ts (64 行)`
- **verdict**: stale
- **source evidence**: `wc -l` returns: queries.ts 155, mutations.ts 356, proxy.ts 243, failover.ts 288, usage.ts 319, subscription.ts 63.
- **exact replacement**: `queries.ts (155 行)`, `mutations.ts (356 行)`, `proxy.ts (243 行)`, `failover.ts (288 行)`, `usage.ts (319 行)`, `subscription.ts (63 行)`
- **severity**: low

---

## Rust Concept References (Chapter 2, but referenced in Ch1)

### F26: AppError line number is off by one
- **note location**: 2.1, Rust concepts table
- **quoted claim**: `error.rs:6 的 AppError`
- **verdict**: wrong
- **source evidence**: `src-tauri/src/error.rs:7` shows `pub enum AppError {`. Line 6 is `#[derive(Debug, Error)]`.
- **exact replacement**: `error.rs:7 的 AppError`
- **severity**: low

---

## Verified Correct Claims

The following claims were spot-checked and found correct:

- `main.rs` is 22 lines (`wc -l` = 22) ✓
- `lib.rs` is 1825 lines (`wc -l` = 1825) ✓
- `run()` at `lib.rs:203` ✓
- `panic_hook::setup_panic_hook()` at `lib.rs:205` ✓
- `tauri::Builder::default()` at `lib.rs:207` ✓
- Plugin registrations at lines 211, 252, 254, 275-279 ✓
- `.setup()` at `lib.rs:284` ✓
- `Database::init()` at `lib.rs:383` ✓
- `migrate_from_json()` at `lib.rs:403` ✓
- `AppState::new(db)` at `lib.rs:423` ✓
- `proxy_service.set_app_handle()` at `lib.rs:426` ✓
- `init_default_skill_repos()` at `lib.rs:433` ✓
- Skills SSOT migration at `lib.rs:443` ✓
- Import live configs at `lib.rs:496-529` ✓
- Seed official providers at `lib.rs:531` ✓
- Import additive mode providers at `lib.rs:579-599` ✓
- Import OMO configs at `lib.rs:602-650` ✓
- Import MCP servers at `lib.rs:653-695` ✓
- Import prompts at `lib.rs:698-720` ✓
- Register deep link handler at `lib.rs:768` ✓
- Create tray menu at `lib.rs:794` ✓
- `app.manage(app_state)` at `lib.rs:845` ✓
- Init SkillService at `lib.rs:861` ✓
- Init CopilotAuthManager at `lib.rs:871` ✓
- Init CodexOAuthManager at `lib.rs:883` ✓
- Init global proxy client at `lib.rs:893` ✓
- Silent startup at `lib.rs:1041` ✓
- `invoke_handler` at `lib.rs:1072` ✓
- `app.run()` at `lib.rs:1383` ✓
- Exit flow at `lib.rs:1383-1410` ✓
- `cleanup_before_exit()` at `lib.rs:1513` ✓
- `stop_with_restore_keep_state()` at `lib.rs:1531` ✓
- 100ms sleep at `lib.rs:1406` ✓
- 9 plugins registered (single_instance, deep_link, process, dialog, opener, store, window_state, updater, log) ✓
- `AppState` at `store.rs:6` ✓
- `SwitchLockManager` at `proxy/switch_lock.rs:14` ✓
- `lock_for_app` at `switch_lock.rs:26` ✓
- `ProxyService` at `services/proxy.rs:55` ✓
- `SETTINGS_STORE` at `settings.rs:519` ✓
- `settings_store()` at `settings.rs:521` ✓
- `mutate_settings` at `settings.rs:574` (private, param `mutator`) ✓
- `is_additive_mode()` at `app_config.rs:373` ✓
- `CircuitBreakerConfig::from(&AppProxyConfig)` at `circuit_breaker.rs:51` ✓
- `lock_conn!` macro at `database/mod.rs:61` ✓
- `App.tsx` is 1604 lines ✓
- `useProviderActions.ts` is 385 lines ✓
- hooks/ directory has 25 files ✓
- lib/query/ directory has 10 files ✓
- `switch_proxy_provider` command at `commands/proxy.rs:277` ✓
- `hot_switch_provider` at `services/proxy.rs:1811` ✓
