# Chapter 3 (§3.6–§3.8) Database / Services Skeptic Findings

Verifier: ch3_db_services_skeptic
Scope: sections 3.6, 3.7, 3.8 — tool config comparison, database, services, commands, migrations

---

## Finding 1 — Codex config path wrong (format and extension)

**Note location:** §3.6 table, line 2537
**Quoted claim:** `Codex CLI | codex_config.rs | 66.4KB | ~/.codex/config.json`

**Verdict:** wrong

**Source evidence:**
- `src-tauri/src/codex_config.rs:44-45` — `pub fn get_codex_config_path() -> PathBuf { get_codex_config_dir().join("config.toml") }`
- The file is TOML, not JSON. The extension is `.toml`.

**Severity:** medium

**Replacement text:** `| Codex CLI | codex_config.rs | 66.5KB | ~/.codex/config.toml |`

---

## Finding 2 — OpenCode config path wrong (directory and filename)

**Note location:** §3.6 table, line 2539
**Quoted claim:** `OpenCode | opencode_config.rs | 6.9KB | ~/.opencode/config.json`

**Verdict:** wrong

**Source evidence:**
- `src-tauri/src/opencode_config.rs:40-46` — `get_opencode_dir()` returns `~/.config/opencode`, and `get_opencode_config_path()` joins `"opencode.json"`.
- Actual path: `~/.config/opencode/opencode.json`, not `~/.opencode/config.json`.

**Severity:** medium

**Replacement text:** `| OpenCode | opencode_config.rs | 6.9KB | ~/.config/opencode/opencode.json |`

---

## Finding 3 — OpenClaw config path wrong (filename)

**Note location:** §3.6 table, line 2540
**Quoted claim:** `OpenClaw | openclaw_config.rs | 34.9KB | ~/.openclaw/config.json`

**Verdict:** wrong

**Source evidence:**
- `src-tauri/src/openclaw_config.rs:46-47` — `pub fn get_openclaw_config_path() -> PathBuf { get_openclaw_dir().join("openclaw.json") }`
- Actual path: `~/.openclaw/openclaw.json`, not `~/.openclaw/config.json`.

**Severity:** medium

**Replacement text:** `| OpenClaw | openclaw_config.rs | 35.0KB | ~/.openclaw/openclaw.json |`

---

## Finding 4 — "Common patterns" claim unsupported

**Note location:** §3.6 lines 2545-2550
**Quoted claim:** "共同模式（每个模块都有）: 1. read_xxx_config() 2. write_xxx_config() 3. build_live_config() 4. switch_provider() 5. import_from_live()"

**Verdict:** wrong

**Source evidence:**
- `grep -n "fn.*switch_provider" src-tauri/src/hermes_config.rs` → 0 matches
- `grep -n "fn.*switch_provider" src-tauri/src/openclaw_config.rs` → 0 matches
- `grep -n "fn.*switch_provider" src-tauri/src/opencode_config.rs` → 0 matches
- `grep -n "fn.*import_from_live" src-tauri/src/hermes_config.rs` → 0 matches
- `grep -n "fn.*build_live" src-tauri/src/hermes_config.rs` → 0 matches
- `switch_provider()` and `import_from_live()` live in `services/provider/mod.rs`, not in the individual config modules.
- `build_live_config()` does not exist as a named function in any config module.

**Severity:** high — misrepresents the architecture by claiming functions exist in config modules when they're centralized in the service layer.

**Replacement text:**
```
**注意**：`switch_provider()` 和 `import_from_live()` 逻辑集中在 `services/provider/mod.rs`，不在各 config 模块中。
各 config 模块提供的是路径解析、读写原始配置文件、以及构建特定工具 live config 的辅助函数。
```

---

## Finding 5 — proxy_config table SQL missing 4 columns

**Note location:** §3.7 lines 2626-2643
**Quoted claim:** proxy_config CREATE TABLE statement

**Verdict:** wrong

**Source evidence:** `src-tauri/src/database/schema.rs:124-137`

The notes omit these columns present in the source:
- `enable_logging INTEGER NOT NULL DEFAULT 1` (line 127)
- `streaming_idle_timeout INTEGER NOT NULL DEFAULT 120` (line 130)
- `created_at TEXT NOT NULL DEFAULT (datetime('now'))` (line 136)
- `updated_at TEXT NOT NULL DEFAULT (datetime('now'))` (line 136)

**Severity:** high — the `streaming_idle_timeout` and `enable_logging` columns are operational config that a maintainer would need to know about.

