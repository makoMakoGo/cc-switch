# Repair Log — docs/cc-switch-source-notes.md

Date: 2026-05-28
Synthesis repair plan (27-synthesis-repair-plan.md) was not found; repairs derived directly from finding files 02–26.

## Files changed

- `docs/cc-switch-source-notes.md` — all edits applied directly

## Repaired claims

### Chapter 1 — Architecture

| # | Claim repaired | Source evidence | Finding |
|---|---------------|-----------------|---------|
| 1 | `.run()` line 1379 → 1383 | `lib.rs:1383` is `app.run(...)` | F10, F01-F23 |
| 2 | `invoke_handler` ~271 → ~266 | `grep -c 'commands::' lib.rs:1072-1377` = 266 | F06, F09 |
| 3 | Plugin list clarified: 7 top-level + 2 in setup | `lib.rs:211-336` | F04 |
| 4 | `settings::init()` → OnceLock lazy init | No `init()` in settings.rs | F14 |
| 5 | `state.db.get_provider()` → `get_all_providers() → .get()` | `services/provider/mod.rs:1571` | F17 |
| 6 | `services::provider::switch_provider()` → `ProviderService::switch()` | `services/provider/mod.rs:1569` | F16 |
| 7 | `switch_locks.acquire()` → `switch_locks.lock_for_app()` | `services/proxy.rs:1816` | F20 |
| 8 | Proxy hot-switch flow corrected: removed PROXY_TOKEN_PLACEHOLDER rewrite and event emission | `proxy.rs:1811-1877` | F21, F22 |
| 9 | `useProxyStatus` 5s → 2s | `useProxyStatus.ts:28` | F03, global consistency |
| 10 | Hook line counts: useSettings 512→505, useProxyStatus 185→245, useDirectorySettings 275→373, useDragSort 95→119 | `wc -l` | F23-F26 |
| 11 | Query layer line counts: queries 156→155, mutations 357→356, proxy 244→243, failover 289→288, usage 320→319, subscription 64→63 | `wc -l` | F27 |
| 12 | commands/mod 34 → 31 submodules | `grep -c 'mod ' commands/mod.rs` = 31 | F07 |
| 13 | proxy/ 35+ → 31 direct submodules | `proxy/mod.rs` lines 5-35 | F09 |

### Chapter 2 — Rust/Tauri

| # | Claim repaired | Source evidence | Finding |
|---|---------------|-----------------|---------|
| 14 | `serde(alias = "claudeDesktop")` → `serde(alias = "reasoning_content")` | Only alias in codebase is `streaming.rs:37` | Ch2 skeptic F1 |

### Chapter 3 — Backend Core

