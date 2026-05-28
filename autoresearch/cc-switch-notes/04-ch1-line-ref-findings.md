# Chapter 1 Line Reference & Count Findings

Auditor: ch1_line_ref_auditor
Scope: All file:line references, command counts, plugin counts, module counts, and line counts in Chapter 1 (lines 1–265) of `docs/cc-switch-source-notes.md`.

---

## Finding 1: Command count inconsistency — diagram says ~266, text says ~271, actual is 267

**Note location:** §1.1 应用生命周期, line 55 (diagram) and line 63 (key points)

**Quoted claim (diagram):**
```
├─ .invoke_handler(...)     // lib.rs:1072  注册 ~266 个命令
```

**Quoted claim (key points):**
```
`.invoke_handler()` 注册约 271 个 Tauri 命令（1072-1377）
```

**Verdict:** wrong

**Source evidence:**
- `src-tauri/src/lib.rs:1072-1377` — the `invoke_handler` block.
- `sed -n '1073,1377p' src-tauri/src/lib.rs | grep -c 'commands::'` → 266
- Plus `update_tray_menu` at line 1190 (not prefixed with `commands::`) → total = **267**.
- The diagram says "~266" (misses `update_tray_menu`); the text says "~271" (wrong by 4).

**Severity:** medium

**Exact replacement:**
- Diagram line 55: `注册 ~267 个命令`
- Key points line 63: `注册 267 个 Tauri 命令（1072-1377）`
- Section 1.1.1 line 86: `注册命令（.invoke_handler()，lib.rs:1072，267 个命令）`

---

## Finding 2: commands/ submodule count — notes say 34, actual is 32 files

**Note location:** §1.4 模块依赖全景图, line 252

**Quoted claim:**
```
│  commands/  │  │  services/ │  │   proxy/    │
│ 34 个子模块 │  │ 25 个子模块│  │ 35+ 个模块  │
```

**Verdict:** wrong

**Source evidence:**
- `ls -1 src-tauri/src/commands/ | wc -l` → 32 files (30 `.rs` files + `mod.rs` + 1 subdirectory entry if any; the actual listing shows 32 entries).
- Excluding `mod.rs`, there are **31** submodule files.
- The notes claim 34 — off by 3.

**Severity:** medium

**Exact replacement:**
```
│  commands/  │  │  services/ │  │   proxy/    │
│ 31 个子模块 │  │ 26 个子模块│  │ 31 个子模块  │
```

---

## Finding 3: services/ submodule count — notes say 25, actual is 26

**Note location:** §1.4 模块依赖全景图, line 252

**Quoted claim:**
```
│ 25 个子模块│
```

**Verdict:** stale

**Source evidence:**
- `ls -1 src-tauri/src/services/ | wc -l` → 27 entries (25 `.rs` files + 2 subdirectories: `provider/`, `webdav_sync/`).
- Excluding `mod.rs`: **26** submodules.
- The notes claim 25 — off by 1.

**Severity:** medium

**Exact replacement:** `│ 26 个子模块│`

---

## Finding 4: proxy/ submodule count — notes say 35+, actual is 31

**Note location:** §1.4 模块依赖全景图, line 252

**Quoted claim:**
```
│ 35+ 个模块  │
```

**Verdict:** wrong

**Source evidence:**
- `ls -1 src-tauri/src/proxy/ | wc -l` → 32 entries (30 `.rs` files + 2 subdirectories: `providers/`, `usage/`).
- Excluding `mod.rs`: **31** submodules.
- The notes claim "35+" — off by at least 4.

**Severity:** medium

**Exact replacement:** `│ 31 个子模块  │`

---

## Finding 5: setup() closure span — notes say "786 行" and "284-1070", actual is 788 lines / 284-1071

**Note location:** §1.1 应用生命周期, lines 62 and 81

**Quoted claim (line 62):**
```
`.setup()` 闭包约 790 行（284-1070），包含所有初始化逻辑
```

**Quoted claim (line 81):**
```
6. **Setup closure**（`lib.rs:284-1070`）— 786 行的 `.setup()` 闭包：
```

**Verdict:** stale

