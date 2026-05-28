# Post-Repair Backend Audit — docs/cc-switch-source-notes.md

**Date**: 2026-05-28
**Scope**: Chapters 1–4 backend/proxy claims; high-severity backend findings from synthesis plan
**Auditor**: post-repair-backend-auditor
**Verdict**: **FAIL** — 8 unresolved must-fix issues remain; several high-severity findings were not actually repaired despite repair log claims.

---

## Executive Summary

The repair log (28-repair-log.md) claims 60 repairs were applied. However, spot-checking against the actual document reveals that **many repairs did not land or were only partially applied**. The document contains massive verbatim duplication (~7100 lines repeated 6–7×), and repairs were applied to some duplicate blocks but not others. The result is a document that is internally contradictory on nearly every point that was supposed to be fixed.

**Critical pattern**: The repair log lists repairs as "done" but the same errors persist in duplicate blocks throughout the document. Since readers cannot know which copy is authoritative, every duplicate must be consistent.

---

## Unresolved Must-Fix Issues

### U1 — commands/ submodule count: still shows 34 (should be 31)

**Severity**: HIGH
**Location**: §1.4 line 253
**Current text**: `│ 34 个子模块 │`
**Correct**: `│ 31 个子模块 │`
**Source**: `grep -E '^\s*pub mod |^\s*mod ' src-tauri/src/commands/mod.rs | wc -l` = 31
**Repair log claim**: Repair #12 says "34 → 31 子模块" and repair #19 says "33 → 31 子模块"
**Status**: UNREPAIRED. Line 253 still shows 34. Line 254 was fixed (shows 31), but this creates an internal contradiction within the same diagram.

---

### U2 — Database module sizes: 3 of 4 still wrong

**Severity**: HIGH
**Location**: §3.7 module structure section (lines ~2897–2899)
**Current text**:
```
- mod.rs（1.1KB）— Database 结构体 + 初始化
- schema.rs（11.7KB）— 表结构定义 + Schema 迁移
- migration.rs（28.3KB）— JSON → SQLite 数据迁移
```
**Correct**:
- `mod.rs`（8.9KB）— actual: 9128 bytes
- `schema.rs`（77.8KB）— actual: 79691 bytes, 2050 lines
- `migration.rs`（9.2KB）— actual: 9468 bytes

