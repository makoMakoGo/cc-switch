# 23 — Global File:Line Audit Findings

Scope: All chapters. Every backtick `file.rs:NNN` reference, file-size claim, and line-count claim sampled against source.

---

## Finding 1 — `.run()` line number wrong in startup chain

- **note location:** §1.1 startup chain diagram, `└─ .run() // lib.rs:1379`
- **verdict:** wrong
- **source evidence:** `src-tauri/src/lib.rs:1379` is `let app = builder`, line 1383 is `app.run(|app_handle, event| {`
- **severity:** high — misleading startup flow reference
- **replacement:** `└─ .run() // lib.rs:1383`

---

## Finding 2 — commands/mod.rs submodule count wrong

- **note location:** §3.3, "33 个子模块声明（commands/mod.rs:3-34）"
- **verdict:** wrong
- **source evidence:** `src-tauri/src/commands/mod.rs` lines 3-34 contain 31 `mod` declarations (lines 3-29: 27 modules, lines 31-34: 4 modules, line 30 is blank)
- **severity:** medium — stale count
- **replacement:** "31 个子模块声明（commands/mod.rs:3-34）"

---

## Finding 3 — Query layer file sizes dramatically wrong

- **note location:** §1.3 state management, "lib/query/ 目录（10 个文件）"
- **verdict:** wrong
- **source evidence (bytes from stat):**

| File | Notes claim | Actual bytes | Actual KB |
|------|------------|-------------|-----------|
| proxy.ts | 3.2KB | 6662 | 6.5KB |
| failover.ts | 2.7KB | 8133 | 7.9KB |
| omo.ts | 12.1KB | 2631 | 2.6KB |
| subscription.ts | 0.6KB | 2175 | 2.1KB |
| copilot.ts | 5.9KB | 1784 | 1.7KB |
| usage.ts | 6.0KB | 8751 | 8.5KB |

- **severity:** high — completely misleading file size claims; omo.ts and copilot.ts are swapped or hallucinated
- **replacement:** proxy.ts 6.5KB, failover.ts 7.9KB, omo.ts 2.6KB, subscription.ts 2.1KB, copilot.ts 1.7KB, usage.ts 8.5KB

---

## Finding 4 — DAO bullet-point sizes contradict own table

- **note location:** §3.5 database/dao/ section, bullet points after the table
- **verdict:** wrong
- **source evidence:**

| File | Table says | Bullet says | Actual bytes | Actual KB |
|------|-----------|------------|-------------|-----------|
| proxy.rs | 33.9KB | 7.5KB | 34715 | 33.9KB |
| settings.rs | 11.9KB | 28.9KB | 12235 | 11.9KB |
| mcp.rs | 4.1KB | 19.6KB | 4231 | 4.1KB |
| failover.rs | 4.8KB | 5.5KB | 4920 | 4.8KB |
| stream_check.rs | 2.7KB | 10.9KB | 2778 | 2.7KB |

- **severity:** high — bullet points give wildly wrong sizes that contradict the correct table above them
- **replacement:** Delete or correct the bullet points to match the table (proxy.rs 33.9KB, settings.rs 11.9KB, mcp.rs 4.1KB, failover.rs 4.8KB, stream_check.rs 2.7KB)

---

## Finding 5 — `app_store::refresh()` function name wrong

- **note location:** §1.1 startup chain, `app_store::refresh() // lib.rs:288`
- **verdict:** wrong
- **source evidence:** `src-tauri/src/lib.rs:288` is `app_store::refresh_app_config_dir_override(app.handle());`
- **severity:** medium — misleading function name
- **replacement:** `app_store::refresh_app_config_dir_override() // lib.rs:288`

---

## Finding 6 — Frontend hook line counts stale (large drift)

- **note location:** §1.3 state management, "hooks/ 目录（25 个 hooks）"
- **verdict:** stale
- **source evidence (wc -l):**

| File | Notes claim | Actual lines |
|------|------------|-------------|
| useSettings.ts | 512 | 505 |
| useProxyStatus.ts | 185 | 245 |
| useDirectorySettings.ts | 275 | 373 |
| useDragSort.ts | 95 | 119 |

