# Global Consistency Audit Findings

Audit of `docs/cc-switch-source-notes.md` (8241 lines).  
Source: repo at `~/01-workspace/cc-switch`, verified 2026-05-28.

---

## F01 — Duplicate heading: "### 4.3" appears twice with different content

**Location**: Lines 3877 and 3964

**Verdict**: wrong

**Severity**: medium

**Description**: The section heading "### 4.3" is used twice:
- Line 3877: `### 4.3 ProxyState 和 ProxyServer`
- Line 3964: `### 4.3 认证和路由`

These are two different sections with different content. The second should be "### 4.4" or similar.

**Source evidence**: `grep -n '### 4.3 ' docs/cc-switch-source-notes.md` returns lines 3877 and 3964.

**Fix**: Change line 3964 from `### 4.3 认证和路由` to `### 4.4 认证和路由`.

---

## F02 — `settings.rs` line count: notes say 877 in one place, 876 in others

**Location**: Line 600 vs lines 2869 and 5290

**Verdict**: stale

**Severity**: low

**Description**: The notes contain contradictory line counts:
- Line 600: `settings.rs — 设置管理（28.8KB，877 行）`
- Line 2869: `settings.rs（876 行）— 通用设置`
- Line 5290 (appendix table): `settings.rs | 28.8KB | 876`

Actual: `wc -l src-tauri/src/settings.rs` → 876 lines.

**Source evidence**: `wc -l src-tauri/src/settings.rs` → 876

**Fix**: Change line 600 from "877 行" to "876 行".

---

## F03 — `services/proxy.rs` size: notes claim 141.3KB, actual is 144.8KB

**Location**: Lines 5102, 5175, 5220, 5272, 5293

**Verdict**: stale

**Severity**: low

**Description**: Notes consistently claim 141.3KB for `services/proxy.rs`. Actual: `wc -c src-tauri/src/services/proxy.rs` → 144,756 bytes (144.8KB). The file has grown ~3.5KB since the notes were written.

**Source evidence**: `wc -c src-tauri/src/services/proxy.rs` → 144756

**Fix**: Update all occurrences from "141.3KB" to "144.8KB".

---

## F04 — `claude_desktop_config.rs` size: notes claim 61.4KB, actual is 62.9KB

**Location**: Lines 2536, 5110, 5182, 5315

**Verdict**: stale

**Severity**: low

**Description**: Notes claim 61.4KB for `claude_desktop_config.rs`. Actual: `wc -c src-tauri/src/claude_desktop_config.rs` → 62,939 bytes (62.9KB).

**Source evidence**: `wc -c src-tauri/src/claude_desktop_config.rs` → 62939

**Fix**: Update from "61.4KB" to "62.9KB".

---

## F05 — `ProxyState` struct field count: notes show 10 fields, actual is 10

**Location**: Multiple locations (e.g., lines 1254–1267)

**Verdict**: ok

**Severity**: low

**Description**: Notes show `ProxyState` with 10 fields (db, config, status, start_time, current_providers, provider_router, gemini_shadow, codex_chat_history, app_handle, failover_manager). Actual struct at `src-tauri/src/proxy/server.rs:34-51` has exactly 10 fields.

**Source evidence**: `src-tauri/src/proxy/server.rs:34-51` shows 10 fields.

**Fix**: No fix needed.

---

## F06 — `RequestForwarder` struct field count: notes show 16 fields, actual is 16

**Location**: Multiple locations (e.g., lines 3773–3791)

**Verdict**: ok

**Severity**: low

**Description**: Notes show `RequestForwarder` with 16 fields. Actual struct at `src-tauri/src/proxy/forwarder.rs:89-121` has exactly 16 fields (router, status, current_providers, gemini_shadow, codex_chat_history, failover_manager, app_handle, current_provider_id_at_start, session_id, session_client_provided, rectifier_config, optimizer_config, copilot_optimizer_config, non_streaming_timeout, streaming_first_byte_timeout, max_attempts).

**Source evidence**: `src-tauri/src/proxy/forwarder.rs:89-121` shows 16 fields.

**Fix**: No fix needed.

---

## F07 — `lib.rs` module count: notes claim 34, actual is 34

**Location**: Multiple locations

**Verdict**: ok

**Severity**: low

**Description**: Notes claim 34 module declarations in `lib.rs`. Actual: `grep -c 'mod \|pub mod ' src-tauri/src/lib.rs` → 34.

**Source evidence**: `grep -c 'mod \|pub mod ' src-tauri/src/lib.rs` → 34

**Fix**: No fix needed.

---

## F08 — Command count: notes claim 271, actual is 271

**Location**: Multiple locations

**Verdict**: ok

**Severity**: low

