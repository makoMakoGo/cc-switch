# Chapter 3 Database Persistence Fact-Check Findings

Agent: `swarm-cc-switch-notes-factcheck-ch3_database_persistence_trace-0`
Scope: Sections 3.6–3.8, database/persistence and migration claims.

---

## Finding 1 — `proxy_config` table schema missing 4 columns

**Note location:** §3.7, "proxy_config 表" (lines 2626–2643)

**Claim:** The `CREATE TABLE` statement lists 16 columns.

**Verdict:** stale

**Severity:** high — a maintainer reading this schema would think the table is simpler than it is, missing fields for logging, idle timeout, and timestamps.

**Source evidence:** `src-tauri/src/database/schema.rs:124–137`

The actual `CREATE TABLE` (line 124) has 20 columns. The notes omit:
- `enable_logging INTEGER NOT NULL DEFAULT 1` (line 127)
- `streaming_idle_timeout INTEGER NOT NULL DEFAULT 120` (line 130)
- `created_at TEXT NOT NULL DEFAULT (datetime('now'))` (line 136)
- `updated_at TEXT NOT NULL DEFAULT (datetime('now'))` (line 136)

**Replacement:** Add these 4 columns to the SQL block in the notes at lines 2626–2643.

---

## Finding 2 — `session_log_sync` table schema missing `last_synced_at` column

**Note location:** §3.7, "session_log_sync 表" (lines 2684–2691)

**Claim:** The table has 3 columns: `file_path`, `last_modified`, `last_line_offset`.

**Verdict:** stale

**Severity:** high — this column is `NOT NULL`, so ignoring it would break INSERTs for anyone using the notes as a schema reference.

**Source evidence:** `src-tauri/src/database/schema.rs:280–284`

The actual schema has 4 columns. Missing:
- `last_synced_at INTEGER NOT NULL` (line 284)

**Replacement:** Add `last_synced_at INTEGER NOT NULL` to the SQL block at line 2690.

---

## Finding 3 — `proxy_request_logs` table schema missing 2 cache cost columns

**Note location:** §3.7, "proxy_request_logs 表" (lines 2713–2738)

**Claim:** The table goes directly from `output_cost_usd` to `total_cost_usd`.

**Verdict:** stale

**Severity:** medium — these are cost accounting columns; omitting them misleads anyone investigating billing/usage accuracy.

**Source evidence:** `src-tauri/src/database/schema.rs:189–190`

The actual schema has 2 additional columns between `output_cost_usd` and `total_cost_usd`:
- `cache_read_cost_usd TEXT NOT NULL DEFAULT '0'` (line 190)
- `cache_creation_cost_usd TEXT NOT NULL DEFAULT '0'` (line 190)

**Replacement:** Add these 2 columns to the SQL block after `output_cost_usd` at line 2725.

---

## Finding 4 — `init()` code block uses `?` for cleanup but actual code uses non-fatal error handling

**Note location:** §3.7, "Database::init()" code block (lines 2829–2844)

**Claim:** The code block shows:
```rust
db.cleanup_old_stream_check_logs(7)?;  // 清理 7 天前的日志
db.rollup_and_prune(30)?;  // 滚动合并 30 天前的数据
```

**Verdict:** wrong

**Severity:** high — this is an API behavior claim. If a maintainer copies this pattern, they'd make startup fail on a non-critical cleanup error, which is the opposite of the actual design.

**Source evidence:** `src-tauri/src/database/mod.rs:143–149`

Actual code:
```rust
if let Err(e) = db.cleanup_old_stream_check_logs(7) {
    log::warn!("Startup stream_check_logs cleanup failed: {e}");
}
if let Err(e) = db.rollup_and_prune(30) {
    log::warn!("Startup rollup_and_prune failed: {e}");
}
```

**Replacement:** Replace `?` with the `if let Err(e)` pattern in the code block. Add a note: "Non-critical cleanup steps use `if let Err(e)` to avoid failing startup on non-essential operations."

---

## Finding 5 — `init()` code block and flow list missing `ensure_incremental_auto_vacuum()` step

**Note location:** §3.7, "Database::init()" code block (lines 2829–2844) and numbered flow (lines 2846–2858)

**Claim:** The init flow goes directly from `apply_schema_migrations()` to `ensure_model_pricing_seeded()`.

