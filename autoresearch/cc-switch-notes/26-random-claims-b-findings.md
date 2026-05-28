# Random Claims Audit B — Findings

Auditor: global_random_claims_b
Date: 2026-05-28
Scope: All chapters, broad sample differing from auditor A

---

## Finding 1: DAO file size contradictions — table vs bullet points

**Location**: Ch3 §3.3 (lines 634–659)

**Claim (table, correct)**:
```
| proxy.rs | 33.9KB | 代理配置和请求日志 DAO |
| settings.rs | 11.9KB | 设置 DAO |
| failover.rs | 4.8KB | 故障转移 DAO |
| mcp.rs | 4.1KB | MCP 服务器 DAO |
| stream_check.rs | 2.7KB | 流式检查 DAO |
```

**Claim (bullet points, wrong)**:
```
- `proxy.rs`（7.5KB）是最大的 DAO 文件
- `settings.rs`（28.9KB）包含设置的读写操作
- `failover.rs`（5.5KB）包含故障转移队列操作
- `mcp.rs`（19.6KB）包含 MCP 服务器的 CRUD 操作
- `stream_check.rs`（10.9KB）包含流式检查记录操作
```

**Verdict**: wrong

**Source evidence**:
```
$ wc -c src-tauri/src/database/dao/*.rs
34715 proxy.rs        → 33.9KB
12235 settings.rs     → 11.9KB
 4920 failover.rs     → 4.8KB
 4231 mcp.rs          → 4.1KB
 2778 stream_check.rs → 2.7KB
```

The bullet points below the table use sizes from other directories (e.g., 28.9KB is `src-tauri/src/settings.rs`, 10.9KB is `commands/stream_check.rs`). The table itself is correct; the prose summary contradicts it.

**Severity**: high — a maintainer reading the bullets instead of the table would get wrong mental model of DAO module sizes.

**Fix**: Replace the five wrong bullet points with sizes from the table:
```
- `proxy.rs`（33.9KB）是最大的 DAO 文件，包含代理配置和请求日志操作
- `settings.rs`（11.9KB）包含设置的读写操作
- `failover.rs`（4.8KB）包含故障转移队列操作
- `mcp.rs`（4.1KB）包含 MCP 服务器的 CRUD 操作
- `stream_check.rs`（2.7KB）包含流式检查记录操作
```

---

## Finding 2: commands/mod.rs submodule count — 31 not 33

**Location**: Ch3 (lines 681, 5478)

**Claim**: `33 个子模块声明（commands/mod.rs:3-34）`

**Verdict**: wrong

**Source evidence**:
```bash
$ grep -c 'mod ' src-tauri/src/commands/mod.rs
31
```

Actual file `src-tauri/src/commands/mod.rs` has 31 `mod` declarations (lines 3–34, with a blank line at 30). The notes claim 33 in two separate locations.

**Severity**: medium — wrong module count misleads anyone auditing the codebase.

**Fix**: Replace `33 个子模块声明` with `31 个子模块声明`.

---

## Finding 3: Tauri command count — 249 not 271

**Location**: Ch1 §1.1 (lines 63, 86), Ch1 §1.1.1 (line 86), and multiple other locations

**Claim**: `约 271 个 Tauri 命令（1072-1377）`

**Verdict**: wrong

**Source evidence**:
```bash
$ grep -c '#\[tauri::command\]' src-tauri/src/commands/*.rs | awk -F: '{sum+=$2} END {print sum}'
249
```

The `.invoke_handler()` span (lib.rs:1072–1377) registers commands via `tauri::generate_handler![]`, but the actual `#[tauri::command]` annotations across all command files total 249, not 271.

**Severity**: medium — inflated command count misleads architecture assessment.

**Fix**: Replace `约 271 个` with `约 249 个` in all occurrences.

---

## Finding 4: useProxyStatus polling interval — 2s not 5s

**Location**: Ch1 §1.3 (line 206)

**Claim**: `useProxyStatus() — 轮询代理状态（每 5 秒）`

**Verdict**: wrong

**Source evidence** (`src/hooks/useProxyStatus.ts:28`):
```typescript
refetchInterval: (query) => (query.state.data?.running ? 2000 : false),
```

The actual polling interval is 2000ms (2 seconds) when the proxy is running, and disabled (`false`) when not running. Section 5.2 of the same notes correctly states "每 2 秒", but section 1.3 says "每 5 秒".

**Severity**: medium — incorrect polling interval could mislead performance analysis.

**Fix**: Replace `每 5 秒` with `每 2 秒` in section 1.3.

---

## Finding 5: settings.rs line count — 876 not 877

**Location**: Ch3 §3.5 (line 600)

**Claim**: `settings.rs — 设置管理（28.8KB，877 行）`

**Verdict**: stale

**Source evidence**:
```bash
$ wc -l src-tauri/src/settings.rs
876
```

