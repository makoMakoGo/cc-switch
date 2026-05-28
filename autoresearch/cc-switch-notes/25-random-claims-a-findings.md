# Random Claims Audit A — Findings

Randomized broad audit sampling claims across all chapters (architecture, backend, proxy, frontend, quality, roadmap). Every claim below was independently verified against source code.

---

## Finding 1: commands/mod.rs submodule count is 31, not 33

**Note location:** Ch3 §3.5, line 681
> "33 个子模块声明（commands/mod.rs:3-34）"

**Verdict:** wrong

**Source evidence:** `src-tauri/src/commands/mod.rs` lines 3–34 contain 31 `mod` declarations:
```
3: auth, 4: balance, 5: codex_oauth, 6: coding_plan, 7: config, 8: copilot,
9: deeplink, 10: env, 11: failover, 12: global_proxy, 13: hermes, 14: import_export,
15: mcp, 16: misc, 17: model_fetch, 18: omo, 19: openclaw, 20: plugin, 21: prompt,
22: provider, 23: proxy, 24: session_manager, 25: settings, 26: skill (pub mod),
27: stream_check, 28: subscription, 29: sync_support, [30: blank], 31: lightweight,
32: usage, 33: webdav_sync, 34: workspace
```
Line 30 is blank. Total: 31 modules. The table at line 700 correctly says "32 个文件" (31 modules + mod.rs).

**Exact replacement:** `31 个子模块声明（commands/mod.rs:3-34）`

**Severity:** medium — wrong module count misleads anyone mapping the codebase structure

---

## Finding 2: DAO proxy.rs size wrong in summary (7.5KB vs 33.9KB)

**Note location:** Ch3 §3.5, line 649
> "`proxy.rs`（7.5KB）是最大的 DAO 文件，包含代理配置和请求日志操作"

**Verdict:** wrong

**Source evidence:** `wc -c src-tauri/src/database/dao/proxy.rs` → 34715 bytes (33.9KB). The table at line 637 correctly says "proxy.rs | 33.9KB". The summary text contradicts its own table.

**Exact replacement:** `` `proxy.rs`（33.9KB）是最大的 DAO 文件，包含代理配置和请求日志操作 ``

**Severity:** medium — 4.5× size error, and the "最大" claim is correct only with the right number

---

## Finding 3: DAO settings.rs size wrong in summary (28.9KB vs 11.9KB)

**Note location:** Ch3 §3.5, line 652
> "`settings.rs`（28.9KB）包含设置的读写操作"

**Verdict:** wrong

**Source evidence:** `wc -c src-tauri/src/database/dao/settings.rs` → 12235 bytes (11.9KB). The table at line 640 correctly says "settings.rs | 11.9KB". The summary text appears to confuse the DAO file with `src/settings.rs` (28.8KB/876 lines).

**Exact replacement:** `` `settings.rs`（11.9KB）包含设置的读写操作 ``

**Severity:** medium — 2.4× size error, confuses two different files

---

## Finding 4: DAO failover.rs size wrong in summary (5.5KB vs 4.8KB)

**Note location:** Ch3 §3.5, line 654
> "`failover.rs`（5.5KB）包含故障转移队列操作"

**Verdict:** wrong

**Source evidence:** `wc -c src-tauri/src/database/dao/failover.rs` → 4920 bytes (4.8KB). The table at line 642 correctly says "failover.rs | 4.8KB".

**Exact replacement:** `` `failover.rs`（4.8KB）包含故障转移队列操作 ``

**Severity:** low — small numerical error

---

## Finding 5: DAO mcp.rs size wrong in summary (19.6KB vs 4.1KB)

**Note location:** Ch3 §3.5, line 655
> "`mcp.rs`（19.6KB）包含 MCP 服务器的 CRUD 操作"

**Verdict:** wrong

**Source evidence:** `wc -c src-tauri/src/database/dao/mcp.rs` → 4231 bytes (4.1KB). The table at line 643 correctly says "mcp.rs | 4.1KB". The summary number 19.6KB is ~5× the actual size.

**Exact replacement:** `` `mcp.rs`（4.1KB）包含 MCP 服务器的 CRUD 操作 ``

**Severity:** medium — 4.8× size error

---

## Finding 6: DAO stream_check.rs size wrong in summary (10.9KB vs 2.7KB)

**Note location:** Ch3 §3.5, line 658
> "`stream_check.rs`（10.9KB）包含流式检查记录操作"

**Verdict:** wrong

**Source evidence:** `wc -c src-tauri/src/database/dao/stream_check.rs` → 2778 bytes (2.7KB). The table at line 646 correctly says "stream_check.rs | 2.7KB". The summary number 10.9KB is ~4× the actual size.

**Exact replacement:** `` `stream_check.rs`（2.7KB）包含流式检查记录操作 ``

**Severity:** medium — 4× size error

---

## Finding 7: commands/provider.rs size wrong in summary (40.6KB vs 32.3KB)

**Note location:** Ch3 §3.5, line 735
> "`provider.rs`（40.6KB）包含 Provider CRUD 和切换命令"

