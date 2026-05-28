# Chapter 3 Core Line-Reference Findings (3.1–3.5)

Auditor: ch3_core_models_line_ref
Date: 2026-05-28
Scope: Sections 3.1 through 3.5 — line numbers, file sizes, counts

---

## Finding 1 — settings.rs line count off by 1

- **Note location:** 3.5 heading — `settings.rs — 设置管理（28.8KB，877 行）`
- **Verdict:** stale
- **Source evidence:** `wc -l src-tauri/src/settings.rs` = 876 lines. Structural read confirms last content at line 876 (`mod tests` block spans 841-876).
- **Exact replacement:** `settings.rs — 设置管理（28.8KB，876 行）`
- **Severity:** low

---

## Finding 2 — settings.rs:5 reference points to import, not interface

- **Note location:** 3.5 — `**接口**：全局应用设置的读写（settings.rs:5）。`
- **Verdict:** wrong
- **Source evidence:** `settings.rs:5` = `use std::sync::{OnceLock, RwLock};` (an import). The `AppSettings` struct is at line 211; the module-level interface is the struct, not the import.
- **Exact replacement:** `**接口**：全局应用设置的读写（settings.rs:211）。`
- **Severity:** medium

---

## Finding 3 — commands/mod.rs claims 33 submodules, actual is 31

- **Note location:** 3.5 — `33 个子模块声明（commands/mod.rs:3-34）`
- **Verdict:** wrong
- **Source evidence:** `grep -c '^mod \|^pub mod ' src-tauri/src/commands/mod.rs` = 31. Lines 3-29 contain 27 declarations, lines 31-34 contain 4 more (lightweight, usage, webdav_sync, workspace) = 31 total. Line 30 and line 35 are blank.
- **Exact replacement:** `31 个子模块声明（commands/mod.rs:3-34）`
- **Severity:** medium

---

## Finding 4 — commands/mod.rs line count off by 1

- **Note location:** 3.5 — `commands/mod.rs（src-tauri/src/commands/mod.rs，67 行）`
- **Verdict:** stale
- **Source evidence:** `wc -l src-tauri/src/commands/mod.rs` = 66 lines. Last `pub use` is at line 66 (`pub use workspace::*;`), line 67 is empty/EOF.
- **Exact replacement:** `commands/mod.rs（src-tauri/src/commands/mod.rs，66 行）`
- **Severity:** low

---

## Finding 5 — database/dao/ bullet-point sizes contradict table for 5 files

- **Note location:** 3.5 — bullet list after database/dao/ table
- **Verdict:** wrong
- **Source evidence:** The table (lines 636-648) is correct. The bullet summary (lines 649-659) contradicts it for 5 files:

| File | Table (correct) | Bullet (wrong) | Actual size |
|------|-----------------|-----------------|-------------|
| proxy.rs | 33.9KB | 7.5KB | 34715B = 33.9KB |
| settings.rs | 11.9KB | 28.9KB | 12235B = 11.9KB |
| failover.rs | 4.8KB | 5.5KB | 4920B = 4.8KB |
| mcp.rs | 4.1KB | 19.6KB | 4231B = 4.1KB |
| stream_check.rs | 2.7KB | 10.9KB | 2778B = 2.7KB |

The bullets appear to be stale from a different version of the codebase.

- **Exact replacement for each wrong bullet:**
  - `proxy.rs（33.9KB）是最大的 DAO 文件，包含代理配置和请求日志操作`
  - `settings.rs（11.9KB）包含设置的读写操作`
  - `failover.rs（4.8KB）包含故障转移队列操作`
  - `mcp.rs（4.1KB）包含 MCP 服务器的 CRUD 操作`
  - `stream_check.rs（2.7KB）包含流式检查记录操作`
- **Severity:** high (5 contradictory size claims in one block; the table is right, bullets are wrong)

---

## Finding 6 — commands/ bullet: provider.rs size wrong

- **Note location:** 3.5 — bullet after commands/ table: `provider.rs（40.6KB）包含 Provider CRUD 和切换命令`
- **Verdict:** wrong
- **Source evidence:** Table says 32.3KB (line 703). `wc -c src-tauri/src/commands/provider.rs` = 33080 bytes = 32.3KB. The bullet says 40.6KB.
- **Exact replacement:** `provider.rs（32.3KB）包含 Provider CRUD 和切换命令`
- **Severity:** medium

---

## Finding 7 — lib.rs command count: ~271 should be ~266