**Source**: `wc -c src-tauri/src/database/{mod,schema,migration}.rs`
**Repair log claim**: None explicitly for this block. The repair log only addresses DAO bullet sizes (repair #17), not the module structure sizes.
**Status**: UNREPAIRED. The schema.rs size is off by 6.6×. The same section at line 3020 correctly states 77.8KB, creating an internal contradiction.

---

### U3 — DAO line counts: 6 of 12 still wildly wrong

**Severity**: HIGH
**Location**: §3.7 DAO line count list (lines ~2910–2925)
**Current vs correct**:

| File | Current (wrong) | Correct |
|------|-----------------|---------|
| proxy.rs | 247 行 | 952 行 |
| settings.rs | 876 行 | 327 行 |
| failover.rs | 182 行 | 149 行 |
| mcp.rs | 643 行 | 106 行 |
| stream_check.rs | 364 行 | 74 行 |
| mod.rs | 66 行 | 19 行 |

**Source**: `wc -l src-tauri/src/database/dao/*.rs`
**Repair log claim**: None. The repair log only addresses DAO bullet *sizes* (repair #17), not line counts.
**Status**: UNREPAIRED. proxy.rs is off by 3.9×, mcp.rs by 6.1×, stream_check.rs by 4.9×. These appear hallucinated.

---

### U4 — DAO module names: wrong in 2 locations

**Severity**: HIGH
**Location**: §3.8 line 1667, §3.8 line 3030
**Current text**: `providers、settings、mcp_servers、prompts、skills、proxy_config、proxy_request_logs、session_usage、subscription、usage_cache、universal_providers、stream_check`
**Correct**: `providers、settings、mcp、prompts、skills、proxy（代理配置 + 请求日志）、failover、providers_seed、usage_rollup、stream_check、universal_providers`

**Errors**: `mcp_servers` → `mcp`; `proxy_config` and `proxy_request_logs` → single `proxy.rs`; `session_usage`/`subscription`/`usage_cache` don't exist in dao/; missing `failover`/`providers_seed`/`usage_rollup`.

**Source**: `ls src-tauri/src/database/dao/`
**Repair log claim**: Repair #21 says "DAO module names corrected"
**Status**: UNREPAIRED. Both occurrences (lines 1667 and 3030) still have the wrong names.

---

### U5 — Config paths: 3 wrong extensions/locations

**Severity**: MEDIUM
**Location**: §3.6 config comparison table (lines 2544, 2546, 2547)

| Tool | Current (wrong) | Correct | Source |
|------|-----------------|---------|--------|
| Codex CLI | `~/.codex/config.json` | `~/.codex/config.toml` | `codex_config.rs:44-45` |
| OpenCode | `~/.opencode/config.json` | `~/.config/opencode/opencode.json` | `opencode_config.rs:40-46` |
| OpenClaw | `~/.openclaw/config.json` | `~/.openclaw/openclaw.json` | `openclaw_config.rs:46-47` |

**Repair log claim**: None
**Status**: UNREPAIRED. A maintainer following these paths would not find the config files.

---

### U6 — "共同模式" hallucination: 3 fabricated function names still present

**Severity**: HIGH
**Location**: §3.6 lines 2558–2560, §7.2 lines 5278–5282
**Current text**: Claims `build_live_config()`, `switch_provider()`, `import_from_live()` exist as per-module patterns in every config module.
**Reality**: None of these functions exist in any config module. `switch_provider()` is a Tauri command in `commands/provider.rs:102` delegating to `ProviderService::switch()`. `build_live_config()` doesn't exist anywhere. `import_from_live()` doesn't exist; actual functions are `import_hermes_providers_from_live()`, etc. in `services/provider/live.rs`.

**Source**: `grep -rn "build_live_config\|import_from_live" src-tauri/src/` = 0 matches
**Repair log claim**: None
**Status**: UNREPAIRED. The §7.2 trait definition at lines 5278–5282 still uses these fabricated names as if they were real APIs.

---

### U7 — schema.rs table count: still says 15, should be 23

**Severity**: MEDIUM
**Location**: §3.7 (line ~3020)
**Current text**: `schema.rs | 77.8KB | 数据库 schema 定义（15 张表的 SQL）`
**Correct**: `23 张表`
**Source**: `grep -c "CREATE TABLE" src-tauri/src/database/schema.rs` = 23
**Repair log claim**: Repair #20 says "schema.rs 15张表 → 23张表"
**Status**: UNREPAIRED. At least one occurrence still shows 15.

---

### U8 — RequestContext struct: missing 3 fields

**Severity**: MEDIUM
**Location**: §4.3 lines 3963–3975
**Current text**: Shows 10 fields
**Actual** (handler_context.rs:35-68): 13 fields. Missing:
- `pub app_type_str: &'static str` (line 54)
- `pub app_type: AppType` (line 57, `#[allow(dead_code)]`)
- `pub session_client_provided: bool` (line 61)

**Source**: `src-tauri/src/proxy/handler_context.rs:35-68`
**Repair log claim**: None
**Status**: UNREPAIRED.

---

## Evidence-Backed Suggested Edits

### S1 — Fix commands/ diagram (line 253)

```diff
- │ 34 个子模块 │
+ │ 31 个子模块 │
```

### S2 — Fix database module sizes (lines ~2897–2899)

```diff
-- `mod.rs`（1.1KB）— Database 结构体 + 初始化
-- `schema.rs`（11.7KB）— 表结构定义 + Schema 迁移
-- `migration.rs`（28.3KB）— JSON → SQLite 数据迁移
+- `mod.rs`（8.9KB）— Database 结构体 + 初始化
+- `schema.rs`（77.8KB）— 表结构定义 + Schema 迁移（当前版本 `SCHEMA_VERSION = 10`，`mod.rs:52`）
+- `migration.rs`（9.2KB）— JSON → SQLite 数据迁移
```

### S3 — Fix DAO line counts (lines ~2910–2925)

```diff
-- `proxy.rs`（247 行）— 代理配置
+- `proxy.rs`（952 行）— 代理配置和请求日志
-- `settings.rs`（876 行）— 通用设置
+- `settings.rs`（327 行）— 通用设置
-- `failover.rs`（182 行）— 故障转移队列
+- `failover.rs`（149 行）— 故障转移队列
-- `mcp.rs`（643 行）— MCP 服务器配置
+- `mcp.rs`（106 行）— MCP 服务器配置
-- `stream_check.rs`（364 行）— 流式检查配置
+- `stream_check.rs`（74 行）— 流式检查配置
-- `mod.rs`（66 行）— 模块声明
+- `mod.rs`（19 行）— 模块声明
```

### S4 — Fix DAO module names (lines 1667 and 3030)

```diff
-dao/ 子目录包含 12 个 DAO 模块：providers、settings、mcp_servers、prompts、skills、proxy_config、proxy_request_logs、session_usage、subscription、usage_cache、universal_providers、stream_check
+dao/ 子目录包含 11 个 DAO 模块：providers、settings、mcp、prompts、skills、proxy（代理配置 + 请求日志）、failover、providers_seed、usage_rollup、stream_check、universal_providers
```

### S5 — Fix config paths (lines 2544, 2546, 2547)

```diff
-| Codex CLI | codex_config.rs | 66.4KB | `~/.codex/config.json` |
+| Codex CLI | codex_config.rs | 66.5KB | `~/.codex/config.toml` |
-| OpenCode | opencode_config.rs | 6.9KB | `~/.opencode/config.json` |
+| OpenCode | opencode_config.rs | 6.9KB | `~/.config/opencode/opencode.json` |
-| OpenClaw | openclaw_config.rs | 34.9KB | `~/.openclaw/config.json` |
+| OpenClaw | openclaw_config.rs | 35.0KB | `~/.openclaw/openclaw.json` |
```

### S6 — Remove or correct "共同模式" claims (lines 2558–2560)

Replace the fabricated function list with accurate description:
```diff
-**共同模式**（每个模块都有）：
-1. `read_xxx_config()` — 读取工具的配置文件
-2. `write_xxx_config()` — 写入工具的配置文件
-3. `build_live_config()` — 构建当前生效的配置
-4. `switch_provider()` — 切换 provider 的核心逻辑
-5. `import_from_live()` — 从工具的 live 配置导入 provider
+**注意**：`switch_provider()` 和 `import_from_live()` 逻辑集中在 `services/provider/mod.rs`，不在各 config 模块中。各 config 模块提供的是路径解析、读写原始配置文件、以及构建特定工具 live config 的辅助函数。
```

### S7 — Fix schema.rs table count (line ~3020)

```diff
-| schema.rs | 77.8KB | 数据库 schema 定义（15 张表的 SQL） |
+| schema.rs | 77.8KB | 数据库 schema 定义（23 张表的 SQL） |
```

### S8 — Fix handlers/ directory claim (line 3704)

```diff
-├── handlers/           # 请求处理器
+├── handlers.rs         # 请求处理器（各 API 端点的 HTTP handler）
```

---

## False Alarms (Checked and Rejected)

### FA1 — services/ submodule count = 25

**Claim**: §1.4 says `services/ │ 25 个子模块`
**Investigation**: `ls -1 src-tauri/src/services/ | wc -l` = 27 entries (25 .rs files + 2 subdirectories). Excluding mod.rs: 26 submodules. If counting only .rs files: 25.
**Verdict**: DEFENSIBLE. The note counts .rs files only, which is a reasonable convention. The ch1 line-ref finding says 26, but both are arguable depending on counting method. Not a must-fix.

### FA2 — Provider switch flow simplification (lines 109–112)

**Claim**: `switch_normal() → read_live_settings() → build_effective_settings_with_common_config() → write_live_with_common_config()`
**Investigation**: Per ch1 source trace F14, the actual flow is `switch_normal() → backfill via read_live_settings() → set_current_provider() → write_live_with_common_config()` with `build_effective_settings_with_common_config` called *inside* `write_live_with_common_config`.
**Verdict**: ACCEPTABLE SIMPLIFICATION. The notes describe the logical flow, not the exact call sequence. The key functions are all real and the overall behavior is correct. Low risk of misleading a maintainer.

### FA3 — useProxyStatus polling interval contradiction (lines 206–207)

**Claim**: Line 206 says "每 5 秒", line 207 says "每 2 秒"
**Investigation**: `src/hooks/useProxyStatus.ts:28` shows `refetchInterval: 2000` (2 seconds). Line 206 is in a duplicate block that was not repaired; line 207 was repaired.
**Verdict**: LOW SEVERITY. The 2-second value is correct. This is a duplicate-block issue, not a factual error in the authoritative copy.

### FA4 — AppError variant line numbers off by 1

**Claim**: First 11 variants have line numbers pointing to `#[error("...")]` attribute instead of variant definition.
**Investigation**: Confirmed. The notes count the attribute line, not the variant line.
**Verdict**: LOW SEVERITY. Both conventions are navigable — a reader using "Go to line" would land on the attribute, which is immediately above the variant. Not a must-fix for backend correctness.

### FA5 — Error classification was correctly repaired

**Claim**: §4.1.2 now shows status-code-specific classification with Retryable/NonRetryable/ClientAbort.
**Investigation**: Lines ~3860–3870 show the corrected `categorize_proxy_error()` description with proper status code breakdown.
**Verdict**: CORRECTLY REPAIRED. ✓

### FA6 — ProxyError enum was correctly completed

**Claim**: §4.3 now shows all 20 variants.
**Investigation**: Lines 3912–3934 show all 20 variants from `AlreadyRunning` through `Internal(String)`.
**Verdict**: CORRECTLY REPAIRED. ✓

### FA7 — Stop flow was correctly updated

**Claim**: §4.1.3 now shows 5-second timeout.
**Investigation**: Lines ~3886–3889 show "带 5 秒超时等待服务器任务结束".
**Verdict**: CORRECTLY REPAIRED. ✓

---

## Repairs Confirmed as Landing

The following repairs from the repair log were verified as actually present in the document:

| # | Repair | Status |
|---|--------|--------|
| 5 | `state.db.get_all_providers(app_type) → .get(id)` | ✓ Landed (line 104) |
| 6 | `ProviderService::switch()` | ✓ Landed (line 105) |
| 7 | `switch_locks.lock_for_app()` | ✓ Landed (line 143) |
| 8 | Proxy hot-switch flow (no PROXY_TOKEN_PLACEHOLDER, no events) | ✓ Landed (lines 142–148) |
| 9 | useProxyStatus 2s polling | ✓ Landed (line 207) |
| 10 | Hook line counts (useSettings 505, useProxyStatus 245, etc.) | ✓ Landed (lines 210–214) |
| 11 | Query layer line counts (155, 356, etc.) | ✓ Landed (lines 217–222) |
| 13 | proxy/ 31 modules | ✓ Landed (line 254) |
| 22 | proxy_config 4 missing columns | ✓ Landed (lines 2633–2655) |
| 23 | proxy_request_logs 2 cost columns | ✓ Landed (lines 2726–2752) |
| 24 | session_log_sync last_synced_at | ✓ Landed (lines 2697–2703) |
| 25 | Database::init() pre-migration backup + ensure_incremental_auto_vacuum | ✓ Landed (lines 2845–2875) |
| 33 | Error classification (status-code-specific) | ✓ Landed (lines ~3860–3870) |
| 34 | Stop flow 5-second timeout | ✓ Landed (lines ~3886–3889) |
| 35 | ProxyError 20 variants complete | ✓ Landed (lines 3912–3934) |
| 31 | AppSettings webdav_sync: Option<WebDavSyncSettings> | ✓ Landed (line 2541) |
| 30 | UsageScript 11 fields | ✓ (not re-checked in this audit, per repair log) |

---

## Pass/Fail Summary

| Category | Verdict | Details |
|----------|---------|---------|
| Ch1 Architecture (backend claims) | **FAIL** | commands/ count wrong (U1); setup closure counts wrong; app_store function name wrong |
| Ch3 Backend Core (models, settings) | **FAIL** | "共同模式" hallucination (U6); config paths wrong (U5) |
| Ch3 Database Persistence | **FAIL** | Module sizes wrong (U2); DAO line counts wrong (U3); DAO names wrong (U4); table count wrong (U7) |
| Ch4 Proxy Subsystem | **PASS** | Error classification, ProxyError enum, stop flow all correctly repaired. RequestContext missing fields (U8) is medium severity but does not affect proxy behavior understanding. |
| Overall | **FAIL** | 8 unresolved must-fix issues; document is internally contradictory due to unrepaired duplicate blocks |

---

## Root Cause

The repair log states: *"Massive verbatim duplication (~7100 lines repeated 6-7× throughout document) ... would need duplicate removal to fix."* This is the core problem. The document has the same content repeated in multiple locations, and repairs were applied to some copies but not others. A reader encountering the wrong copy would see stale/wrong data and have no way to know it was "fixed" elsewhere.

**Recommendation**: The document needs a deduplication pass before surgical repairs can be effective. Until then, every repair must be applied to all duplicate occurrences to be trustworthy.