The appendix table at line 5290 correctly states 876 lines. Section 3.5 says 877.

**Severity**: low — off by one line.

**Fix**: Replace `877 行` with `876 行` in section 3.5.

---

## Finding 6: error.rs line numbers — inconsistent convention for last 5 variants

**Location**: Ch3 §3.2 (lines 472–489)

**Claim**: Line numbers for AppError variants in the table.

**Verdict**: ambiguous

**Source evidence** (`src-tauri/src/error.rs:1-63:raw`):

For the first 11 variants, the notes point to the `#[error("...")]` attribute line:
- `Config(String)` | :8 → line 8 is `#[error("配置错误: {0}")]` ✓
- `InvalidInput(String)` | :10 → line 10 is `#[error("无效输入: {0}")]` ✓
- ... (consistent through `HttpStatus` at :47)

For the last 5 variants, the notes point to the variant definition line instead:
- `Localized { key, zh, en }` | :50 → line 49 is `#[error("{zh} ({en})")]`, line 50 is `Localized {`
- `Database(String)` | :56 → line 55 is `#[error("数据库错误: {0}")]`, line 56 is `Database(String),`
- `OmoConfigNotFound` | :58 → line 57 is `#[error("OMO 配置文件不存在")]`, line 58 is `OmoConfigNotFound,`
- `AllProvidersCircuitOpen` | :60 → line 59 is `#[error("所有供应商已熔断...")]`, line 60 is variant
- `NoProvidersConfigured` | :62 → line 61 is `#[error("未配置供应商")]`, line 62 is variant

**Severity**: low — inconsistent but both lines are adjacent; a reader can find the variant either way.

**Fix**: Standardize to point to the `#[error]` attribute line for all variants:
```
| `Localized { key, zh, en }` | :49 | 中英双语错误 |
| `Database(String)` | :55 | 数据库错误 |
| `OmoConfigNotFound` | :57 | OMO 配置不存在 |
| `AllProvidersCircuitOpen` | :59 | 所有供应商已熔断 |
| `NoProvidersConfigured` | :61 | 未配置供应商 |
```

---

## Finding 7: Hook line counts in §1.3 — multiple wrong values

**Location**: Ch1 §1.3 (lines 209–213)

**Claim**:
```
hooks/ 目录（25 个 hooks）：
  ├─ useSettings.ts (512 行)
  ├─ useProviderActions.ts (385 行)
  ├─ useProxyStatus.ts (185 行)
  ├─ useDirectorySettings.ts (275 行)
  └─ useDragSort.ts (95 行)
```

**Verdict**: wrong

**Source evidence**:
```bash
$ wc -l src/hooks/useSettings.ts src/hooks/useProviderActions.ts src/hooks/useProxyStatus.ts src/hooks/useDirectorySettings.ts src/hooks/useDragSort.ts
505 useSettings.ts
385 useProviderActions.ts
245 useProxyStatus.ts
373 useDirectorySettings.ts
119 useDragSort.ts
```

Section 5.2 of the same notes has the correct values (505, 385, 245, 373, 119). Section 1.3 has wrong values for 4 out of 5 hooks.

**Severity**: medium — stale or fabricated line counts in the architecture overview.

**Fix**: Update section 1.3 to match actual values:
```
  ├─ useSettings.ts (505 行)
  ├─ useProviderActions.ts (385 行)
  ├─ useProxyStatus.ts (245 行)
  ├─ useDirectorySettings.ts (373 行)
  └─ useDragSort.ts (119 行)
```

---

## Finding 8: Proxy module line counts — off by 1 for 4 files

**Location**: Appendix (lines 5346, 5396, 5411, 5370)

**Claim**:
```
error_mapper.rs — 118 行
proxy/providers/adapter.rs — 70 行
proxy/providers/mod.rs — 518 行
proxy/session.rs — 627 行
proxy/model_mapper.rs — 313 行
proxy/error.rs — 206 行
```

**Verdict**: stale

**Source evidence**:
```bash
$ wc -l src-tauri/src/proxy/error_mapper.rs src-tauri/src/proxy/providers/adapter.rs src-tauri/src/proxy/providers/mod.rs src-tauri/src/proxy/session.rs src-tauri/src/proxy/model_mapper.rs src-tauri/src/proxy/error.rs
118 error_mapper.rs
 69 providers/adapter.rs
517 providers/mod.rs
626 session.rs
312 model_mapper.rs
206 error.rs
```

Four files are off by +1 in the notes (adapter.rs 70→69, mod.rs 518→517, session.rs 627→626, model_mapper.rs 313→312). Two match exactly (error_mapper.rs 118, error.rs 206).

**Severity**: low — off by one, likely a line-counting convention difference.