**Replacement SQL:**
```sql
CREATE TABLE IF NOT EXISTS proxy_config (
    app_type TEXT PRIMARY KEY CHECK (app_type IN ('claude','codex','gemini')),
    proxy_enabled INTEGER NOT NULL DEFAULT 0,
    listen_address TEXT NOT NULL DEFAULT '127.0.0.1',
    listen_port INTEGER NOT NULL DEFAULT 15721,
    enable_logging INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 0,
    auto_failover_enabled INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    streaming_first_byte_timeout INTEGER NOT NULL DEFAULT 60,
    streaming_idle_timeout INTEGER NOT NULL DEFAULT 120,
    non_streaming_timeout INTEGER NOT NULL DEFAULT 600,
    circuit_failure_threshold INTEGER NOT NULL DEFAULT 4,
    circuit_success_threshold INTEGER NOT NULL DEFAULT 2,
    circuit_timeout_seconds INTEGER NOT NULL DEFAULT 60,
    circuit_error_rate_threshold REAL NOT NULL DEFAULT 0.6,
    circuit_min_requests INTEGER NOT NULL DEFAULT 10,
    default_cost_multiplier TEXT NOT NULL DEFAULT '1',
    pricing_model_source TEXT NOT NULL DEFAULT 'response',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
)
```

---

## Finding 6 — proxy_request_logs table SQL missing 2 cost columns

**Note location:** §3.7 lines 2714-2738
**Quoted claim:** proxy_request_logs CREATE TABLE statement

**Verdict:** wrong

**Source evidence:** `src-tauri/src/database/schema.rs:184-196`

The notes omit these columns present in the source:
- `cache_read_cost_usd TEXT NOT NULL DEFAULT '0'` (line 190)
- `cache_creation_cost_usd TEXT NOT NULL DEFAULT '0'` (line 190)

**Severity:** medium — these are cost-tracking columns needed for accurate billing/usage queries.

**Replacement:** Add after `output_cost_usd`:
```
    cache_read_cost_usd TEXT NOT NULL DEFAULT '0',
    cache_creation_cost_usd TEXT NOT NULL DEFAULT '0',
```

---

## Finding 7 — session_log_sync table SQL missing last_synced_at column

**Note location:** §3.7 lines 2686-2691
**Quoted claim:** session_log_sync CREATE TABLE statement (3 columns)

**Verdict:** wrong

**Source evidence:** `src-tauri/src/database/schema.rs:280-285`

The actual table has 4 columns; the notes omit:
- `last_synced_at INTEGER NOT NULL` (line 284)

**Severity:** medium

**Replacement SQL:**
```sql
CREATE TABLE IF NOT EXISTS session_log_sync (
    file_path TEXT PRIMARY KEY,
    last_modified INTEGER NOT NULL,
    last_line_offset INTEGER NOT NULL DEFAULT 0,
    last_synced_at INTEGER NOT NULL
)
```

---

## Finding 8 — Database module structure sizes (first listing) — 3 of 4 wrong

**Note location:** §3.7 lines 2860-2864
**Quoted claim:**
```
- mod.rs（1.1KB）
- schema.rs（11.7KB）
- backup.rs（31.7KB）
- migration.rs（28.3KB）
```

**Verdict:** wrong

**Source evidence:**
| File | Claimed | Actual (bytes) | Actual (KB) |
|------|---------|----------------|-------------|
| mod.rs | 1.1KB | 9,128 | 8.9KB |
| schema.rs | 11.7KB | 79,691 | 77.8KB |
| backup.rs | 31.7KB | 32,495 | 31.7KB ✓ |
| migration.rs | 28.3KB | 9,468 | 9.2KB |

The schema.rs size is off by ~6.7×. The note itself elsewhere (line 2989) correctly states 77.8KB for schema.rs, making this an internal contradiction.

**Severity:** high — completely misleading for a maintainer estimating module complexity.

**Replacement text:**
```
- `mod.rs`（8.9KB）— Database 结构体 + 初始化
- `schema.rs`（77.8KB）— 表结构定义 + Schema 迁移（当前版本 `SCHEMA_VERSION = 10`，`mod.rs:52`）
- `backup.rs`（31.7KB）— SQL 导入导出 + 快照备份
- `migration.rs`（9.2KB）— JSON → SQLite 数据迁移
```

---

## Finding 9 — DAO line counts — 6 of 12 wrong

**Note location:** §3.7 lines 2865-2877
**Quoted claim:** Line counts for each DAO file

