# Chapter 1 Skeptic Findings

Adversarial pass: every architecture statement assumed fabricated until source proves it.

---

## Finding 1: Internal inconsistency — invoke_handler command count

**note location**: 1.1 应用生命周期, line 55 (`~266 个命令`) vs line 63 (`~271 个命令`) vs line 86 (`约 271 个命令`)

**verdict**: wrong

**source evidence**: `src-tauri/src/lib.rs:1072-1377` — counting every `commands::*` and `update_tray_menu` entry inside `tauri::generate_handler![...]` yields **267** commands. The note states three different numbers (~266, ~271, ~271) in the same chapter.

**severity**: medium

**fix**: Replace all three occurrences with `~267 个命令`.

---

## Finding 2: Internal inconsistency — setup closure line count

**note location**: 1.1 应用生命周期, line 62 (`约 790 行（284-1070）`) vs line 81 (`786 行的 .setup() 闭包`)

**verdict**: wrong

**source evidence**: `src-tauri/src/lib.rs:284-1071` — `.setup(|app| {` at line 284, `})` at line 1071. Inclusive count = 1071 − 284 + 1 = **788 lines**. Neither 790 nor 786 is correct.

**severity**: medium

**fix**: Replace both with `788 行（284-1071）`.

---

## Finding 3: Hook line counts — useProxyStatus.ts stale

**note location**: 1.3 状态管理, line 211 (`useProxyStatus.ts (185 行)`)

**verdict**: stale

**source evidence**: `src/hooks/useProxyStatus.ts` — `wc -l` returns **245** lines.

**severity**: low

**fix**: Replace `185 行` with `245 行`.

---

## Finding 4: Hook line counts — useDirectorySettings.ts stale

**note location**: 1.3 状态管理, line 212 (`useDirectorySettings.ts (275 行)`)

**verdict**: stale

**source evidence**: `src/hooks/useDirectorySettings.ts` — `wc -l` returns **373** lines.

**severity**: low

**fix**: Replace `275 行` with `373 行`.

---

## Finding 5: Hook line counts — useSettings.ts stale

**note location**: 1.3 状态管理, line 209 (`useSettings.ts (512 行)`)

**verdict**: stale

**source evidence**: `src/hooks/useSettings.ts` — `wc -l` returns **505** lines.

**severity**: low

**fix**: Replace `512 行` with `505 行`.

---

## Finding 6: Hook line counts — useDragSort.ts stale

**note location**: 1.3 状态管理, line 213 (`useDragSort.ts (95 行)`)

**verdict**: stale

**source evidence**: `src/hooks/useDragSort.ts` — `wc -l` returns **119** lines.

**severity**: low

**fix**: Replace `95 行` with `119 行`.

---

## Finding 7: commands/ submodule count wrong

**note location**: 1.4 模块依赖全景图, line 252 (`commands/ 34 个子模块`)

**verdict**: wrong

**source evidence**: `src-tauri/src/commands/` — `find -maxdepth 1 -name "*.rs"` yields 32 files (including `mod.rs`), i.e. **31 submodules**.

**severity**: medium

**fix**: Replace `34 个子模块` with `31 个子模块`.

---

## Finding 8: Function name truncated — app_store::refresh()

**note location**: 1.1 应用生命周期, line 30 (`app_store::refresh()  // lib.rs:288`)

**verdict**: wrong

**source evidence**: `src-tauri/src/lib.rs:288` — the actual call is `app_store::refresh_app_config_dir_override(app.handle());`, not `app_store::refresh()`.

**severity**: medium

**fix**: Replace `app_store::refresh()` with `app_store::refresh_app_config_dir_override()`.

---

## Finding 9: Session usage sync loop line reference off

**note location**: 1.1 应用生命周期, line 53 (`session usage sync loop  // lib.rs:999`)

**verdict**: ambiguous