**Source evidence:**
- `src-tauri/src/lib.rs:284` — `.setup(|app| {`
- `src-tauri/src/lib.rs:1071` — `})`
- Span: 1071 − 284 + 1 = **788 lines**.
- The notes say "786 行" (off by 2) and "284-1070" (should be 284-1071).

**Severity:** low

**Exact replacement:**
- Line 62: `` `.setup()` 闭包约 788 行（284-1071），包含所有初始化逻辑 ``
- Line 81: `6. **Setup closure**（`lib.rs:284-1071`）— 788 行的 `.setup()` 闭包：`

---

## Finding 6: session usage sync loop — notes say lib.rs:999, actual start is lib.rs:972

**Note location:** §1.1 应用生命周期 (setup diagram), line 53

**Quoted claim:**
```
│    ├─ session usage sync loop        // lib.rs:999
```

**Verdict:** wrong

**Source evidence:**
- `src-tauri/src/lib.rs:970` — comment: `// Session log usage sync: 启动时同步一次，之后每 60 秒检查`
- `src-tauri/src/lib.rs:972` — `tauri::async_runtime::spawn(async move {`
- `src-tauri/src/lib.rs:999` — `crate::services::session_usage_gemini::sync_gemini_usage(db),` (one call within the initial sync, not the loop start).

**Severity:** low

**Exact replacement:**
```
│    ├─ session usage sync loop        // lib.rs:972
```

---

## Finding 7: Plugin registration line reference "lib.rs:270+" misleading — updater and log are inside setup()

**Note location:** §1.1.1 run() 启动流程, line 80

**Quoted claim:**
```
5. **Plugin registration**（`lib.rs:270+`）— 注册 9 个插件：single_instance、deep_link、process、dialog、opener、store、window_state、updater、log
```

**Verdict:** ambiguous

**Source evidence:**
- 7 plugins registered in the builder chain (lines 211–282): single_instance, deep_link, process, dialog, opener, store, window_state.
- 2 plugins registered inside `.setup()`: updater (line 294–300, conditional on `#[cfg(desktop)]`), log (line 317–336).
- The line reference "lib.rs:270+" technically covers both, but grouping all 9 under a single "Plugin registration" step with that reference is misleading — the reader would expect them all at that location.

**Severity:** low

**Suggested fix:** Split into two items or clarify:
```
5. **Plugin registration**（`lib.rs:211-282`）— 7 个插件在 builder 链中注册：single_instance、deep_link、process、dialog、opener、store、window_state
   - **Setup 中注册的插件**：updater（`lib.rs:294`，仅桌面端）、log（`lib.rs:317`）
```

---

## Finding 8: useProxyStatus.ts line count — notes say 185, actual is 245

**Note location:** §1.3 状态管理 (前端状态管理层次), line 211

**Quoted claim:**
```
├─ useProxyStatus.ts (185 行)      ← 代理状态轮询
```

**Verdict:** stale

**Source evidence:**
- `wc -l src/hooks/useProxyStatus.ts` → **245 lines**.

**Severity:** medium

**Exact replacement:**
```
├─ useProxyStatus.ts (245 行)      ← 代理状态轮询
```

---

## Finding 9: useDirectorySettings.ts line count — notes say 275, actual is 373

**Note location:** §1.3 状态管理 (前端状态管理层次), line 212

**Quoted claim:**
```
├─ useDirectorySettings.ts (275 行) ← 目录配置
```

**Verdict:** stale

**Source evidence:**
- `wc -l src/hooks/useDirectorySettings.ts` → **373 lines**.

**Severity:** medium

**Exact replacement:**
```
├─ useDirectorySettings.ts (373 行) ← 目录配置
```

---

## Finding 10: useDragSort.ts line count — notes say 95, actual is 119

**Note location:** §1.3 状态管理 (前端状态管理层次), line 213

**Quoted claim:**
```
└─ useDragSort.ts (95 行)          ← 拖拽排序
```

**Verdict:** stale

**Source evidence:**
- `wc -l src/hooks/useDragSort.ts` → **119 lines**.

**Severity:** low

**Exact replacement:**
```
└─ useDragSort.ts (119 行)          ← 拖拽排序
```

---

## Finding 11: useSettings.ts line count — notes say 512, actual is 505

**Note location:** §1.3 状态管理 (前端状态管理层次), line 209