**Verdict:** wrong

**Source evidence:** (`wc -l src-tauri/src/database/dao/*.rs`)
| File | Claimed lines | Actual lines |
|------|--------------|--------------|
| providers.rs | 786 | 786 ✓ |
| proxy.rs | 247 | **952** |
| usage_rollup.rs | 377 | 377 ✓ |
| settings.rs | 876 | **327** |
| skills.rs | 263 | 263 ✓ |
| failover.rs | 182 | **149** |
| mcp.rs | 643 | **106** |
| prompts.rs | 88 | 88 ✓ |
| providers_seed.rs | 94 | 94 ✓ |
| stream_check.rs | 364 | **74** |
| universal_providers.rs | 74 | 74 ✓ |
| mod.rs | 66 | **19** |

proxy.rs is off by 3.9× (247 vs 952). mcp.rs is off by 6.1× (643 vs 106). stream_check.rs is off by 4.9× (364 vs 74). These appear to be hallucinated or from a different version.

**Severity:** high — wildly wrong line counts mislead anyone estimating code complexity.

**Replacement text:**
```
  - `providers.rs`（786 行）— Provider CRUD
  - `proxy.rs`（952 行）— 代理配置和请求日志
  - `usage_rollup.rs`（377 行）— 用量统计
  - `settings.rs`（327 行）— 通用设置
  - `skills.rs`（263 行）— Skills 管理
  - `failover.rs`（149 行）— 故障转移队列
  - `mcp.rs`（106 行）— MCP 服务器配置
  - `prompts.rs`（88 行）— Prompt 管理
  - `providers_seed.rs`（94 行）— 官方预设种子数据
  - `stream_check.rs`（74 行）— 流式检查配置
  - `universal_providers.rs`（74 行）— 通用 Provider
  - `mod.rs`（19 行）— 模块声明
```

---

## Finding 10 — commands/mod.rs submodule count wrong (33 vs 31)

**Note location:** §3.8 line 2982
**Quoted claim:** "33 个子模块声明（commands/mod.rs:3-34）"

**Verdict:** wrong

**Source evidence:** `src-tauri/src/commands/mod.rs:3-34`

Counting `mod` declarations: auth, balance, codex_oauth, coding_plan, config, copilot, deeplink, env, failover, global_proxy, hermes, import_export, mcp, misc, model_fetch, omo, openclaw, plugin, prompt, provider, proxy, session_manager, settings, skill, stream_check, subscription, sync_support, lightweight, usage, webdav_sync, workspace = **31 modules**.

`grep -c "^mod \\|^pub mod " src-tauri/src/commands/mod.rs` → 31.

**Severity:** medium — stale count, off by 2.

**Replacement text:** "31 个子模块声明（commands/mod.rs:3-34）"

---

## Finding 11 — Services file sizes — 11 of 22 wildly wrong

**Note location:** §3.8 table, lines 3630-3651
**Quoted claim:** Size for each services/ module

**Verdict:** wrong

**Source evidence:** (`wc -c src-tauri/src/services/*.rs src-tauri/src/services/**/*.rs`)

| File | Claimed | Actual (bytes) | Actual (KB) | Off by |
|------|---------|----------------|-------------|--------|
| subscription.rs | 1.3KB | 42,077 | 41.1KB | 31.6× |
| coding_plan.rs | 607B | 22,473 | 21.9KB | 37.0× |
| env_checker.rs | 168B | 6,001 | 5.9KB | 35.7× |
| env_manager.rs | 240B | 8,693 | 8.5KB | 36.2× |
| webdav.rs | 554B | 18,385 | 18.0KB | 33.2× |
| webdav_sync.rs | 884B | 29,661 | 29.0KB | 33.6× |
| webdav_auto_sync.rs | 274B | 8,211 | 8.0KB | 30.0× |
| session_usage.rs | 682B | 23,134 | 22.6KB | 33.9× |
| session_usage_codex.rs | 787B | 26,185 | 25.6KB | 33.3× |
| session_usage_gemini.rs | 494B | 16,520 | 16.1KB | 33.4× |
| omo.rs | 560B | 19,553 | 19.1KB | 34.9× |

All 11 wrong sizes are off by ~30-37×, consistent with sizes being taken from a `ls -la` short listing (which shows permissions like `644` and the raw byte count for tiny files, but the note author appears to have captured the wrong column or used an artifact from a different listing format). The pattern "644 shown as file size" matches the `ls -la` output I observed in the dao/ directory listing where every entry showed `644` as the first number.