**source evidence**: `src-tauri/src/lib.rs:999` is `crate::services::session_usage_gemini::sync_gemini_usage(db),` — the last call in the initial sync block. The loop itself (with `tokio::time::interval`) starts at line 1002. The spawned async block containing both starts at line 972.

**severity**: low

**fix**: Replace `lib.rs:999` with `lib.rs:972` (the spawned async block that contains both initial sync and periodic loop).

---

## Finding 10: Query file line counts — all off by 1

**note location**: 1.3 状态管理, lines 216-221

| File | Claimed | Actual |
|------|---------|--------|
| queries.ts | 156 | 155 |
| mutations.ts | 357 | 356 |
| proxy.ts | 244 | 243 |
| failover.ts | 289 | 288 |
| usage.ts | 320 | 319 |
| subscription.ts | 64 | 63 |

**verdict**: stale

**source evidence**: `wc -l` on each file in `src/lib/query/`.

**severity**: low

**fix**: Update each count to the actual value.

---

## Finding 11: services/ submodule count — slightly off

**note location**: 1.4 模块依赖全景图, line 252 (`services/ 25 个子模块`)

**verdict**: ambiguous

**source evidence**: `src-tauri/src/services/` — 25 `.rs` files at top level (including `mod.rs`), plus 2 subdirectories (`provider/`, `webdav_sync/`). If counting only `.rs` files the number is 25; if counting all submodules including subdirectories it is 27. The note does not clarify which counting method is used.

**severity**: low

**fix**: No change needed if counting `.rs` files only. Consider adding note that subdirectories are not counted.

---

## Verified OK Claims

The following claims were independently verified against source and found correct:

- `main.rs` is 22 lines (`src-tauri/src/main.rs:1-22`) ✓
- `lib.rs` is 1825 lines (`wc -l src-tauri/src/lib.rs`) ✓
- `lib.rs` declares 34 modules (lines 1-36, including cfg-conditional `linux_fix`) ✓
- `run()` at `lib.rs:203` ✓
- `panic_hook::setup_panic_hook()` at `lib.rs:205` ✓
- `tauri::Builder::default()` at `lib.rs:207` ✓
- All 9 plugin registrations at stated line numbers ✓
- `.setup(|app| {` at `lib.rs:284` ✓
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
- `initialize_common_config_snippets()` defined at `lib.rs:1601` ✓
- `restore_proxy_state_on_startup()` defined at `lib.rs:1558` ✓
- Silent startup at `lib.rs:1041` ✓
- `.invoke_handler()` at `lib.rs:1072` ✓
- `app.run()` at `lib.rs:1383` ✓
- Exit flow at `lib.rs:1383` with save window state at `lib.rs:1401` ✓
- `cleanup_before_exit()` at `lib.rs:1513` ✓
- `stop_with_restore_keep_state()` at `lib.rs:1531` ✓
- 100ms wait at `lib.rs:1406` ✓
- `AppState` struct at `store.rs:6` with correct fields ✓
- `Arc<T>` import at `store.rs:3` ✓
- `Database` with `Mutex<Connection>` at `database/mod.rs:76-77` ✓
- `SwitchLockManager` at `proxy/switch_lock.rs:14` ✓
- `lock_for_app` at `switch_lock.rs:26` ✓
- `ProxyService` at `services/proxy.rs:55` with correct fields ✓
- `SETTINGS_STORE` at `settings.rs:519` ✓
- `settings_store()` at `settings.rs:521` ✓
- `mutate_settings()` at `settings.rs:574`, private, param name `mutator` ✓
- `is_additive_mode()` at `app_config.rs:373` ✓
- Switch vs Additive mode classification (Claude/ClaudeDesktop/Codex/Gemini = switch; OpenCode/OpenClaw/Hermes = additive) ✓
- `App.tsx` is 1604 lines ✓
- hooks/ directory has 25 files ✓
- lib/query/ directory has 10 files ✓
- `switch_provider` registered at `lib.rs:1079` ✓