**Quoted claim:**
```
├─ useSettings.ts (512 行)         ← 设置管理（读写、同步）
```

**Verdict:** stale

**Source evidence:**
- `wc -l src/hooks/useSettings.ts` → **505 lines**.

**Severity:** low

**Exact replacement:**
```
├─ useSettings.ts (505 行)         ← 设置管理（读写、同步）
```

---

## Finding 12: All lib/query/ file line counts off by exactly 1

**Note location:** §1.3 状态管理 (前端状态管理层次), lines 216–221

**Quoted claims and actuals:**

| File | Notes claim | Actual (`wc -l`) | Delta |
|------|-------------|-------------------|-------|
| queries.ts | 156 | 155 | −1 |
| mutations.ts | 357 | 356 | −1 |
| proxy.ts | 244 | 243 | −1 |
| failover.ts | 289 | 288 | −1 |
| usage.ts | 320 | 319 | −1 |
| subscription.ts | 64 | 63 | −1 |

**Verdict:** stale

**Source evidence:**
- All six files are off by exactly 1 line, suggesting the notes were generated by a tool that counts lines differently (e.g., including a trailing empty line that `wc -l` does not count).

**Severity:** low

**Exact replacements:**
```
├─ queries.ts (155 行)
├─ mutations.ts (356 行)
├─ proxy.ts (243 行)
├─ failover.ts (288 行)
├─ usage.ts (319 行)
└─ subscription.ts (63 行)
```

---

## Finding 13: lib.rs line count — notes say 1825, matches `wc -l`

**Note location:** §1.1 应用生命周期, line 61

**Quoted claim:**
```
`lib.rs`（1825 行）是整个后端的"上帝文件"
```

**Verdict:** ok

**Source evidence:**
- `wc -l src-tauri/src/lib.rs` → 1825.
- The `read` tool shows 1826 lines because it includes the trailing empty line after the final newline, but `wc -l` counts 1825.

**Severity:** n/a

---

## Finding 14: All lib.rs:line references in the startup diagram — verified correct

**Note location:** §1.1 应用生命周期, lines 17–56 (startup diagram)

**Verified references (all ok):**