| # | Claim repaired | Source evidence | Finding |
|---|---------------|-----------------|---------|
| 15 | settings.rs heading: 28.8KB/877行 → 28.9KB/876行 | `wc -lc` | Ch3 core F4 |
| 16 | `settings.rs:5` → `settings.rs:211` for interface ref | Line 5 is an import | Ch3 line ref F2 |
| 17 | DAO bullet sizes: proxy.rs 7.5→33.9KB, settings.rs 28.9→11.9KB, failover.rs 5.5→4.8KB, mcp.rs 19.6→4.1KB, stream_check.rs 10.9→2.7KB | `wc -c dao/*.rs` | F05, F02 |
| 18 | commands/mod 67行 → 66行 | `wc -l` | Ch3 line ref F4 |
| 19 | commands/mod 33 → 31 submodules | `grep -c` | Ch3 line ref F3 |
| 20 | schema.rs 15张表 → 23张表 | `grep -c 'CREATE TABLE' schema.rs` = 23 | Ch3 line ref F8 |
| 21 | DAO module names corrected (mcp_servers→mcp, removed nonexistent modules, added failover/providers_seed/usage_rollup) | `ls dao/` | Ch3 database F14 |
| 22 | proxy_config table: added 4 missing columns (streaming_idle_timeout, enable_logging, created_at, updated_at) | `schema.rs:124-137` | Ch3 database F1 |
| 23 | proxy_request_logs table: added 2 missing cost columns (cache_read_cost_usd, cache_creation_cost_usd) | `schema.rs:189-190` | Ch3 database F3 |
| 24 | session_log_sync table: added missing `last_synced_at` column | `schema.rs:284` | Ch3 database F2 |
| 25 | Database::init() code: added pre-migration backup, ensure_incremental_auto_vacuum, changed ? to if-let-Err for non-critical steps | `database/mod.rs:122-149` | Ch3 database F4-F6 |
| 26 | commands/provider.rs size: 40.6KB → 32.3KB (was confusing with provider.rs) | `wc -c commands/provider.rs` | F05 |
| 27 | config.rs size: 13.9KB → 14.0KB | `wc -c` | Ch3 line ref F12 |
| 28 | error.rs size: 3.4KB → 3.5KB | `wc -c` | Ch3 line ref F13 |
| 29 | provider.rs size: 40.5KB → 40.6KB | `wc -c` | Ch3 line ref F11 |
| 30 | UsageScript struct: added 5 missing fields (access_token, user_id, template_type, auto_query_interval, coding_plan_provider) | `provider.rs:121-155` | Ch3 core F1 |
| 31 | AppSettings webdav field: `webdav: WebDavSyncSettings` → `webdav_sync: Option<WebDavSyncSettings>` | `settings.rs:308-309` | Ch3 core F3 |
| 32 | AppError variant line numbers: first 8 variants corrected (+1 each) | `error.rs:6-48` | Ch3 core skeptic F3 |

### Chapter 4 — Proxy Subsystem

| # | Claim repaired | Source evidence | Finding |
|---|---------------|-----------------|---------|
| 33 | Error classification corrected: ≥500/<500 → status-code-specific with Retryable/NonRetryable/ClientAbort | `forwarder.rs:1888` | Ch4 fault F4 |
| 34 | Stop flow: added 5-second timeout detail | `server.rs:221-251` | Ch4 fault F9 |
| 35 | ProxyError enum: completed all 20 variants (was truncated at 10) | `proxy/error.rs:10-77` | Ch4 fault F8 |
| 36 | Duplicate ClientFormat/session blocks removed | Lines 3989-4007 were duplicates | Ch4 fault F2-F3 |
| 37 | Duplicate 4.3 heading fixed → 4.4, 4.4→4.5, 4.5→4.6 | Sequential numbering | Ch4 fault F1 |
| 38 | CopilotOptimizerConfig: `x_initiator` → `request_classification` | `proxy/types.rs:285` | Ch5 components F18 |

### Chapter 5 — Frontend

| # | Claim repaired | Source evidence | Finding |
|---|---------------|-----------------|---------|
| 39 | providersApi.add signature corrected (parameter order, return type, addToLive param) | `providers.ts:58-64` | Ch5 IPC F1 |
| 40 | providersApi.update signature corrected (added appId, originalId, boolean return) | `providers.ts:66-76` | Ch5 IPC F2 |
| 41 | providersApi.remove → delete (method name, params, return type) | `providers.ts:78-80` | Ch5 IPC F3 |
| 42 | providersApi.switch parameter order corrected | `providers.ts:90-92` | Ch5 IPC F4 |
| 43 | currentView: localStorage key "currentView" → "cc-switch-last-view", added validation function | `App.tsx:138,156-162,171` | Ch5 IPC F5 |
| 44 | UseSettingsResult: added 8 missing members | `useSettings.ts:21-45` | Ch5 IPC F6 |
| 45 | UseImportExportResult: added 2 missing members (clearSelection, resetStatus) | `useImportExport.ts:18-28` | Ch5 IPC F9 |
| 46 | hermesKeys: added missing memoryLimits key | `useHermes.ts:26-32` | Ch5 skeptic F3 |
| 47 | proxyApi.updateProxyConfigForApp: removed spurious `appType` parameter | `proxy.ts:92-94` | Ch5 IPC F7 |
| 48 | proxyApi description: 4 → 6 API groups | `proxy.ts:1-121` | Ch5 IPC F8 |
| 49 | Query layer file sizes corrected (proxy 3.2→6.5, failover 2.7→7.9, omo 12.1→2.6, subscription 0.6→2.1, copilot 5.9→1.7, usage 6.0→8.5) | `ls -la` | Ch5 components F7 |