**Verdict:** stale

**Severity:** medium — missing a step that affects disk space management behavior.

**Source evidence:** `src-tauri/src/database/mod.rs:138–140`

Between `apply_schema_migrations()` (line 137) and `ensure_model_pricing_seeded()` (line 141), the actual code calls:
```rust
if let Err(e) = db.ensure_incremental_auto_vacuum() {
    log::warn!("Failed to ensure incremental auto-vacuum: {e}");
}
```

This step is absent from both the code block and the numbered flow list.

**Replacement:** Add `ensure_incremental_auto_vacuum()` to the code block after `apply_schema_migrations()`, and add a numbered step between 9 and 10 in the flow list.

---

## Finding 6 — `init()` code block missing pre-migration backup logic

**Note location:** §3.7, "Database::init()" code block (lines 2829–2844)

**Claim:** The code block jumps from `create_tables()` to `apply_schema_migrations()`.

**Verdict:** stale

**Severity:** medium — the backup logic is a critical safety feature for database upgrades.

**Source evidence:** `src-tauri/src/database/mod.rs:122–135`

Between `create_tables()` (line 120) and `apply_schema_migrations()` (line 137), the actual code includes:
```rust
// Pre-migration backup: only when upgrading from an existing database
let conn = lock_conn!(db.conn);
let version = Self::get_user_version(&conn)?;
drop(conn);
if version > 0 && version < SCHEMA_VERSION {
    if let Err(e) = db.backup_database_file() {
        log::warn!("Pre-migration backup failed, continuing migration: {e}");
    }
}
```

**Replacement:** Add this logic to the code block between `create_tables()` and `apply_schema_migrations()`.

---

## Finding 7 — `mod.rs` size claim says 1.1KB, actual is 8.9KB

**Note location:** §3.7, "模块结构" (line 2861)

**Claim:** `mod.rs（1.1KB）`

**Verdict:** wrong

**Severity:** medium — off by 8×, misleading for anyone sizing the module.

**Source evidence:** `du -b src-tauri/src/database/mod.rs` → 9128 bytes (8.9KB), 271 lines.

**Replacement:** `mod.rs（8.9KB，271 行）`

---

## Finding 8 — `migration.rs` size claim says 28.3KB, actual is 9.2KB

**Note location:** §3.7, "模块结构" (line 2864)

**Claim:** `migration.rs（28.3KB）`

**Verdict:** wrong

**Severity:** medium — off by 3×. The table at line 2993 correctly states 9.2KB, so this is an internal contradiction.

**Source evidence:** `du -b src-tauri/src/database/migration.rs` → 9468 bytes (9.2KB), 245 lines.

**Replacement:** `migration.rs（9.2KB，245 行）`

---

## Finding 9 — `schema.rs` size claim says 11.7KB, actual is 77.8KB

**Note location:** §3.7, "模块结构" (line 2862)

**Claim:** `schema.rs（11.7KB）`

**Verdict:** wrong

**Severity:** medium — off by 6.6×. The table at line 2989 correctly states 77.8KB. This contradicts itself.

**Source evidence:** `du -b src-tauri/src/database/schema.rs` → 79691 bytes (77.8KB), 2050 lines.

**Replacement:** `schema.rs（77.8KB，2050 行）`

---

## Finding 10 — DAO `proxy.rs` size claim says 7.5KB, actual is 33.9KB

**Note location:** §3.8, bullet point at line 2950

**Claim:** `proxy.rs（7.5KB）是最大的 DAO 文件`

**Verdict:** wrong

**Severity:** medium — the table at line 2938 correctly states 33.9KB. The bullet point contradicts its own table.

**Source evidence:** `du -b src-tauri/src/database/dao/proxy.rs` → 34715 bytes (33.9KB), 952 lines.

**Replacement:** `proxy.rs（33.9KB，952 行）是最大的 DAO 文件`

---

## Finding 11 — DAO `settings.rs` size claim says 28.9KB, actual is 11.9KB

**Note location:** §3.8, bullet point at line 2953

**Claim:** `settings.rs（28.9KB）`

**Verdict:** wrong

**Severity:** medium — off by 2.4×. Table at line 2941 correctly states 11.9KB.

