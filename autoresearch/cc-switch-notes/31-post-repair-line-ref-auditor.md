# Post-Repair Line Reference Audit — docs/cc-switch-source-notes.md

Date: 2026-05-28
Scope: file:line references, markdown headings, code fences in primary (non-duplicate) content
Auditor: post-repair-line-ref-auditor

---

## PASS/FAIL: FAIL — 7 unresolved must-fix issues in primary content

---

## 1. Unresolved Must-Fix Issues

### 1.1 Stray code fence creates unclosed fence (line 2876)

Line 2875 properly closes the `Database::init()` code block. Line 2876 contains a stray ```` ``` ```` marker with no matching opener. This leaves the document with one unclosed code fence (depth never returns to 0 after line 2875).

**Location**: `docs/cc-switch-source-notes.md:2876`
**Evidence**: Depth tracker confirms last depth=0 at line 2875, final depth=1. Line 2876 is the first unclosed opening fence.
**Fix**: Delete line 2876 (the stray ```` ``` ````).

### 1.2 Broken ASCII art — duplicate lines in module dependency chart (lines 253–254)

The repair added the corrected line "31 个子模块" (line 254) but did not remove the stale "34 个子模块" (line 253). The chart now renders with two entries for the commands/ box, breaking the layout.

**Location**: `docs/cc-switch-source-notes.md:253-254`
**Source**: `src-tauri/src/commands/mod.rs` has 31 `mod` declarations (lines 3–34, confirmed by `grep -c`).
**Fix**: Delete line 253 (`│ 34 个子模块 │`).

### 1.3 Broken diagram — duplicate polling interval lines (lines 206–207)

Same pattern as 1.2: the repair added the corrected "每 2 秒" line (207) but did not remove the stale "每 5 秒" line (206).

**Location**: `docs/cc-switch-source-notes.md:206-207`
**Source**: `src/hooks/useProxyStatus.ts:28` shows `refetchInterval: ... 2000` (2 seconds).
**Fix**: Delete line 206 (`└─ useProxyStatus()                 ← 轮询代理状态（每 5 秒）`).

### 1.4 Stale localStorage key "currentView" (lines 203, 232)

Two references to `localStorage("currentView")` in the primary data-flow diagrams. The actual key is `"cc-switch-last-view"` (`src/App.tsx:138`).

**Location**: `docs/cc-switch-source-notes.md:203` and `docs/cc-switch-source-notes.md:232`
**Source**: `src/App.tsx:138` has `const VIEW_STORAGE_KEY = "cc-switch-last-view";`
**Fix**: Replace `localStorage("currentView")` with `localStorage("cc-switch-last-view")` at both locations.

### 1.5 Stale "34 个模块声明" for lib.rs (line 756)

The first occurrence of the lib.rs module listing (in primary Ch3 content) still says "34 个模块声明". Source has 35 `mod` declarations in `lib.rs:1-36`.

**Location**: `docs/cc-switch-source-notes.md:756`
**Source**: `src-tauri/src/lib.rs:1-36` — 35 `mod` statements (lines 1–33, 35–36; line 34 is blank).
**Fix**: Change "34 个模块声明" to "35 个模块声明".

### 1.6 Stale "~271 个 Tauri 命令" (line 759)

Same section as 1.5. The invoke_handler registers exactly 266 commands (`grep -c '^\s*commands::' lib.rs` = 266).

**Location**: `docs/cc-switch-source-notes.md:759`
**Source**: `src-tauri/src/lib.rs:1072-1377` — 266 `commands::` entries.
**Fix**: Change "约 271 个 Tauri 命令" to "~266 个 Tauri 命令".

### 1.7 Stale "34 个模块" in module dependency chart (line 246)

The chart header still says "声明 34 个模块" for lib.rs. Should be 35.

**Location**: `docs/cc-switch-source-notes.md:246`
**Source**: Same as 1.5 — 35 mod declarations.
**Fix**: Change "声明 34 个模块" to "声明 35 个模块".

---

## 2. Known Duplicate-Block Issues (Not Repaired — Acknowledged)