**Fix**: Update to actual `wc -l` values:
```
proxy/providers/adapter.rs — 69 行
proxy/providers/mod.rs — 517 行
proxy/session.rs — 626 行
proxy/model_mapper.rs — 312 行
```

---

## Finding 9: error.rs file size — 3.5KB not 3.4KB

**Location**: Ch3 §3.2 (line 466), Appendix (line 5288)

**Claim**: `error.rs — 错误模型（3.4KB，146 行）`

**Verdict**: stale

**Source evidence**:
```bash
$ wc -c src-tauri/src/error.rs
3565
```

3565 bytes = 3.48KB (binary) ≈ 3.5KB. The notes say 3.4KB.

**Severity**: low — 0.1KB rounding difference.

**Fix**: Replace `3.4KB` with `3.5KB`.

---

## Finding 10: config.rs file size — 14.0KB not 13.9KB

**Location**: Ch3 §3.1 (line 441), Appendix (line 5289)

**Claim**: `config.rs — 路径解析和文件 I/O（13.9KB，424 行）`

**Verdict**: stale

**Source evidence**:
```bash
$ wc -c src-tauri/src/config.rs
14327
```

14327 bytes = 13.99KB (binary) ≈ 14.0KB. The notes say 13.9KB.

**Severity**: low — 0.1KB rounding difference.

**Fix**: Replace `13.9KB` with `14.0KB`.

---

## Verified OK Claims (spot-checked)

The following claims were independently verified as correct:

| Claim | Location | Evidence |
|-------|----------|----------|
| main.rs is 22 lines | §1.1 | `wc -l` = 22, content ends at line 22 |
| lib.rs is 1825 lines | §1.1 | `wc -l` = 1825 |
| lib.rs has 34 module declarations | §1.4 | Counted from lines 1-36 |
| AppState at store.rs:6 | §1.3 | Line 6 confirmed |
| run() at lib.rs:203 | §1.1 | Line 203 confirmed |
| .invoke_handler at lib.rs:1072 | §1.1 | Line 1072 confirmed |
| cleanup_before_exit at lib.rs:1513 | §1.1 | Line 1513 confirmed |
| stop_with_restore_keep_state at lib.rs:1531 | §1.1 | Line 1531 confirmed |
| 100ms I/O wait at lib.rs:1406 | §1.1 | Line 1406 confirmed |
| SCHEMA_VERSION = 10 at database/mod.rs:52 | §3.3 | Line 52 confirmed |
| lock_conn! macro at database/mod.rs:61 | §3.3 | Line 61 confirmed |
| Database struct at database/mod.rs:76 | §3.3 | Line 76 confirmed |
| SwitchLockManager at switch_lock.rs:14 | §1.3 | Line 14 confirmed |
| lock_for_app at switch_lock.rs:26 | §1.3 | Line 26 confirmed |
| ProxyService at services/proxy.rs:55 | §1.3 | Line 55 confirmed |
| PROXY_TOKEN_PLACEHOLDER at services/proxy.rs:22 | §4.1 | Line 22 confirmed, value = "PROXY_MANAGED" |
| PROXY_AUTH_PLACEHOLDER at forwarder.rs:35 | §4.1 | Line 35 confirmed, value = "PROXY_MANAGED" |
| AppType enum at app_config.rs:341 | §3.3 | Line 341 confirmed |
| is_additive_mode at app_config.rs:373 | §3.3 | Line 373 confirmed |
| View type at App.tsx:94 | §5.1 | Line 94 confirmed |
| App.tsx is 1604 lines | §5.1 | `wc -l` = 1604 |
| useProviderActions.ts is 385 lines | §5.2 | `wc -l` = 385 |
| mutate_settings parameter name is `mutator` | §1.3 | Line 574 confirmed |
| All DAO file sizes in the table | §3.3 | All 12 sizes match `wc -c` |
| All service file line counts | §6.1 | proxy.rs 3909, provider/mod.rs 2766, usage_stats.rs 3250, skill.rs 3127, stream_check.rs 2166 — all match |
| provider.rs is 1153 lines, 40.5KB | §3.4 | `wc -l` = 1153, `wc -c` = 41528 (40.6KB) |
| app_config.rs is 1183 lines, 41.0KB | §3.3 | `wc -l` = 1183, `wc -c` = 41996 (41.0KB) |
| database/schema.rs is 2050 lines | Appendix | `wc -l` = 2050 |
| database/backup.rs is 860 lines | Appendix | `wc -l` = 860 |
| database/migration.rs is 245 lines | Appendix | `wc -l` = 245 |
| proxy/forwarder.rs is 3100 lines | §4.1 | `wc -l` = 3100 |
| proxy/circuit_breaker.rs is 495 lines | §4.1 | `wc -l` = 495 |
| proxy/provider_router.rs is 523 lines | §4.1 | `wc -l` = 523 |
| proxy/server.rs is 388 lines | §4.1 | `wc -l` = 388 |