**Severity:** high — 11 service modules listed with sizes 30-37× smaller than reality; any maintainer relying on these to gauge module complexity would be severely misled.

**Replacement table rows:**
```
| subscription.rs | 41.1KB | 订阅管理 |
| coding_plan.rs | 21.9KB | Coding Plan |
| env_checker.rs | 5.9KB | 环境变量检查 |
| env_manager.rs | 8.5KB | 环境变量管理 |
| webdav.rs | 18.0KB | WebDAV 客户端 |
| webdav_sync.rs | 29.0KB | WebDAV 同步逻辑 |
| webdav_auto_sync.rs | 8.0KB | 自动同步 |
| session_usage.rs | 22.6KB | Claude 会话用量同步 |
| session_usage_codex.rs | 25.6KB | Codex 会话用量同步 |
| session_usage_gemini.rs | 16.1KB | Gemini 会话用量同步 |
| omo.rs | 19.1KB | OMO 集成 |
```

---

## Finding 12 — DAO prose sizes contradict DAO table above (5 wrong)

**Note location:** §3.8 lines 2950-2960
**Quoted claim:** Prose summary of DAO file sizes

**Verdict:** wrong

**Source evidence:** This prose block repeats the DAO table from lines 2935-2949 but with 5 different (wrong) sizes:

| File | Prose says | Table says | Actual |
|------|-----------|------------|--------|
| proxy.rs | 7.5KB | 33.9KB | 33.9KB |
| settings.rs | 28.9KB | 11.9KB | 11.9KB |
| failover.rs | 5.5KB | 4.8KB | 4.8KB |
| mcp.rs | 19.6KB | 4.1KB | 4.1KB |
| stream_check.rs | 10.9KB | 2.7KB | 2.7KB |

The table at 2935-2949 is correct; the prose summary at 2950-2960 has 5 wrong sizes. This is a redundant block that should be deleted entirely.

**Severity:** medium — internal contradiction within the same section confuses readers.

**Replacement:** Delete lines 2950-2960 (the prose list duplicating the table with wrong sizes).

---

## Finding 13 — Database::init() pseudocode omits key steps and error handling

**Note location:** §3.7 lines 2829-2844
**Quoted claim:** Simplified `init()` pseudocode

**Verdict:** wrong

**Source evidence:** `src-tauri/src/database/mod.rs:95-158`

The pseudocode omits:
1. **`db_exists` check** — auto_vacuum is only set for new databases (`if !db_exists`, line 109), but the notes show it unconditionally.
2. **Pre-migration backup** — lines 122-134 create a backup when upgrading from an older schema version. Not in pseudocode.
3. **`ensure_incremental_auto_vacuum()`** — line 138, called between schema migrations and pricing seed. Not in pseudocode or the numbered list at 2846-2859.
4. **Error handling** — cleanup operations use `if let Err(e)` with `log::warn!` (non-fatal), not `?` (fatal) as shown in the pseudocode.

**Severity:** medium — the pseudocode suggests failures in cleanup/rollup are fatal when they're actually logged and swallowed; a maintainer reading the notes would add unnecessary error handling.

**Replacement pseudocode:**
```rust
pub fn init() -> Result<Self, AppError> {  // database/mod.rs:95
    let db_path = get_app_config_dir().join("cc-switch.db");
    let db_exists = db_path.exists();
    // 确保父目录存在
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let conn = Connection::open(&db_path)?;
    conn.execute("PRAGMA foreign_keys = ON;", [])?;
    if !db_exists {
        conn.execute("PRAGMA auto_vacuum = INCREMENTAL;", [])?;  // 仅新库
    }
    register_db_change_hook(&conn);
    let db = Self { conn: Mutex::new(conn) };
    db.create_tables()?;
    // 仅版本升级时创建备份
    if version > 0 && version < SCHEMA_VERSION { db.backup_database_file()?; }
    db.apply_schema_migrations()?;
    db.ensure_incremental_auto_vacuum()?;  // 确保 auto_vacuum 设置
    db.ensure_model_pricing_seeded()?;
    // 以下操作失败仅 warn，不中断启动
    db.cleanup_old_stream_check_logs(7).ok();
    db.rollup_and_prune(30).ok();
    conn.execute_batch("PRAGMA incremental_vacuum;").ok();
    Ok(db)
}
```

---

## Finding 14 — schema.rs line count: note says 2050 in body, 2050 is exact

**Note location:** §3.7 line 2566
**Quoted claim:** "schema.rs（2050 行，77.8KB）"