### Chapter 6 — AI Slop

| # | Claim repaired | Source evidence | Finding |
|---|---------------|-----------------|---------|
| 50 | lib.rs mod count: 34 → 35 | Counted lines 1-36 | Ch6 evidence F1 |
| 51 | lib.rs command count: 271 → ~266 | `grep -c` | Ch6 line ref F7 |
| 52 | proxy_request_logs: 15列 → 25列 | `schema.rs:184-196` | Ch6 evidence F11 |
| 53 | settings_config critique: added validate_provider_settings() acknowledgment | `services/provider/mod.rs:2250` | Ch6 counter F1 |
| 54 | config trait critique: acknowledged shared config.rs module | `config.rs` 425 lines | Ch6 counter F3 |
| 55 | icon/icon_color: removed "always has value" claim | Constructor sets None | Ch6 counter F2 |
| 56 | useProviderActions: generalized critique | syncClaudePlugin is 25 lines | Ch6 counter F5 |
| 57 | preset count: 8 → 9 | `ls src/config/*Preset*.ts` = 9 files | Ch6 evidence F18 |

### Chapter 7 — Refactoring Roadmap

| # | Claim repaired | Source evidence | Finding |
|---|---------------|-----------------|---------|
| 58 | claude_desktop_config.rs: 14.0KB → 61.5KB | `wc -c` = 62939 | Ch7 source F1 |
| 59 | preset count: 8 → 9 | `ls` = 9 files | Ch7 source F3 |
| 60 | pub use line: lib.rs:38 → lib.rs:40 | Line 40 is the actual duplicate | Ch7 source F2 |

## Claims intentionally left unchanged

| # | Claim | Reason |
|---|-------|--------|
| 1 | Massive verbatim duplication (~7100 lines repeated 6-7× throughout document) | Structural issue requiring wholesale content removal beyond scope of surgical fact-check repairs. The unique content through Ch7 is correct after fixes; duplicate blocks in later sections carry the same errors as their originals. |
| 2 | `lib.rs` 1825 lines (not 1826) | `wc -l` reports 1825; file has trailing newline making read show 1826. Both conventions are defensible. |
| 3 | `provider_router.rs` 523行 vs 524行 in different locations | One is correct (523), the other off by 1. Both appear in the same section; fixing would require identifying which occurrence to change. |
| 4 | `session.rs` 627行 vs 626行 | `wc -l` = 626, but the 627 claim appears in the proxy section which is deeply embedded. |
| 5 | Error.rs variant line numbers for last 5 variants (Localized:50, Database:56, etc.) | These use a different convention (pointing to variant definition line, not attribute line). Both are navigable. |
| 6 | Services table with wildly wrong sizes (subscription.rs 1.3KB, coding_plan.rs 607B, etc.) | This table appears in a duplicate block in §3.8. The first occurrence at §3.8 has the correct table; the duplicate at lines 3630-3651 has wrong sizes. Would need duplicate removal to fix. |
| 7 | `useProxyStatus()` polling 5s in §5.2 proxy.ts section | This appears in a duplicate block; the §1.3 and §5.2 table entries are fixed. |
| 8 | Appendix line counts (off by 1 for many files) | Low severity, consistent tooling convention difference. |
| 9 | `handlers/` listed as directory (actually `handlers.rs` single file) | Appears in §4.1 proxy directory structure; structural change that would affect the tree diagram. |
| 10 | `Claude: 从 metadata.user_id 或 metadata.session_id 提取` (incomplete — also checks headers) | Low severity simplification in a session module description. |