- **severity:** medium — useProxyStatus.ts and useDirectorySettings.ts have drifted significantly (60 and 98 lines respectively)
- **replacement:** useSettings.ts 505, useProxyStatus.ts 245, useDirectorySettings.ts 373, useDragSort.ts 119

---

## Finding 7 — commands/provider.rs size bullet contradicts table

- **note location:** §3.3 commands/ section, bullet "provider.rs（40.6KB）"
- **verdict:** wrong
- **source evidence:** `src-tauri/src/commands/provider.rs` is 33040 bytes (32.3KB), matching the table entry "provider.rs | 32.3KB". The 40.6KB figure matches `src-tauri/src/provider.rs` (41528 bytes = 40.6KB), a different file.
- **severity:** medium — confusing two different files with the same name
- **replacement:** Delete the bullet or change to `commands/provider.rs（32.3KB）`

---

## Finding 8 — `lib.rs:999` for session usage sync loop off by 2

- **note location:** §1.1 startup chain, `session usage sync loop // lib.rs:999`
- **verdict:** wrong
- **source evidence:** `src-tauri/src/lib.rs:999` is `);` (end of gemini sync call). The sync loop `let mut interval = ...` starts at line 1002.
- **severity:** low — off by 2-3 lines
- **replacement:** `session usage sync loop // lib.rs:1002`

---

## Finding 9 — Import section start lines off by 1

- **note location:** §1.1 startup chain
- **verdict:** wrong
- **source evidence:**

| Notes claim | Actual start line | Content |
|------------|------------------|---------|
| `lib.rs:602-650` | 601 | `// 2. OMO 配置导入` comment at 601, `if` at 602 |
| `lib.rs:653-695` | 652 | `// 3. 导入 MCP 服务器配置` comment at 652, `if` at 653 |
| `lib.rs:698-720` | 697 | `// 4. 导入提示词文件` comment at 697, `if` at 698 |

- **severity:** low — consistently off by 1, pointing to the `if` statement rather than the section comment
- **replacement:** `lib.rs:601-650`, `lib.rs:652-695`, `lib.rs:697-720`

---

## Finding 10 — `settings.rs:5` reference is misleading

- **note location:** §3.5, "全局应用设置的读写（settings.rs:5）"
- **verdict:** ambiguous
- **source evidence:** `src-tauri/src/settings.rs:5` is `use std::sync::{OnceLock, RwLock};` — an import, not an interface definition. The actual AppSettings struct is at line 211, SETTINGS_STORE at line 519.
- **severity:** low — misleading reference
- **replacement:** `settings.rs:211` (AppSettings struct) or `settings.rs:519` (SETTINGS_STORE)

---

## Finding 11 — `provider.rs` line count claim (1153 vs 1154)

- **note location:** §3.4, "provider.rs — 核心数据模型（40.5KB，1153 行）"
- **verdict:** wrong (off by 1)
- **source evidence:** `wc -l` reports 1153, but file has 1154 lines (last line has no trailing newline). File size is 41528 bytes (40.6KB, not 40.5KB).
- **severity:** low — rounding difference
- **replacement:** "provider.rs — 核心数据模型（40.6KB，1153 行）"

---

## Finding 12 — `config.rs` size claim (13.9KB vs 14.0KB)

- **note location:** §3.1, "config.rs — 路径解析和文件 I/O（13.9KB，424 行）"
- **verdict:** wrong (rounding)
- **source evidence:** 14327 bytes = 14.0KB. `wc -l` reports 424.
- **severity:** low — rounding
- **replacement:** "config.rs — 路径解析和文件 I/O（14.0KB，424 行）"

---

## Finding 13 — `error.rs` size claim (3.4KB vs 3.5KB)

- **note location:** §3.2, "error.rs — 错误模型（3.4KB，146 行）"
- **verdict:** wrong (rounding)
- **source evidence:** 3565 bytes = 3.5KB. `wc -l` reports 146.
- **severity:** low — rounding
- **replacement:** "error.rs — 错误模型（3.5KB，146 行）"

---

## Finding 14 — `settings.rs` size claim (28.8KB vs 28.9KB)