These are in verbatim-duplicate sections that the repair log (item #1 in "Claims intentionally left unchanged") explicitly deferred. They carry the same errors as their pre-repair originals.

| Notes line | Stale claim | Correct value | Source |
|---|---|---|---|
| 1650, 3013, 5520, 6956 | "33 个子模块声明（commands/mod.rs:3-34）" | 31 | `grep -c '^mod \|^pub mod ' commands/mod.rs` = 31 |
| 1723, 3086, 5593, 7029 | "34 个模块声明（lib.rs:1-36）" | 35 | 35 mod declarations in lib.rs:1-36 |
| 1726, 3089, 5596, 7032 | "约 271 个 Tauri 命令" | ~266 | `grep -c` = 266 |

These will self-resolve when the duplicate blocks are removed (a structural cleanup acknowledged as out-of-scope).

---

## 3. False Alarms Checked and Rejected

All of the following were verified against source and found correct or within acceptable convention:

| Notes reference | Claim | Verdict |
|---|---|---|
| `lib.rs:1825` (10 occurrences) | 1825 行 | ✅ `wc -l` = 1825 (trailing newline convention; repair log item #2) |
| `lib.rs:203` | `run()` function | ✅ Line 203 has `pub fn run()` |
| `lib.rs:1072` | `invoke_handler` | ✅ Line 1072 has `.invoke_handler(...)` |
| `lib.rs:1383` | `app.run()` | ✅ Line 1383 has `app.run(...)` |
| `lib.rs:38` | pub exports | ✅ Line 38 has `pub use app_config::{...}` |
| `lib.rs:40` | duplicate pub use | ✅ Line 40 has `pub use commands::open_provider_terminal;` (redundant with line 41) |
| `lib.rs:1513` | `cleanup_before_exit` | ✅ Line 1513 |
| `lib.rs:1558` | `restore_proxy_state_on_startup` | ✅ Line 1558 |
| `lib.rs:1601` | `initialize_common_config_snippets` | ✅ Line 1601 |
| `lib.rs:1685` | `is_chinese_locale` | ✅ Line 1685 |
| `error.rs:6` | AppError | ✅ Line 6 is `#[derive(Debug, Error)]`, line 7 is `pub enum AppError` |
| `error.rs:50` | Localized variant | ✅ Line 50 has `Localized {` |
| `error.rs:96` | `From<PoisonError>` | ✅ Line 96 |
| `error.rs:102` | `From<rusqlite::Error>` | ✅ Line 102 |
| `error.rs:114` | `impl Serialize` | ✅ Line 114 |
| `settings.rs:211` | `AppSettings` struct | ✅ Line 211 |
| `settings.rs:519` | `SETTINGS_STORE` | ✅ Line 519 |
| `settings.rs:521` | `settings_store()` | ✅ Line 521 |
| `settings.rs:574` | `mutate_settings` | ✅ Line 574 |
| `provider.rs:10` | `Provider` struct | ✅ Line 10 |
| `provider.rs:114` | `ProviderManager` | ✅ Line 114 |
| `provider.rs:121` | `UsageScript` | ✅ Line 121 |
| `store.rs:6` | `AppState` | ✅ Line 6 |
| `database/mod.rs:52` | `SCHEMA_VERSION = 10` | ✅ Line 52 |
| `database/mod.rs:61` | `lock_conn!` macro | ✅ Line 61 |
| `database/mod.rs:76` | `Database` struct | ✅ Line 76 |
| `database/mod.rs:95` | `init()` | ✅ Line 95 |
| `proxy/forwarder.rs:89` | `RequestForwarder` | ✅ Line 89 |
| `proxy/server.rs:34` | `ProxyState` | ✅ Line 34 |
| `proxy/server.rs:54` | `ProxyServer` | ✅ Line 54 |
| `switch_lock.rs:14` | `SwitchLockManager` | ✅ Line 14 |
| `switch_lock.rs:26` | `lock_for_app` | ✅ Line 26 |
| `services/proxy.rs:55` | `ProxyService` | ✅ Line 55 |
| `services/proxy.rs:64` | `HotSwitchOutcome` | ✅ Line 64 |
| `services/provider/mod.rs:46` | `ProviderService` | ✅ Line 46 |
| `services/provider/mod.rs:51` | `SwitchResult` | ✅ Line 51 |
| `services/provider/mod.rs:2250` | `validate_provider_settings` | ✅ Line 2250 |
| `config.rs:90` | `get_app_config_dir()` | ✅ Line 90 |
| `config.rs:37` | `get_claude_config_dir()` | ✅ Line 37 |
| `config.rs:74` | `get_claude_settings_path()` | ✅ Line 74 |
| `config.rs:153` | `read_json_file` | ✅ Line 153 |
| `config.rs:181` | `write_json_file` | ✅ Line 181 |
| `config.rs:196` | `write_text_file` | ✅ Line 196 |
| `config.rs:204` | `atomic_write` | ✅ Line 204 |
| `App.tsx:94` | View type | ✅ Line 94 |
| `App.tsx:119` | `STORAGE_KEY` | ✅ Line 119 |
| `App.tsx:130` | `getInitialApp()` | ✅ Line 130 |
| `useProxyStatus.ts:28` | 2s polling | ✅ `refetchInterval: ... 2000` |
| `providers.ts:49` | `providersApi` | ✅ Line 49 |
| `providers.ts:58-64` | `add()` signature | ✅ Matches source |
| `providers.ts:66-76` | `update()` signature | ✅ Matches source |
| `providers.ts:78-80` | `delete()` method | ✅ Method is `delete` (not `remove`), matches source |
| `providers.ts:90-92` | `switch()` signature | ✅ Matches source |
| Hook line counts (505, 385, 245, 373, 119) | useSettings, useProviderActions, useProxyStatus, useDirectorySettings, useDragSort | ✅ All match `wc -l` |
| Query line counts (155, 356, 243, 288, 319, 63) | queries, mutations, proxy, failover, usage, subscription | ✅ All match `wc -l` |
| `commands/mod.rs` 31 submodules | 31 mod declarations | ✅ `grep -c` = 31 |
| `commands/mod.rs` 66 lines | File length | ✅ `wc -l` = 66 |
| Ch4 headings 4.1–4.6 | Sequential numbering | ✅ No duplicates (repair #37 fixed this) |
| `lib.rs:6.4` table (line 5194) | "35 个 `mod` 声明" | ✅ Correctly repaired |

---

## 4. Summary

**Primary content**: 7 must-fix issues remain (1 broken fence, 3 duplicate-line artifacts from incomplete repairs, 2 stale count references, 1 stale key name).

**Duplicate blocks**: 12 stale references across 4 duplicate sections, all acknowledged in repair log as out-of-scope pending structural deduplication.

**Repaired references**: All 60 repairs from the repair log were spot-checked; the repairs themselves are correct where applied. The issues above are locations the repair missed or introduced artifacts in.