**Source evidence:** `du -b src-tauri/src/database/dao/settings.rs` → 12235 bytes (11.9KB), 327 lines.

**Replacement:** `settings.rs（11.9KB，327 行）`

---

## Finding 12 — DAO `mcp.rs` size claim says 19.6KB, actual is 4.1KB

**Note location:** §3.8, bullet point at line 2956

**Claim:** `mcp.rs（19.6KB）`

**Verdict:** wrong

**Severity:** medium — off by 4.8×. Table at line 2943 correctly states 4.1KB.

**Source evidence:** `du -b src-tauri/src/database/dao/mcp.rs` → 4231 bytes (4.1KB), 106 lines.

**Replacement:** `mcp.rs（4.1KB，106 行）`

---

## Finding 13 — DAO `stream_check.rs` size claim says 10.9KB, actual is 2.7KB

**Note location:** §3.8, bullet point at line 2959

**Claim:** `stream_check.rs（10.9KB）`

**Verdict:** wrong

**Severity:** medium — off by 4×. Table at line 2947 correctly states 2.7KB.

**Source evidence:** `du -b src-tauri/src/database/dao/stream_check.rs` → 2778 bytes (2.7KB), 74 lines.

**Replacement:** `stream_check.rs（2.7KB，74 行）`

---

## Finding 14 — DAO module names list has wrong names and missing files

**Note location:** §3.8, line 2999

**Claim:** "dao/ 子目录包含 12 个 DAO 模块：providers、settings、mcp_servers、prompts、skills、proxy_config、proxy_request_logs、session_usage、subscription、usage_cache、universal_providers、stream_check"

**Verdict:** wrong

**Severity:** high — the names are wrong and would confuse someone navigating the codebase. Several listed modules don't exist; several real modules are missing.

**Source evidence:** `ls src-tauri/src/database/dao/` lists 12 files (including mod.rs):

Actual files (excluding mod.rs): `failover.rs`, `mcp.rs`, `prompts.rs`, `providers.rs`, `providers_seed.rs`, `proxy.rs`, `settings.rs`, `skills.rs`, `stream_check.rs`, `universal_providers.rs`, `usage_rollup.rs`

Errors in the notes:
- `mcp_servers` → should be `mcp`
- `proxy_config` and `proxy_request_logs` → both are in a single `proxy.rs` file (one module, not two)
- `session_usage` → does not exist in dao/ (exists in services/)
- `subscription` → does not exist in dao/
- `usage_cache` → does not exist in dao/
- Missing: `failover`, `providers_seed`, `usage_rollup`

**Replacement:** "dao/ 子目录包含 11 个 DAO 模块：providers、settings、mcp、prompts、skills、proxy（代理配置 + 请求日志）、failover、providers_seed、usage_rollup、stream_check、universal_providers"

---

## Finding 15 — `commands/mod.rs` submodule count says 33, actual is 31

**Note location:** §3.8, line 2982

**Claim:** "33 个子模块声明（commands/mod.rs:3-34）"

**Verdict:** wrong

**Severity:** low — minor count error.

**Source evidence:** `grep -c '^mod \|^pub mod ' src-tauri/src/commands/mod.rs` → 31. Lines 3–34 contain 31 `mod`/`pub mod` declarations (line 30 is blank).

**Replacement:** "31 个子模块声明（commands/mod.rs:3-34）"

---

## Finding 16 — Services table (§3.8) severely incomplete and has wrong byte sizes

**Note location:** §3.8, lines 2898–2900 and 3630–3651

**Claim:** The first table shows only 1 entry (provider/mod.rs). The second table (lines 3630–3651) lists ~21 services modules with byte sizes.

**Verdict:** wrong

**Severity:** high — the sizes in the second table are wildly inaccurate for most entries (off by 30–100×), and 3 modules are entirely missing.

**Source evidence:** `ls -la src-tauri/src/services/`