| Claim | Source |
|-------|--------|
| `main.rs:4` — `fn main()` | `src-tauri/src/main.rs:4` ✓ |
| `lib.rs:203` — `pub fn run()` | `src-tauri/src/lib.rs:203` ✓ |
| `lib.rs:205` — `panic_hook::setup_panic_hook()` | `src-tauri/src/lib.rs:205` ✓ |
| `lib.rs:207` — `tauri::Builder::default()` | `src-tauri/src/lib.rs:207` ✓ |
| `lib.rs:211` — `.plugin(single_instance)` | `src-tauri/src/lib.rs:211` ✓ |
| `lib.rs:252` — `.plugin(deep_link)` | `src-tauri/src/lib.rs:252` ✓ |
| `lib.rs:254` — `.on_window_event()` | `src-tauri/src/lib.rs:254` ✓ |
| `lib.rs:275` — `.plugin(process)` | `src-tauri/src/lib.rs:275` ✓ |
| `lib.rs:276` — `.plugin(dialog)` | `src-tauri/src/lib.rs:276` ✓ |
| `lib.rs:277` — `.plugin(opener)` | `src-tauri/src/lib.rs:277` ✓ |
| `lib.rs:278` — `.plugin(store)` | `src-tauri/src/lib.rs:278` ✓ |
| `lib.rs:279` — `.plugin(window_state)` | `src-tauri/src/lib.rs:279` ✓ |
| `lib.rs:284` — `.setup(\|app\| {` | `src-tauri/src/lib.rs:284` ✓ |
| `lib.rs:288` — `app_store::refresh_app_config_dir_override()` | `src-tauri/src/lib.rs:288` ✓ |
| `lib.rs:317` — init log plugin | `src-tauri/src/lib.rs:317` ✓ |
| `lib.rs:383` — `Database::init()` | `src-tauri/src/lib.rs:383` ✓ |
| `lib.rs:403` — `migrate_from_json()` | `src-tauri/src/lib.rs:403` ✓ |
| `lib.rs:423` — `AppState::new(db)` | `src-tauri/src/lib.rs:423` ✓ |
| `lib.rs:426` — `proxy_service.set_app_handle()` | `src-tauri/src/lib.rs:426` ✓ |
| `lib.rs:433` — `init_default_skill_repos()` | `src-tauri/src/lib.rs:433` ✓ |
| `lib.rs:443` — skills SSOT migration | `src-tauri/src/lib.rs:443` ✓ |
| `lib.rs:496-529` — import live configs | `src-tauri/src/lib.rs:496-529` ✓ |
| `lib.rs:531` — seed official providers | `src-tauri/src/lib.rs:531` ✓ |
| `lib.rs:579-599` — import additive mode providers | `src-tauri/src/lib.rs:579-599` ✓ |
| `lib.rs:602-650` — import OMO configs | `src-tauri/src/lib.rs:602-650` ✓ |
| `lib.rs:653-695` — import MCP servers | `src-tauri/src/lib.rs:653-695` ✓ |
| `lib.rs:698-720` — import prompts | `src-tauri/src/lib.rs:698-720` ✓ |
| `lib.rs:768` — register deep link handler | `src-tauri/src/lib.rs:768` ✓ |
| `lib.rs:794` — create tray menu | `src-tauri/src/lib.rs:794` ✓ |
| `lib.rs:845` — `app.manage(app_state)` | `src-tauri/src/lib.rs:845` ✓ |
| `lib.rs:861` — init SkillService | `src-tauri/src/lib.rs:861` ✓ |
| `lib.rs:871` — init CopilotAuthManager | `src-tauri/src/lib.rs:871` ✓ |
| `lib.rs:883` — init CodexOAuthManager | `src-tauri/src/lib.rs:883` ✓ |
| `lib.rs:893` — init global proxy client | `src-tauri/src/lib.rs:893` ✓ |
| `lib.rs:1601` — `initialize_common_config_snippets()` | `src-tauri/src/lib.rs:1601` ✓ |
| `lib.rs:1558` — `restore_proxy_state_on_startup()` | `src-tauri/src/lib.rs:1558` ✓ |
| `lib.rs:1041` — silent startup or show window | `src-tauri/src/lib.rs:1041` ✓ |
| `lib.rs:1072` — `.invoke_handler(...)` | `src-tauri/src/lib.rs:1072` ✓ |
| `lib.rs:1383` — `app.run(...)` | `src-tauri/src/lib.rs:1383` ✓ |

---

## Finding 15: Exit flow references — verified correct

**Note location:** §1.1 应用生命周期, lines 66–70

| Claim | Source |
|-------|--------|
| `lib.rs:1383` — exit flow entry | `src-tauri/src/lib.rs:1383` ✓ |
| `lib.rs:1401` — save window state | `src-tauri/src/lib.rs:1401` ✓ |
| `lib.rs:1513` — `cleanup_before_exit()` | `src-tauri/src/lib.rs:1513` ✓ |
| `lib.rs:1531` — `stop_with_restore_keep_state()` | `src-tauri/src/lib.rs:1531` ✓ |
| `lib.rs:1406` — 100ms wait | `src-tauri/src/lib.rs:1406` ✓ |

**Verdict:** ok

---

## Finding 16: Plugin count (9) — verified correct

**Note location:** §1.1 应用生命周期, line 64 and §1.1.1, line 80

**Quoted claim:**
```
9 个插件被注册（single_instance、deep_link、process、dialog、opener、store、window_state、updater、log）
```

**Verdict:** ok

**Source evidence:**
- Builder chain (7): single_instance:211, deep_link:252, process:275, dialog:276, opener:277, store:278, window_state:279
- Inside setup (2): updater:294 (desktop only), log:317
- Total: 9 ✓

---

## Finding 17: Module count in lib.rs (34) — verified correct

**Note location:** §1.4 模块依赖全景图, line 245

**Quoted claim:**
```
│   lib.rs    │  1825 行，声明 34 个模块
```

**Verdict:** ok

**Source evidence:**
- `src-tauri/src/lib.rs:1-36` — 34 `mod` declarations (including conditional `linux_fix`).

---

## Finding 18: store.rs, database/mod.rs, settings.rs, proxy/switch_lock.rs, services/proxy.rs references — verified correct