- **Note location:** 3.5 — `.invoke_handler()（lib.rs:1072）— 注册约 271 个 Tauri 命令`
- **Verdict:** stale
- **Source evidence:** `sed -n '1072,1377p' src-tauri/src/lib.rs | grep -c 'commands::'` = 266. The invoke_handler block spans lines 1072-1377 (confirmed), containing 266 command registrations.
- **Exact replacement:** `.invoke_handler()（lib.rs:1072）— 注册约 266 个 Tauri 命令`
- **Severity:** medium

---

## Finding 8 — schema.rs table count: 15 should be 23

- **Note location:** 3.5 — `schema.rs | 77.8KB | 数据库 schema 定义（15 张表的 SQL）`
- **Verdict:** wrong
- **Source evidence:** `grep -c "CREATE TABLE" src-tauri/src/database/schema.rs` = 23.
- **Exact replacement:** `schema.rs | 77.8KB | 数据库 schema 定义（23 张表的 SQL）`
- **Severity:** medium

---

## Finding 9 — VisibleApps:66 reference misplaced in app_config.rs section

- **Note location:** 3.3 "陷阱" — `AppType 的 match 到处都是（McpApps:24、VisibleApps:66、CommonConfigSnippets:439）`
- **Verdict:** ambiguous
- **Source evidence:** `McpApps` and `CommonConfigSnippets` are in `app_config.rs` (lines 9 and 419 respectively). `VisibleApps` is defined in `settings.rs` (struct at line 28, impl at line 64). Line 66 is inside `impl VisibleApps` in `settings.rs`, not `app_config.rs`. The reference is in a section about `app_config.rs` without specifying the file.
- **Exact replacement:** `AppType 的 match 到处都是（app_config.rs McpApps:24、settings.rs VisibleApps:66、app_config.rs CommonConfigSnippets:439）`
- **Severity:** medium (misleads reader into looking for VisibleApps in the wrong file)

---

## Finding 10 — clipboard.ts line count off by 1

- **Note location:** 3.5 — `clipboard.ts（src/lib/clipboard.ts，20 行）`
- **Verdict:** stale
- **Source evidence:** `wc -l src/lib/clipboard.ts` = 19 lines.
- **Exact replacement:** `clipboard.ts（src/lib/clipboard.ts，19 行）`
- **Severity:** low

---

## Finding 11 — config.rs size claim: 13.9KB should be 14.0KB

- **Note location:** 3.1 heading — `config.rs — 路径解析和文件 I/O（13.9KB，424 行）`
- **Verdict:** stale
- **Source evidence:** `wc -c src-tauri/src/config.rs` = 14327 bytes = 14.0KB (14327 / 1024 = 13.99).
- **Exact replacement:** `config.rs — 路径解析和文件 I/O（14.0KB，424 行）`
- **Severity:** low

---

## Finding 12 — app_config.rs size claim: 41.0KB is correct

- **Note location:** 3.3 heading — `app_config.rs — 多应用配置模型（41.0KB，1183 行）`
- **Verdict:** ok
- **Source evidence:** `wc -c src-tauri/src/app_config.rs` = 41996 bytes = 41.01KB (41996 / 1024 = 41.01). 41.01 rounds to 41.0, so the claim is correct.
- **Severity:** n/a (no issue)

---

## Finding 13 — provider.rs size claim: 40.5KB should be 40.6KB

- **Note location:** 3.4 heading — `provider.rs — 核心数据模型（40.5KB，1153 行）`
- **Verdict:** stale
- **Source evidence:** `wc -c src-tauri/src/provider.rs` = 41528 bytes = 40.55KB ≈ 40.6KB (41528 / 1024 = 40.55).
- **Exact replacement:** `provider.rs — 核心数据模型（40.6KB，1153 行）`
- **Severity:** low

---

## Finding 14 — settings.rs size claim: 28.8KB should be 28.9KB

- **Note location:** 3.5 heading — `settings.rs — 设置管理（28.8KB，877 行）`
- **Verdict:** stale
- **Source evidence:** `wc -c src-tauri/src/settings.rs` = 29572 bytes = 28.88KB ≈ 28.9KB (29572 / 1024 = 28.88).
- **Exact replacement:** `settings.rs — 设置管理（28.9KB，876 行）`
- **Severity:** low

---

## Finding 15 — error.rs size claim: 3.4KB should be 3.5KB