| Notes claim | Actual size | Error magnitude |
|---|---|---|
| subscription.rs 1.3KB | 41.1KB | 31× too small |
| coding_plan.rs 607B | 21.9KB | 37× too small |
| env_checker.rs 168B | 5.9KB | 35× too small |
| env_manager.rs 240B | 8.5KB | 35× too small |
| webdav.rs 554B | 18.0KB | 32× too small |
| webdav_sync.rs 884B | 29.0KB | 33× too small |
| webdav_auto_sync.rs 274B | 8.0KB | 29× too small |
| session_usage.rs 682B | 22.6KB | 33× too small |
| session_usage_codex.rs 787B | 25.6KB | 33× too small |
| session_usage_gemini.rs 494B | 16.1KB | 33× too small |
| omo.rs 560B | 19.1KB | 34× too small |

Missing modules (not in either table):
- `codex_oauth_models.rs` (5.6KB)
- `sql_helpers.rs` (5.3KB)
- `usage_cache.rs` (4.4KB)

**Replacement:** Rebuild the services table with correct sizes from `ls -la src-tauri/src/services/` and include all 25 modules.

---

## Finding 17 — Database directory file sizes in "模块结构" contradict the table at lines 2986–2994

**Note location:** §3.7, "模块结构" block (lines 2860–2864) vs table (lines 2986–2994)

**Claim:** The inline list and the table give different sizes for the same files.

**Verdict:** wrong

**Severity:** medium — the table (lines 2986–2994) is correct; the inline list (lines 2860–2864) has wrong sizes for mod.rs, schema.rs, and migration.rs.

**Source evidence:**
| File | Inline list (line 286x) | Table (line 299x) | Actual |
|---|---|---|---|
| mod.rs | 1.1KB | 8.9KB | 8.9KB ✓ table |
| schema.rs | 11.7KB | 77.8KB | 77.8KB ✓ table |
| migration.rs | 28.3KB | 9.2KB | 9.2KB ✓ table |

**Replacement:** Make the inline list match the table values (which are correct).

---

## Finding 18 — `failover_queue` migration claim omits `DROP INDEX` step

**Note location:** §3.7, "failover_queue 重构" (lines 2589–2593)

**Claim:** "迁移时删除旧表和索引（`DROP TABLE IF EXISTS failover_queue`）"

**Verdict:** ambiguous

**Severity:** low — the note says "删除旧表和索引" but only shows the `DROP TABLE` statement. The actual migration also drops the index explicitly before dropping the table.

**Source evidence:** `src-tauri/src/database/schema.rs:345–346`

```rust
let _ = conn.execute("DROP INDEX IF EXISTS idx_failover_queue_order", []);
let _ = conn.execute("DROP TABLE IF EXISTS failover_queue", []);
```

**Replacement:** "迁移时先删除旧索引 `idx_failover_queue_order`，再删除旧表（`DROP TABLE IF EXISTS failover_queue`）"

---

## Finding 19 — proxy_request_logs indexes list incomplete

**Note location:** §3.7, "索引" section (lines 2740–2745)

**Claim:** Lists 5 indexes for `proxy_request_logs`.

**Verdict:** stale

**Severity:** low — there is an additional conditional index created by `create_request_logs_usage_indexes_if_supported()` (schema.rs:217, defined at line 1920).

**Source evidence:** `src-tauri/src/database/schema.rs:217`

**Replacement:** Add a note: "另有条件索引通过 `create_request_logs_usage_indexes_if_supported()` 创建（`schema.rs:1920`）"

---

## Finding 20 — Services table at §3.8 (line 2898) shows only 1 of 25 entries

**Note location:** §3.8, lines 2898–2900

**Claim:** The table header says "25 个子模块" but only lists `provider/mod.rs`.

**Verdict:** wrong

**Severity:** medium — the full table appears later (lines 3630–3651) but without a header, and that table has wrong sizes (see Finding 16).

**Source evidence:** `src-tauri/src/services/mod.rs` has exactly 25 `pub mod` declarations.

**Replacement:** Merge the two tables into one complete table at line 2898, with correct sizes and all 25 entries.

---

## Summary

| Category | Count |
|---|---|
| Schema column omissions (high) | 3 |
| API behavior / error handling (high) | 1 |
| Wrong DAO module names (high) | 1 |
| Wrong services sizes (high) | 1 |
| File size errors (medium) | 7 |
| Missing init steps (medium) | 2 |
| Count errors (low) | 2 |
| Ambiguous/stale minor claims (low) | 2 |
| **Total** | **20** |

All findings verified independently against source code. No reliance on other agents' conclusions.