- **note location:** §3.5, "settings.rs — 设置管理（28.8KB，877 行）"
- **verdict:** wrong (rounding)
- **source evidence:** 29572 bytes = 28.9KB. `wc -l` reports 876 (file has 877 lines, last without trailing newline).
- **severity:** low — rounding
- **replacement:** "settings.rs — 设置管理（28.9KB，877 行）"

---

## Finding 15 — Query layer line counts off by 1 (systematic)

- **note location:** §1.3 state management, "lib/query/ 目录"
- **verdict:** wrong (off by 1, consistent pattern)
- **source evidence (wc -l):**

| File | Notes claim | Actual |
|------|------------|--------|
| queries.ts | 156 | 155 |
| mutations.ts | 357 | 356 |
| proxy.ts | 244 | 243 |
| failover.ts | 289 | 288 |
| usage.ts | 320 | 319 |
| subscription.ts | 64 | 63 |

- **severity:** low — all off by 1 in same direction, likely tooling difference
- **replacement:** Use actual counts from wc -l

---

## Finding 16 — Frontend utility file line counts off by 1 (systematic)

- **note location:** Various §3.x sections for frontend utilities
- **verdict:** wrong (off by 1)
- **source evidence (wc -l):**

| File | Notes claim | Actual |
|------|------------|--------|
| base64.ts | 44 | 43 |
| clipboard.ts | 20 | 19 |
| updater.ts | 127 | 126 |
| platform.ts | 49 | 48 |
| authBinding.ts | 22 | 21 |
| usageRange.ts | 80 | 79 |
| api/index.ts | 31 | 30 |
| api/config.ts | 78 | 77 |
| api/model-fetch.ts | 93 | 92 |
| api/auth.ts | 107 | 106 |
| api/failover.ts | 100 | 99 |
| api/sessions.ts | 55 | 54 |
| query/index.ts | 6 | 5 |

- **severity:** low — all off by 1, consistent tooling difference
- **replacement:** Use actual counts from wc -l

---

## Finding 17 — `lib.rs` line count (1825 vs 1826)

- **note location:** §1.1, "lib.rs（1825 行）是整个后端的'上帝文件'"
- **verdict:** ambiguous
- **source evidence:** `wc -l` reports 1825. File has 1826 lines (last line 1826 is empty/EOF without trailing newline marker).
- **severity:** low — tooling difference
- **replacement:** "lib.rs（1825 行）" is acceptable per wc -l convention

---

## Finding 18 — Duplicate content blocks in notes

- **note location:** Multiple sections across chapters 1, 3, and 5
- **verdict:** ok (structural issue, not factual error)
- **source evidence:** The following blocks appear verbatim twice each:
  - SwitchLockManager definition (§1.3 and §3.5 and §3.6)
  - ProxyService definition (§1.3 and §3.5 and §3.6)
  - HotSwitchOutcome definition (§3.5 and §3.6)
  - database/dao/ file table (§3.5 and §3.6)
  - commands/mod.rs listing (§3.3 and §3.6)
  - database/ directory table (§3.3 and §3.6)
  - commands/ directory table (§3.3 and §3.6)
  - lib.rs module list (§3.3 and §3.6)
- **severity:** low — no factual error, but increases maintenance burden and risk of inconsistent updates

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| High | 3 | Wrong .run() line, query layer sizes hallucinated, DAO bullet sizes contradict table |
| Medium | 4 | Wrong command count, stale hook sizes, wrong function name, wrong file attribution |
| Low | 11 | Rounding, off-by-1 systematic, misleading reference, structural duplication |

**Verified OK (spot-checked, not exhaustive):** 120+ specific `file.rs:NNN` references across all chapters were verified correct, including all of: lib.rs startup chain (lines 203-1601), store.rs AppState (line 6), error.rs AppError (lines 6-63), app_config.rs types (lines 9-496), settings.rs types (lines 14-574), config.rs functions (lines 37-403), database/mod.rs (lines 52-95), proxy/switch_lock.rs (lines 14-26), services/proxy.rs (lines 55-64), proxy/forwarder.rs (lines 61-192), proxy/server.rs (lines 34-54), services/skill.rs (lines 28-51), services/provider/mod.rs (line 51), provider.rs (lines 10-121), and commands/mod.rs structure.