**Verdict:** ok (minor)

**Source evidence:** `wc -l src-tauri/src/database/schema.rs` → 2050. `wc -c` → 79,691 bytes = 77.8KB. Both match.

**Severity:** low — no action needed.

---

## Finding 15 — services/mod.rs "25 个子模块" — correct but table incomplete

**Note location:** §3.8 line 2896
**Quoted claim:** "25 个子模块"

**Verdict:** ok

**Source evidence:** `grep -c "^pub mod" src-tauri/src/services/mod.rs` → 25. The count is correct. However, the note's table at 2898-2901 only shows 1 row (provider/mod.rs) before abruptly ending and jumping to ProviderService internals. The remaining 24 modules appear later in a separate table at 3630-3651 with the size errors documented in Finding 11.

**Severity:** low — the count is accurate; the presentation is fragmented.

---

## Finding 16 — lib.rs "34 个模块声明" — correct

**Note location:** §3.8 line 3055
**Quoted claim:** "34 个模块声明（lib.rs:1-36）"

**Verdict:** ok

**Source evidence:** `grep -c "^pub mod\\|^mod " src-tauri/src/lib.rs` → 34.

**Severity:** low — no action needed.

---

## Finding 17 — Commands file sizes all verified correct

**Note location:** §3.8 lines 3000-3034
**Quoted claim:** Size for each commands/ file

**Verdict:** ok

**Source evidence:** All 32 command file sizes match actual byte counts within rounding tolerance (±0.1KB). Verified via `wc -c src-tauri/src/commands/*.rs`.

**Severity:** low — no action needed.

---

## Finding 18 — DAO byte-size table at lines 2935-2949 — all correct

**Note location:** §3.8 lines 2935-2949
**Quoted claim:** Byte sizes for DAO files

**Verdict:** ok

**Source evidence:** All 12 DAO file sizes match actual byte counts. Verified via `wc -c src-tauri/src/database/dao/*.rs`.

**Severity:** low — no action needed.

---

## Finding 19 — Section 3.6 config file sizes all correct

**Note location:** §3.6 table, lines 2533-2541
**Quoted claim:** File sizes for each tool config module

**Verdict:** ok

**Source evidence:** All 7 file sizes match actual byte counts within ±0.1KB. Verified via `wc -c`.

**Severity:** low — no action needed.

---

## Finding 20 — proxy.rs table at line 3630 says 141.3KB, provider/mod.rs says 105.5KB — both correct

**Note location:** §3.8 lines 2899-3630
**Quoted claim:** Services file sizes

**Verdict:** ok (for the files not covered by Finding 11)

**Source evidence:** `wc -c` confirms provider/mod.rs = 108,053 bytes (105.5KB), proxy.rs = 144,756 bytes (141.4KB). The remaining service file sizes in the table (provider, proxy, usage_stats, skill, stream_check, mcp, prompt, config, speedtest, balance, model_fetch) all match within tolerance.

**Severity:** low — no action needed.

---

## Summary

| # | Section | Verdict | Severity | Issue |
|---|---------|---------|----------|-------|
| 1 | 3.6 | wrong | medium | Codex config path: `.json` → `.toml` |
| 2 | 3.6 | wrong | medium | OpenCode config path: wrong dir and filename |
| 3 | 3.6 | wrong | medium | OpenClaw config path: wrong filename |
| 4 | 3.6 | wrong | high | "Common patterns" don't exist in config modules |
| 5 | 3.7 | wrong | high | proxy_config SQL missing 4 columns |
| 6 | 3.7 | wrong | medium | proxy_request_logs SQL missing 2 cost columns |
| 7 | 3.7 | wrong | medium | session_log_sync SQL missing last_synced_at |
| 8 | 3.7 | wrong | high | Database module sizes: 3 of 4 wrong (up to 6.7×) |
| 9 | 3.7 | wrong | high | DAO line counts: 6 of 12 wrong (up to 6.1×) |
| 10 | 3.8 | wrong | medium | commands submodule count: 33 vs actual 31 |
| 11 | 3.8 | wrong | high | Services file sizes: 11 of 22 wrong (30-37× off) |
| 12 | 3.8 | wrong | medium | DAO prose sizes contradict DAO table (5 wrong) |
| 13 | 3.7 | wrong | medium | Database::init() pseudocode omits key steps |

**Totals:** 13 non-ok findings (0 hallucination, 13 wrong, 0 stale, 0 unsupported, 0 ambiguous), 7 ok.