**Note location:** §1.3 状态管理, lines 153–198

| Claim | Source | Verdict |
|-------|--------|---------|
| `store.rs:6` — `pub struct AppState` | `src-tauri/src/store.rs:6` ✓ | ok |
| `store.rs:3` — `use std::sync::Arc` | `src-tauri/src/store.rs:3` ✓ | ok |
| `store.rs:7` — `pub db: Arc<Database>` | `src-tauri/src/store.rs:7` ✓ | ok |
| `database/mod.rs:76` — `pub struct Database` | `src-tauri/src/database/mod.rs:76` ✓ | ok |
| `database/mod.rs:77` — `conn: Mutex<Connection>` | `src-tauri/src/database/mod.rs:77` ✓ | ok |
| `database/mod.rs:61` — `lock_conn!` macro | `src-tauri/src/database/mod.rs:61` ✓ | ok |
| `proxy/switch_lock.rs:14` — `SwitchLockManager` | `src-tauri/src/proxy/switch_lock.rs:14` ✓ | ok |
| `switch_lock.rs:26` — `lock_for_app()` | `src-tauri/src/proxy/switch_lock.rs:26` ✓ | ok |
| `services/proxy.rs:55` — `ProxyService` | `src-tauri/src/services/proxy.rs:55` ✓ | ok |
| `settings.rs:519` — `SETTINGS_STORE` | `src-tauri/src/settings.rs:519` ✓ | ok |
| `settings.rs:521` — `settings_store()` | `src-tauri/src/settings.rs:521` ✓ | ok |
| `settings.rs:574` — `mutate_settings()` | `src-tauri/src/settings.rs:574` ✓ | ok |
| `app_config.rs:373` — `is_additive_mode()` | `src-tauri/src/app_config.rs:373` ✓ | ok |
| `lib.rs:1079` — `commands::switch_provider` | `src-tauri/src/lib.rs:1079` ✓ | ok |

---

## Finding 19: App.tsx line count (1604) and hooks count (25) — verified correct

**Note location:** §1.3 状态管理, lines 202 and 208

| Claim | Source | Verdict |
|-------|--------|---------|
| `App.tsx (1604 行)` | `wc -l src/App.tsx` → 1604 ✓ | ok |
| `hooks/ 目录（25 个 hooks）` | `ls -1 src/hooks/ \| wc -l` → 25 ✓ | ok |
| `lib/query/ 目录（10 个文件）` | `ls -1 src/lib/query/ \| wc -l` → 10 ✓ | ok |

---

## Finding 20: Chapter 2 references within Chapter 1 scope — error.rs and circuit_breaker.rs verified correct

| Claim | Source | Verdict |
|-------|--------|---------|
| `error.rs:6` — `AppError` | `src-tauri/src/error.rs:6` (derive attribute) ✓ | ok |
| `circuit_breaker.rs:51` — `impl From<&AppProxyConfig>` | `src-tauri/src/proxy/circuit_breaker.rs:51` ✓ | ok |

---

## Summary

| # | Finding | Verdict | Severity |
|---|---------|---------|----------|
| 1 | Command count: diagram ~266, text ~271, actual 267 | wrong | medium |
| 2 | commands/ submodule count: notes 34, actual 31 | wrong | medium |
| 3 | services/ submodule count: notes 25, actual 26 | stale | medium |
| 4 | proxy/ submodule count: notes 35+, actual 31 | wrong | medium |
| 5 | setup() closure: notes "786 行 / 284-1070", actual 788 行 / 284-1071 | stale | low |
| 6 | session usage sync loop: notes lib.rs:999, actual lib.rs:972 | wrong | low |
| 7 | Plugin registration "lib.rs:270+" groups all 9 plugins but 2 are inside setup() | ambiguous | low |
| 8 | useProxyStatus.ts: notes 185, actual 245 | stale | medium |
| 9 | useDirectorySettings.ts: notes 275, actual 373 | stale | medium |
| 10 | useDragSort.ts: notes 95, actual 119 | stale | low |
| 11 | useSettings.ts: notes 512, actual 505 | stale | low |
| 12 | All lib/query/ files off by exactly 1 line | stale | low |
| 13–20 | All other references verified correct | ok | — |
