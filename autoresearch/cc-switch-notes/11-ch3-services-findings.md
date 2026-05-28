# Chapter 3 Services Findings (3.6–3.8)

## Finding 1 — "共同模式" claims `build_live_config()` exists in each config module

**Note location**: 3.6 各工具 config 模块对比 → "共同模式（每个模块都有）" item 3

**Quoted claim**: `build_live_config()` — 构建当前生效的配置

**Verdict**: **hallucination**

**Source evidence**: `grep -rn "build_live_config" src-tauri/src/` returns zero matches. No function named `build_live_config` exists anywhere in the codebase. The closest function is `build_effective_settings_with_common_config` in `services/provider/live.rs:483`, which is a `pub(crate)` internal helper, not a per-module pattern.

**Severity**: high — fabricates a nonexistent API pattern that supposedly exists in every config module

**Replacement**: Remove item 3 from the "共同模式" list.

---

## Finding 2 — "共同模式" claims `switch_provider()` exists in each config module

**Note location**: 3.6 各工具 config 模块对比 → "共同模式（每个模块都有）" item 4

**Quoted claim**: `switch_provider()` — 切换 provider 的核心逻辑

**Verdict**: **hallucination**

**Source evidence**: `grep -rn "switch_provider" src-tauri/src/*_config.rs` returns zero matches. The function `switch_provider` exists only as a Tauri command in `commands/provider.rs:102` and delegates to `ProviderService::switch()` in `services/provider/mod.rs:1569`. It is not a per-config-module pattern.

**Severity**: high — misattributes a single centralized function as a per-module pattern

**Replacement**: Remove item 4 from the "共同模式" list. The actual switch logic lives in `ProviderService::switch()` (`services/provider/mod.rs:1569`), called from the `switch_provider` Tauri command (`commands/provider.rs:102`).

---

## Finding 3 — "共同模式" claims `import_from_live()` exists in each config module

**Note location**: 3.6 各工具 config 模块对比 → "共同模式（每个模块都有）" item 5

**Quoted claim**: `import_from_live()` — 从工具的 live 配置导入 provider

**Verdict**: **hallucination**

**Source evidence**: `grep -rn "import_from_live" src-tauri/src/` returns zero matches. The closest functions are `import_default_config` (`services/provider/mod.rs:2135` via re-export from `live.rs`), `import_hermes_providers_from_live`, `import_openclaw_providers_from_live`, and `import_opencode_providers_from_live` — all in `services/provider/live.rs`, not in individual config modules.

**Severity**: high — fabricates a nonexistent per-module function name

**Replacement**: Remove item 5 from the "共同模式" list. Import-from-live logic lives in `services/provider/live.rs` with tool-specific variants (`import_hermes_providers_from_live`, etc.).

---

## Finding 4 — "共同模式" claims `read_xxx_config()` exists in every module

**Note location**: 3.6 各工具 config 模块对比 → "共同模式（每个模块都有）" item 1

**Quoted claim**: `read_xxx_config()` — 读取工具的配置文件 (implied: every module)

**Verdict**: **ambiguous**

**Source evidence**: `read_codex_config_text()` exists in `codex_config.rs:133`, `read_opencode_config()` in `opencode_config.rs:54`, `read_openclaw_config()` in `openclaw_config.rs:199`, `read_hermes_config()` in `hermes_config.rs:108`. However, `gemini_config.rs` and `claude_desktop_config.rs` do not export a `read_xxx_config()` function by that exact naming pattern. The Claude Code config is managed via `services/provider/mod.rs` (no standalone config module). The claim "每个模块都有" is overstated.

**Severity**: medium — partially true but overstated as universal

**Replacement**: "大部分模块有 `read_xxx_config()` 函数，但命名和签名不统一；Claude Code 的配置读取通过 `services/provider/live.rs` 处理。"

---

## Finding 5 — "共同模式" claims `write_xxx_config()` exists in every module

**Note location**: 3.6 各工具 config 模块对比 → "共同模式（每个模块都有）" item 2

**Quoted claim**: `write_xxx_config()` — 写入工具的配置文件 (implied: every module)

**Verdict**: **ambiguous**

**Source evidence**: `write_codex_live_config_atomic_with_stable_provider()` exists in `codex_config.rs:418`, `write_opencode_config()` in `opencode_config.rs:72`, `write_yaml_section_to_config()` in `hermes_config.rs:296`. No `write_xxx_config()` function found in `gemini_config.rs`, `openclaw_config.rs`, or `claude_desktop_config.rs` by that naming pattern.

**Severity**: medium — partially true but overstated as universal

**Replacement**: "部分模块有 `write_xxx_config()` 函数，但命名不统一；写入逻辑分散在各模块中，有些使用不同的函数名。"

---

## Finding 6 — Database module file sizes: `mod.rs` listed as 1.1KB

