# Chapter 3 (§3.1–§3.5) Core Models — Skeptic Findings

Scope: Sections 3.1 (config.rs), 3.2 (error.rs), 3.3 (app_config.rs), 3.4 (provider.rs), 3.5 (settings.rs).
Each finding verified against source independently.

---

## Finding 1: AppError variant line numbers are systematically off by 1

**Note location:** §3.2, "AppError 枚举（error.rs:7-63）" table (notes line 472)

**Verdict:** wrong

The notes count the `#[error("...")]` attribute line as the variant location, but the variant keyword is on the next line. The first 11 variants are affected; the last 5 are correct (they happen to use the same attribute-then-variant pattern, but the notes correctly count those).

| Variant | Notes | Actual source |
|---------|-------|---------------|
| `Config(String)` | :8 | :9 |
| `InvalidInput(String)` | :10 | :11 |
| `Io { path, source }` | :12 | :13 |
| `IoContext { context, source }` | :18 | :19 |
| `Json { path, source }` | :24 | :25 |
| `JsonSerialize { source }` | :30 | :31 |
| `Toml { path, source }` | :35 | :36 |
| `Lock(String)` | :41 | :42 |
| `McpValidation(String)` | :43 | :44 |
| `Message(String)` | :45 | :46 |
| `HttpStatus { status, body }` | :47 | :48 |
| `Localized { key, zh, en }` | :50 | :50 ✓ |
| `Database(String)` | :56 | :56 ✓ |
| `OmoConfigNotFound` | :58 | :58 ✓ |
| `AllProvidersCircuitOpen` | :60 | :60 ✓ |
| `NoProvidersConfigured` | :62 | :62 ✓ |

**Source evidence:** `src-tauri/src/error.rs:6–63`

**Severity:** medium — systematic offset makes line-number navigation unreliable for 11 of 16 variants.

**Replacement:** Correct lines: 8→9, 10→11, 12→13, 18→19, 24→25, 30→31, 35→36, 41→42, 43→44, 45→46, 47→48.

---

## Finding 2: UsageScript struct is missing 6 of 13 fields

**Note location:** §3.4, "UsageScript（provider.rs:121）" (notes line 1336)

**Verdict:** wrong

The notes show 6 fields (`enabled`, `language`, `code`, `timeout`, `api_key`, `base_url`). The actual struct has 13 fields.

**Missing fields:**
- `access_token: Option<String>` (provider.rs:137, "访问令牌，NewAPI 模板使用")
- `user_id: Option<String>` (provider.rs:141, "用户ID，NewAPI 模板使用")
- `template_type: Option<String>` (provider.rs:145, "模板类型，后端判断验证规则")
- `auto_query_interval: Option<u64>` (provider.rs:149, "自动查询间隔，分钟")
- `coding_plan_provider: Option<String>` (provider.rs:153, "Coding Plan 供应商标识")

**Source evidence:** `src-tauri/src/provider.rs:121–155`

**Severity:** medium — hides NewAPI integration and Coding Plan features from maintainers reading the notes.

**Replacement:** Add all 6 missing fields to the UsageScript code block.

---

## Finding 3: Section 3.5 DAO bullet list has fabricated file sizes (contradicts its own table)

**Note location:** §3.5, bullet list at notes lines 649–659

**Verdict:** wrong

The DAO table at lines 635–648 has correct file sizes. The bullet list immediately below it has wrong sizes for 5 of 12 files:

| File | Table (correct) | Bullet list (wrong) | Actual (`stat`) |
|------|----------------|---------------------|-----------------|
| `proxy.rs` | 33.9KB | **7.5KB** | 33.9KB (34715 bytes) |
| `settings.rs` | 11.9KB | **28.9KB** | 11.9KB (12235 bytes) |
| `failover.rs` | 4.8KB | **5.5KB** | 4.8KB (4920 bytes) |
| `mcp.rs` | 4.1KB | **19.6KB** | 4.1KB (4231 bytes) |
| `stream_check.rs` | 2.7KB | **10.9KB** | 2.7KB (2778 bytes) |

The `proxy.rs` bullet claims 7.5KB when the file is 33.9KB — a 4.5× understatement. The `settings.rs` bullet claims 28.9KB when the file is 11.9KB — a 2.4× overstatement.

**Source evidence:** `stat --format='%s %n' src-tauri/src/database/dao/{proxy,settings,failover,mcp,stream_check}.rs`

**Severity:** high — the bullet list and table are in the same section and directly contradict each other. A maintainer would not know which to trust.

**Replacement:** Delete the bullet list entirely (the table above it is correct and sufficient), or correct the 5 wrong sizes to match the table.

---

## Finding 4: settings.rs section heading has wrong line count and misleading file size

**Note location:** §3.5 heading (notes line 600): "settings.rs — 设置管理（28.8KB，877 行）"

**Verdict:** ambiguous

- The root `settings.rs` is 876 lines (`wc -l`), not 877.
- The "28.8KB" size does not match the root file. The root file is much smaller.
- The section references the root `settings.rs` structs (`AppSettings`, `SETTINGS_STORE`), but the size figure appears to come from `database/dao/settings.rs` (which is 11.9KB, not 28.8KB either).

**Source evidence:** `wc -l src-tauri/src/settings.rs` → 876

**Severity:** low — the heading's line count is off by 1, and the size attribution is confusing but does not affect the struct definitions shown.

**Replacement:** Change heading to "settings.rs — 设置管理（876 行）" and remove or clarify the 28.8KB figure.

---

## Finding 5: AppSettings field group label "设备级 UI 设置" includes non-UI fields