**Verdict:** wrong

**Source evidence:** `wc -c src-tauri/src/commands/provider.rs` → 33040 bytes (32.3KB). The table at line 703 correctly says "provider.rs | 32.3KB". The 40.6KB number matches `src/provider.rs` (41528 bytes), a different file.

**Exact replacement:** `` `provider.rs`（32.3KB）包含 Provider CRUD 和切换命令 ``

**Severity:** medium — confuses two different files with the same name

---

## Finding 8: claude_desktop_config.rs size wrong in refactoring section (14.0KB vs 61.5KB)

**Note location:** Ch7 §7.2, line 5229
> "`claude_desktop_config.rs`（14.0KB）→ `claude_desktop/` 目录"

**Verdict:** wrong

**Source evidence:** `wc -c src-tauri/src/claude_desktop_config.rs` → 62939 bytes (61.5KB). The appendix at line 5315 correctly says "claude_desktop_config.rs | 61.4KB | 1826". The 14.0KB number is off by 4.4×.

**Exact replacement:** `` `claude_desktop_config.rs`（61.5KB）→ `claude_desktop/` 目录 ``

**Severity:** medium — severely understates the file size, which undermines the refactoring rationale

---

## Finding 9: ProxyError variant count understated as "14+"

**Note location:** Ch4 §4.3, line 5394
> "14+ 个错误变体，覆盖代理服务器的所有错误场景"

**Verdict:** ambiguous

**Source evidence:** `src-tauri/src/proxy/error.rs` lines 10–77 define exactly 20 variants:
AlreadyRunning, NotRunning, BindFailed, StopTimeout, StopFailed, ForwardFailed, NoAvailableProvider, AllProvidersCircuitOpen, NoProvidersConfigured, ProviderUnhealthy, UpstreamError, MaxRetriesExceeded, DatabaseError, ConfigError, TransformError, InvalidRequest, Timeout, StreamIdleTimeout, AuthError, Internal.

The notes correctly state "20 个变体" at line 3878, contradicting the "14+" at line 5394.

**Exact replacement:** `20 个错误变体，覆盖代理服务器的所有错误场景`

**Severity:** low — "14+" is technically true but misleadingly imprecise; the correct count is stated elsewhere in the same notes

---

## Finding 10: settings.rs line count off by one (877 vs 876)

**Note location:** Ch3 §3.5, line 600
> "settings.rs — 设置管理（28.8KB，877 行）"

**Verdict:** wrong

**Source evidence:** `wc -l src-tauri/src/settings.rs` → 876 lines. `wc -c` → 29572 bytes (28.9KB). The appendix at line 5290 correctly says "settings.rs | 28.8KB | 876" (though 28.8KB vs 28.9KB is a minor rounding difference).

**Exact replacement:** `settings.rs — 设置管理（28.9KB，876 行）`

**Severity:** low — off by one line and minor rounding

---

## Summary

| # | Finding | Verdict | Severity |
|---|---------|---------|----------|
| 1 | commands/mod.rs submodule count: 33→31 | wrong | medium |
| 2 | DAO proxy.rs size: 7.5KB→33.9KB | wrong | medium |
| 3 | DAO settings.rs size: 28.9KB→11.9KB | wrong | medium |
| 4 | DAO failover.rs size: 5.5KB→4.8KB | wrong | low |
| 5 | DAO mcp.rs size: 19.6KB→4.1KB | wrong | medium |
| 6 | DAO stream_check.rs size: 10.9KB→2.7KB | wrong | medium |
| 7 | commands/provider.rs size: 40.6KB→32.3KB | wrong | medium |
| 8 | claude_desktop_config.rs size: 14.0KB→61.5KB | wrong | medium |
| 9 | ProxyError variant count: "14+"→20 | ambiguous | low |
| 10 | settings.rs line count: 877→876 | wrong | low |

**Pattern:** Findings 2–6 form a cluster — the summary text under the DAO table (lines 649–659) has 5 wrong file sizes while the table itself (lines 637–648) is correct. This suggests the summary was generated or written separately from the table and never cross-checked. Finding 7 follows the same pattern for the commands summary. Finding 8 is a standalone size error in the refactoring chapter.

**Verified OK claims (sample):** main.rs 22 lines ✓, lib.rs 1825 lines ✓, 34 modules ✓, 271 invoke_handler commands ✓, setup closure 284–1070 ✓, AppState at store.rs:6 ✓, Database at database/mod.rs:76 with Mutex<Connection> ✓, SETTINGS_STORE at settings.rs:519 ✓, mutate_settings at settings.rs:574 (private, param name `mutator`) ✓, ProxyConfig default port 15721 ✓, 9 plugins ✓, SCHEMA_VERSION=10 ✓, ProxyService at services/proxy.rs:55 ✓, SwitchLockManager at switch_lock.rs:14 ✓, forwarder.rs 3100 lines/122KB ✓, App.tsx 1604 lines ✓, hooks/ 25 files/3642 lines ✓, is_additive_mode() at app_config.rs:373 ✓.