**Note location**: 3.7 database/ → 模块结构

**Quoted claim**: `mod.rs`（1.1KB）— Database 结构体 + 初始化

**Verdict**: **wrong**

**Source evidence**: `ls -lh src-tauri/src/database/mod.rs` → 8.9KB. The 1.1KB figure matches `services/mod.rs` (1.1KB), not `database/mod.rs`.

**Severity**: medium — wrong file size, off by 8x

**Replacement**: `mod.rs`（8.9KB）— Database 结构体 + 初始化

---

## Finding 7 — Database module file sizes: `schema.rs` listed as 11.7KB

**Note location**: 3.7 database/ → 模块结构

**Quoted claim**: `schema.rs`（11.7KB）— 表结构定义 + Schema 迁移

**Verdict**: **wrong**

**Source evidence**: `ls -lh src-tauri/src/database/schema.rs` → 77.8KB (2050 lines). The 11.7KB figure is off by ~6.6x. The same section correctly states "schema.rs 模块（database/schema.rs，2050 行，77.8KB）" at line 2566, creating an internal contradiction.

**Severity**: medium — wrong file size, internally contradicts the same section

**Replacement**: `schema.rs`（77.8KB）— 表结构定义 + Schema 迁移

---

## Finding 8 — Database module file sizes: `migration.rs` listed as 28.3KB

**Note location**: 3.7 database/ → 模块结构

**Quoted claim**: `migration.rs`（28.3KB）— JSON → SQLite 数据迁移

**Verdict**: **wrong**

**Source evidence**: `ls -lh src-tauri/src/database/migration.rs` → 9.2KB. The 28.3KB figure is off by ~3x.

**Severity**: medium — wrong file size

**Replacement**: `migration.rs`（9.2KB）— JSON → SQLite 数据迁移

---

## Finding 9 — DAO line counts: `settings.rs` listed as 876 行

**Note location**: 3.7 database/ → dao/ line count list

**Quoted claim**: `settings.rs`（876 行）— 通用设置

**Verdict**: **wrong**

**Source evidence**: `wc -l src-tauri/src/database/dao/settings.rs` → 327 lines. The 876 figure is off by ~2.7x.

**Severity**: medium — wrong line count

**Replacement**: `settings.rs`（327 行）— 通用设置

---

## Finding 10 — DAO line counts: `failover.rs` listed as 182 行

**Note location**: 3.7 database/ → dao/ line count list

**Quoted claim**: `failover.rs`（182 行）— 故障转移队列

**Verdict**: **wrong**

**Source evidence**: `wc -l src-tauri/src/database/dao/failover.rs` → 149 lines.

**Severity**: low — wrong line count

**Replacement**: `failover.rs`（149 行）— 故障转移队列

---

## Finding 11 — DAO line counts: `mcp.rs` listed as 643 行

**Note location**: 3.7 database/ → dao/ line count list

**Quoted claim**: `mcp.rs`（643 行）— MCP 服务器配置

**Verdict**: **wrong**

**Source evidence**: `wc -l src-tauri/src/database/dao/mcp.rs` → 106 lines. The 643 figure is off by ~6x.

**Severity**: medium — wrong line count, dramatically off

**Replacement**: `mcp.rs`（106 行）— MCP 服务器配置

---

## Finding 12 — DAO line counts: `stream_check.rs` listed as 364 行

**Note location**: 3.7 database/ → dao/ line count list

**Quoted claim**: `stream_check.rs`（364 行）— 流式检查配置

**Verdict**: **wrong**

**Source evidence**: `wc -l src-tauri/src/database/dao/stream_check.rs` → 74 lines. The 364 figure is off by ~5x.

**Severity**: medium — wrong line count, dramatically off

**Replacement**: `stream_check.rs`（74 行）— 流式检查配置

---

## Finding 13 — DAO line counts: `mod.rs` listed as 66 行

**Note location**: 3.7 database/ → dao/ line count list

**Quoted claim**: `mod.rs`（66 行）— 模块声明

**Verdict**: **wrong**

**Source evidence**: `wc -l src-tauri/src/database/dao/mod.rs` → 19 lines.

**Severity**: low — wrong line count

**Replacement**: `mod.rs`（19 行）— 模块声明

---

## Finding 14 — DAO inline text sizes contradict the table above

**Note location**: 3.8 services/ → database/dao/ inline bullet list (lines 2950–2960)

**Quoted claims**: The inline text lists sizes that differ from the table at lines 2936–2949 and from the actual source.

**Verdict**: **wrong** (5 of 11 entries)

| File | Inline text says | Table says | Actual | Verdict |
|------|-----------------|------------|--------|---------|
| proxy.rs | 7.5KB | 33.9KB | 33.9KB | wrong |
| settings.rs | 28.9KB | 11.9KB | 11.9KB | wrong |
| failover.rs | 5.5KB | 4.8KB | 4.8KB | wrong |
| mcp.rs | 19.6KB | 4.1KB | 4.1KB | wrong |
| stream_check.rs | 10.9KB | 2.7KB | 2.7KB | wrong |