**Description**: Notes claim 271 commands registered via `invoke_handler`. Actual: `grep -c 'commands::' src-tauri/src/lib.rs` → 271.

**Source evidence**: `grep -c 'commands::' src-tauri/src/lib.rs` → 271

**Fix**: No fix needed.

---

## F09 — `commands/mod.rs` module count: notes claim 33, actual is 31

**Location**: Multiple locations (e.g., lines 681, 2982)

**Verdict**: wrong

**Severity**: medium

**Description**: Notes claim "33 个子模块声明". Actual file has 31 module declarations (lines 3–29 and 31–34).

**Source evidence**: `src-tauri/src/commands/mod.rs` shows 31 `mod` declarations.

**Fix**: Replace all occurrences of "33 个子模块声明" with "31 个子模块声明".

---

## F10 — `useProxyStatus` polling interval: Ch1 says 5s, actual is 2s

**Location**: Line 206

**Verdict**: wrong

**Severity**: medium

**Description**: Line 206 claims `useProxyStatus()` polls "每 5 秒". Actual code at `src/hooks/useProxyStatus.ts:28`: `refetchInterval: (query) => (query.state.data?.running ? 2000 : false)` — polls every 2 seconds when running.

**Source evidence**: `src/hooks/useProxyStatus.ts:28` shows `refetchInterval: (query) => (query.state.data?.running ? 2000 : false)`

**Fix**: Change line 206 from "每 5 秒" to "每 2 秒".

---

## F11 — DAO file sizes: bullet points list service-module sizes instead of DAO sizes

**Location**: Lines 649, 1611, 2950, 5446, 6882

**Verdict**: wrong

**Severity**: high

**Description**: The `database/dao/` table lists correct approximate sizes, but bullet points below claim wrong sizes:

| DAO file | Table says | Bullet says | Actual |
|----------|-----------|-------------|--------|
| `proxy.rs` | 33.9KB | **7.5KB** | 34.7KB |
| `settings.rs` | 11.9KB | **28.9KB** | 12.2KB |
| `mcp.rs` | 4.1KB | **19.6KB** | 4.2KB |
| `stream_check.rs` | 2.7KB | **10.9KB** | 2.8KB |

The bullet-point sizes appear to be from `services/` modules, not DAO files.

**Source evidence**: `wc -c src-tauri/src/database/dao/*.rs` returns actual sizes.

**Fix**: Delete the misleading bullet points. The table is sufficient.

---

## F12 — Massive verbatim duplication across the document

**Location**: Lines ~1100–8241

**Verdict**: wrong

**Severity**: high

**Description**: Starting from around line 1100, the same ~1100 lines of content are copy-pasted verbatim 6–7 times through to line 8241. Each copy includes the same code blocks, tables, and definitions.

**Source evidence**: Line-by-line comparison shows identical blocks at lines 1172–1318 ≈ 2134–2290 ≈ 3473–3618 ≈ 4013–4032 ≈ 5969–6065 ≈ 7405–7509.

**Fix**: Delete all duplicate copies. Keep only the first occurrence of each section.

---

## F13 — Terminology inconsistency: "供应商" vs "Provider" vs "provider"

**Location**: Throughout all chapters

**Verdict**: ambiguous

**Severity**: low

**Description**: Notes inconsistently use three terms for the same concept:
- "供应商" (Chinese)
- "Provider" (English, capitalized)
- "provider" (English, lowercase)

**Source evidence**: Lines 3888–3891 show mixed usage.

**Fix**: Standardize on one term per language context.

---

## Summary

| # | Severity | Verdict | Issue |
|---|----------|---------|-------|
| F01 | medium | wrong | Duplicate heading "### 4.3" at lines 3877 and 3964 |
| F02 | low | stale | `settings.rs` line count: 877 vs 876 |
| F03 | low | stale | `services/proxy.rs` size: 141.3KB vs actual 144.8KB |
| F04 | low | stale | `claude_desktop_config.rs` size: 61.4KB vs actual 62.9KB |
| F05 | low | ok | `ProxyState` field count correct (10 fields) |
| F06 | low | ok | `RequestForwarder` field count correct (16 fields) |
| F07 | low | ok | `lib.rs` module count correct (34) |
| F08 | low | ok | Command count correct (271) |
| F09 | medium | wrong | `commands/mod.rs` module count: 33 claimed, 31 actual |
| F10 | medium | wrong | `useProxyStatus` polling: 5s claimed, 2s actual |
| F11 | high | wrong | DAO bullet sizes are service-module sizes |
| F12 | high | wrong | Massive verbatim duplication (~7100 lines) |
| F13 | low | ambiguous | Inconsistent "供应商"/"Provider"/"provider" terminology |