**Note location:** §3.5, "AppSettings 完整字段分组" (notes line 2520–2521)

**Verdict:** stale

The notes claim group 1 ("设备级 UI 设置") covers `settings.rs:212-256`. The line range is correct, but the label is misleading:
- `enable_failover_toggle` (line 245) is a feature toggle, not a UI setting
- `language` (line 256) is a locale setting, not a UI setting

**Source evidence:** `src-tauri/src/settings.rs:212–256`

**Severity:** low — conceptual grouping inaccuracy, does not affect code correctness.

**Replacement:** Rename group to "设备级 UI 与功能设置" or split into sub-groups.

---

## Finding 6: §3.1 config.rs — all claims verified OK

**Note location:** §3.1

**Verdict:** ok

All function line numbers verified:
- `get_claude_config_dir()` → config.rs:37 ✓
- `get_claude_settings_path()` → config.rs:74 ✓
- `get_app_config_dir()` → config.rs:90 ✓
- `read_json_file()` → config.rs:153 ✓
- `write_json_file()` → config.rs:181 ✓
- `write_text_file()` → config.rs:196 ✓
- `atomic_write()` → config.rs:204 ✓
- `sort_json_keys()` → config.rs:164 ✓
- `copy_file()` → config.rs:394 ✓
- `delete_file()` → config.rs:403 ✓

File size (13.9KB, 424 lines) confirmed by `wc -l`.

**Source evidence:** `grep -n 'fn' src-tauri/src/config.rs`, `wc -l src-tauri/src/config.rs`

---

## Finding 7: §3.3 AppType enum and methods — all claims verified OK

**Note location:** §3.3

**Verdict:** ok

- 7 variants: Claude, ClaudeDesktop, Codex, Gemini, OpenCode, OpenClaw, Hermes ✓
- `is_additive_mode()` at app_config.rs:373, returns true for OpenCode | OpenClaw | Hermes ✓
- `as_str()` at app_config.rs:357 ✓
- `all()` at app_config.rs:381 ✓
- `FromStr` at app_config.rs:395, aliases: "claude-desktop" | "claude_desktop" | "claudedesktop" ✓
- Switch mode (4): Claude, ClaudeDesktop, Codex, Gemini ✓
- Additive mode (3): OpenCode, OpenClaw, Hermes ✓

**Source evidence:** `src-tauri/src/app_config.rs:339–415`

---

## Finding 8: §3.3 McpApps, SkillApps, and other app_config types — all claims verified OK

**Note location:** §3.3

**Verdict:** ok

- `McpApps` at app_config.rs:9, 5 fields (claude, codex, gemini, opencode, hermes) ✓
- `SkillApps` at app_config.rs:78, 5 fields ✓
- `CommonConfigSnippets` at app_config.rs:419 ✓
- `MultiAppConfig` at app_config.rs:469 ✓
- `McpServer` at app_config.rs:222 ✓
- `McpRoot` at app_config.rs:254 ✓
- `InstalledSkill` at app_config.rs:169 ✓

**Source evidence:** `src-tauri/src/app_config.rs` (verified each struct location)

---

## Finding 9: §3.4 Provider struct — all claims verified OK

**Note location:** §3.4

**Verdict:** ok

All 12 fields match source: id, name, settings_config (serde rename "settingsConfig"), website_url, category, created_at, sort_index, notes, meta, icon, icon_color, in_failover_queue.

Methods verified:
- `with_id()` at provider.rs:47 ✓
- `is_codex_oauth()` at provider.rs:69 ✓
- `is_github_copilot()` at provider.rs:73 ✓
- `uses_managed_account_auth()` at provider.rs:78 ✓
- `ProviderManager` at provider.rs:114 ✓

**Source evidence:** `src-tauri/src/provider.rs:10–117`

---

## Finding 10: §3.5 settings mechanisms — all claims verified OK

**Note location:** §3.5

**Verdict:** ok

- `SETTINGS_STORE: OnceLock<RwLock<AppSettings>>` at settings.rs:519 ✓
- `settings_store()` at settings.rs:521 ✓
- `mutate_settings(mutator)` at settings.rs:574, private fn, param named `mutator` ✓
- `unwrap_or_else` for lock poison at settings.rs:578 ✓
- `SwitchLockManager` at proxy/switch_lock.rs:14 ✓
- `lock_for_app()` at switch_lock.rs:26 ✓
- `ProxyService` at services/proxy.rs:55 ✓
- `HotSwitchOutcome` at services/proxy.rs:64 ✓

**Source evidence:** `src-tauri/src/settings.rs:519–587`, `src-tauri/src/proxy/switch_lock.rs:14,26`, `src-tauri/src/services/proxy.rs:55,64`

---

## Summary

| # | Section | Finding | Verdict | Severity |
|---|---------|---------|---------|----------|
| 1 | §3.2 | AppError variant lines off by 1 (11 of 16) | wrong | medium |
| 2 | §3.4 | UsageScript missing 6 of 13 fields | wrong | medium |
| 3 | §3.5 | DAO bullet list has 5 fabricated file sizes (contradicts own table) | wrong | **high** |
| 4 | §3.5 | settings.rs heading: 877→876 lines, misleading size | ambiguous | low |
| 5 | §3.5 | AppSettings group label "UI 设置" covers non-UI fields | stale | low |
| 6 | §3.1 | config.rs — all verified | ok | — |
| 7 | §3.3 | AppType enum — all verified | ok | — |
| 8 | §3.3 | McpApps/SkillApps/other types — all verified | ok | — |
| 9 | §3.4 | Provider struct — all verified | ok | — |
| 10 | §3.5 | settings mechanisms — all verified | ok | — |