**Source evidence**: `ls -lh src-tauri/src/database/dao/*.rs` confirms the table sizes. The inline text appears to use stale or hallucinated sizes that don't match either the table or the filesystem.

**Severity**: medium — 5 wrong sizes in inline commentary that contradict the table directly above

**Replacement**: Update inline text to match the table:
- `proxy.rs`（33.9KB）是最大的 DAO 文件
- `settings.rs`（11.9KB）包含设置的读写操作
- `failover.rs`（4.8KB）包含故障转移队列操作
- `mcp.rs`（4.1KB）包含 MCP 服务器的 CRUD 操作
- `stream_check.rs`（2.7KB）包含流式检查记录操作

---

## Finding 15 — proxy_config table missing 4 columns

**Note location**: 3.7 database/ → proxy_config 表 CREATE TABLE (lines 2626–2643)

**Quoted claim**: The CREATE TABLE statement lists 16 columns.

**Verdict**: **stale**

**Source evidence**: `src-tauri/src/database/schema.rs:124-137` shows 20 columns. The notes are missing:
- `enable_logging INTEGER NOT NULL DEFAULT 1`
- `streaming_idle_timeout INTEGER NOT NULL DEFAULT 120`
- `created_at TEXT NOT NULL DEFAULT (datetime('now'))`
- `updated_at TEXT NOT NULL DEFAULT (datetime('now'))`

**Severity**: medium — schema documentation is incomplete

**Replacement**: Add the 4 missing columns to the CREATE TABLE listing.

---

## Finding 16 — commands/mod.rs claims 33 submodules

**Note location**: 3.8 services/ → commands/mod.rs section (line 2982)

**Quoted claim**: "33 个子模块声明（commands/mod.rs:3-34）"

**Verdict**: **wrong**

**Source evidence**: Counting `mod` declarations in `src-tauri/src/commands/mod.rs` lines 3-34: lines 3-29 have 27 declarations, line 30 is blank, lines 31-34 have 4 declarations = 31 total. The file has 67 lines total (confirmed by `wc -l`). The notes list 32 module names in the code block (lines 2966-2976) but claim 33.

**Severity**: low — count off by 2

**Replacement**: "31 个子模块声明（commands/mod.rs:3-34）"

---

## Finding 17 — Database::init() flow description omits steps

**Note location**: 3.7 database/ → Database::init() 初始化流程 (lines 2846–2858)

**Quoted claim**: 13-step initialization flow.

**Verdict**: **stale**

**Source evidence**: The actual `Database::init()` at `database/mod.rs:95-158` has 15 distinct operations. The notes omit:
- `db.ensure_incremental_auto_vacuum()` (line 138, between migrations and seeding)
- `PRAGMA incremental_vacuum` (line 153, disk space reclamation at end)

The notes also merge "启用外键约束" and "新数据库设置增量自动清理" into steps 4-5, but the code only sets auto_vacuum for new databases (`if !db_exists`), which the notes correctly describe but the code block at lines 2831-2843 omits the conditional.

**Severity**: low — flow description is incomplete but not misleading

**Replacement**: Add steps for `ensure_incremental_auto_vacuum()` (after step 9) and `PRAGMA incremental_vacuum` (after step 12).

---

## Summary

| # | Location | Verdict | Severity |
|---|----------|---------|----------|
| 1 | 3.6 共同模式 item 3 | hallucination | high |
| 2 | 3.6 共同模式 item 4 | hallucination | high |
| 3 | 3.6 共同模式 item 5 | hallucination | high |
| 4 | 3.6 共同模式 item 1 | ambiguous | medium |
| 5 | 3.6 共同模式 item 2 | ambiguous | medium |
| 6 | 3.7 mod.rs size | wrong | medium |
| 7 | 3.7 schema.rs size | wrong | medium |
| 8 | 3.7 migration.rs size | wrong | medium |
| 9 | 3.7 settings.rs lines | wrong | medium |
| 10 | 3.7 failover.rs lines | wrong | low |
| 11 | 3.7 mcp.rs lines | wrong | medium |
| 12 | 3.7 stream_check.rs lines | wrong | medium |
| 13 | 3.7 mod.rs lines | wrong | low |
| 14 | 3.8 DAO inline sizes | wrong | medium |
| 15 | 3.7 proxy_config columns | stale | medium |
| 16 | 3.8 commands/mod count | wrong | low |
| 17 | 3.7 Database::init flow | stale | low |

**3 high** (hallucinated API patterns), **10 medium** (wrong sizes/counts/schema), **4 low** (minor count/flow issues).