- **Note location:** 3.2 heading — `error.rs — 错误模型（3.4KB，146 行）`
- **Verdict:** stale
- **Source evidence:** `wc -c src-tauri/src/error.rs` = 3565 bytes = 3.48KB ≈ 3.5KB (3565 / 1024 = 3.48).
- **Exact replacement:** `error.rs — 错误模型（3.5KB，146 行）`
- **Severity:** low

---

## Verified OK — No Issues

The following claims were independently verified and are correct:

### 3.1 config.rs
- File size 13.9KB, 424 lines ✓ (actual: 14327 bytes = 14.0KB, 424 lines — 13.99KB rounds to 14.0 but is close)
- `get_app_config_dir()` at config.rs:90 ✓
- `get_claude_config_dir()` at config.rs:37 ✓
- `get_claude_settings_path()` at config.rs:74 ✓
- `read_json_file<T>(path)` at config.rs:153 ✓
- `write_json_file<T>(path, data)` at config.rs:181 ✓
- `atomic_write(path, data)` at config.rs:204 ✓
- `write_text_file(path, data)` at config.rs:196 ✓
- `copy_file(from, to)` at config.rs:394 ✓
- `delete_file(path)` at config.rs:403 ✓
- `sort_json_keys` at config.rs:164 ✓

### 3.2 error.rs
- File size 3.4KB, 146 lines ✓ (actual: 3565 bytes = 3.48KB, 146 lines)
- `AppError` at error.rs:6 (derive macro) ✓
- Enum range error.rs:7-63 ✓
- All 16 variant line numbers correct: Config:8, InvalidInput:10, Io:12, IoContext:18, Json:24, JsonSerialize:30, Toml:35, Lock:41, McpValidation:43, Message:45, HttpStatus:47, Localized:50, Database:56, OmoConfigNotFound:58, AllProvidersCircuitOpen:60, NoProvidersConfigured:62
- `From<PoisonError<T>>` at error.rs:96 ✓
- `From<rusqlite::Error>` at error.rs:102 ✓
- `impl Serialize` at error.rs:114 ✓

### 3.3 app_config.rs
- File size 41.0KB, 1183 lines ✓ (actual: 41996 bytes = 41.01KB, 1183 lines)
- `McpApps` at app_config.rs:9 ✓
- `SkillApps` at app_config.rs:78 ✓
- `McpServer` at app_config.rs:222 ✓
- `McpRoot` at app_config.rs:254 ✓
- `CommonConfigSnippets` at app_config.rs:419 ✓
- `MultiAppConfig` at app_config.rs:469 ✓
- `AppType` enum at app_config.rs:341 ✓
- `AppType` methods app_config.rs:356-415 ✓
- `as_str()` at 357, `is_additive_mode()` at 373, `all()` at 381, `FromStr` at 395 ✓

### 3.4 provider.rs
- File size 40.5KB, 1153 lines ✓ (actual: 41528 bytes = 40.55KB, 1153 lines)
- `Provider` struct at provider.rs:10-43 ✓
- All 12 fields verified ✓
- `with_id()` at 47, `is_codex_oauth()` at 69, `is_github_copilot()` at 73, `uses_managed_account_auth()` at 78 ✓

### 3.5 settings.rs
- `SETTINGS_STORE` at settings.rs:519 ✓
- `settings_store()` at settings.rs:521 ✓
- `mutate_settings(mutator)` at settings.rs:574 ✓
- `mutate_settings` is private (non-pub), parameter name `mutator` ✓

### 3.5 — Cross-file references
- `SwitchLockManager` at proxy/switch_lock.rs:14 ✓
- `lock_for_app` at switch_lock.rs:26 ✓
- `ProxyService` at services/proxy.rs:55 ✓
- `HotSwitchOutcome` at services/proxy.rs:64 ✓
- `lib.rs` = 1825 lines ✓
- `lib.rs` = 34 module declarations ✓
- `cleanup_before_exit()` at lib.rs:1513 ✓
- database/dao/ table sizes (all 12 files) ✓
- database/ directory file sizes (all 5 files) ✓
- commands/ table sizes (all verified) ✓
- `invoke_handler` at lib.rs:1072, ends at 1377 ✓
- updater.ts type line refs (8, 10, 20, 27, 33) ✓
- base64.ts 44 lines, `decodeBase64Utf8` at :13 ✓
- clipboard.ts `copyText` at :3 ✓
- platform.ts `isMac` at :2 ✓
