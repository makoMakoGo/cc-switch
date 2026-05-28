# Chapter 3 Core API Findings — Fact Check

Scope: sections 3.1–3.5 (config.rs, error.rs, app_config.rs, provider.rs, settings.rs).
All line numbers verified against `wc -l` and direct source reads on 2026-05-28.

---

## Finding 1 — UsageScript struct missing 5 fields

- **Location**: §3.4 provider.rs, "Provider 方法" block after Provider struct
- **Claim**:
  ```rust
  pub struct UsageScript {  // provider.rs:121
      pub enabled: bool,
      pub language: String,
      pub code: String,
      pub timeout: Option<u64>,
      pub api_key: Option<String>,
      pub base_url: Option<String>,
  }
  ```
- **Verdict**: wrong
- **Source evidence**: `src-tauri/src/provider.rs:121-155` — actual struct has 11 fields, not 6:
  ```rust
  pub struct UsageScript {
      pub enabled: bool,
      pub language: String,
      pub code: String,
      pub timeout: Option<u64>,
      pub api_key: Option<String>,           // #[serde(rename = "apiKey")]
      pub base_url: Option<String>,          // #[serde(rename = "baseUrl")]
      pub access_token: Option<String>,      // ← MISSING in notes
      pub user_id: Option<String>,           // ← MISSING in notes
      pub template_type: Option<String>,     // ← MISSING in notes
      pub auto_query_interval: Option<u64>,  // ← MISSING in notes
      pub coding_plan_provider: Option<String>, // ← MISSING in notes
  }
  ```
- **Exact replacement**: Add the 5 missing fields to the notes block:
  ```rust
  pub access_token: Option<String>,   // 用量查询专用访问令牌（NewAPI 模板使用）
  pub user_id: Option<String>,        // 用量查询专用用户 ID（NewAPI 模板使用）
  pub template_type: Option<String>,  // 模板类型（后端验证规则）
  pub auto_query_interval: Option<u64>, // 自动查询间隔（分钟，0 = 禁用）
  pub coding_plan_provider: Option<String>, // Coding Plan 供应商标识
  ```
- **Severity**: high — developers reading the notes will miss half the fields when working with usage scripts.

---

## Finding 2 — AppSettings struct severely truncated (10/38 fields shown)

- **Location**: §3.5 settings.rs, "AppSettings 结构体（`settings.rs:211`）— 主要字段"
- **Claim**: Shows 10 fields as "主要字段"
- **Verdict**: wrong
- **Source evidence**: `src-tauri/src/settings.rs:211-334` — actual struct has 38 fields. The notes omit 28 fields:
  - `use_app_window_controls: bool`
  - `enable_claude_plugin_integration: bool`
  - `skip_claude_onboarding: bool`
  - `launch_on_startup: bool`
  - `proxy_confirmed: Option<bool>`
  - `usage_confirmed: Option<bool>`
  - `stream_check_confirmed: Option<bool>`
  - `enable_failover_toggle: bool`
  - `failover_confirmed: Option<bool>`
  - `first_run_notice_confirmed: Option<bool>`
  - `common_config_confirmed: Option<bool>`
  - `codex_config_dir: Option<String>`
  - `gemini_config_dir: Option<String>`
  - `opencode_config_dir: Option<String>`
  - `openclaw_config_dir: Option<String>`
  - `hermes_config_dir: Option<String>`
  - `current_provider_claude_desktop: Option<String>`
  - `current_provider_codex: Option<String>`
  - `current_provider_gemini: Option<String>`
  - `current_provider_opencode: Option<String>`
  - `current_provider_openclaw: Option<String>`
  - `current_provider_hermes: Option<String>`
  - `skill_storage_location: SkillStorageLocation`
  - `webdav_backup: Option<serde_json::Value>`
  - `backup_interval_hours: Option<u32>`
  - `backup_retain_count: Option<u32>`
  - `preferred_terminal: Option<String>`
  - `local_migrations: Option<LocalMigrations>`
- **Exact replacement**: Replace the truncated struct with the full list, or mark it explicitly as "selected fields only" and add the omitted fields in a second block. The current phrasing "主要字段" implies these are the key ones, but 28 missing fields is misleading.
- **Severity**: high — anyone implementing settings features will miss critical fields.

---

## Finding 3 — AppSettings `webdav` field name and type are wrong

- **Location**: §3.5 settings.rs, AppSettings struct block
- **Claim**: `pub webdav: WebDavSyncSettings, // WebDAV 同步设置`
- **Verdict**: wrong
- **Source evidence**: `src-tauri/src/settings.rs:308-309`:
  ```rust
  #[serde(default, skip_serializing_if = "Option::is_none")]
  pub webdav_sync: Option<WebDavSyncSettings>,
  ```
  Two errors: field name is `webdav_sync` (not `webdav`), and type is `Option<WebDavSyncSettings>` (not `WebDavSyncSettings`).
- **Exact replacement**: `pub webdav_sync: Option<WebDavSyncSettings>, // WebDAV 同步设置`
- **Severity**: high — wrong field name will cause compile errors if anyone copies the notes.

---

## Finding 4 — settings.rs line count off by 1

- **Location**: §3.5 heading
- **Claim**: "settings.rs — 设置管理（28.8KB，877 行）"
- **Verdict**: stale
- **Source evidence**: `wc -l src-tauri/src/settings.rs` → 876 lines. File size is 28.9KB (not 28.8KB).
- **Exact replacement**: "settings.rs — 设置管理（28.9KB，876 行）"
- **Severity**: low — off-by-one in line count.

---

## Finding 5 — config.rs file size slightly off

- **Location**: §3.1 heading
- **Claim**: "config.rs — 路径解析和文件 I/O（13.9KB，424 行）"
- **Verdict**: stale
- **Source evidence**: `ls -la src-tauri/src/config.rs` → 14.0KB. Line count 424 is correct.
- **Exact replacement**: "config.rs — 路径解析和文件 I/O（14.0KB，424 行）"
- **Severity**: low

---

## Finding 6 — error.rs file size slightly off

- **Location**: §3.2 heading
- **Claim**: "error.rs — 错误模型（3.4KB，146 行）"
- **Verdict**: stale
- **Source evidence**: `ls -la src-tauri/src/error.rs` → 3.5KB. Line count 146 is correct.
- **Exact replacement**: "error.rs — 错误模型（3.5KB，146 行）"
- **Severity**: low

---

## Finding 7 — provider.rs file size slightly off

- **Location**: §3.4 heading
- **Claim**: "provider.rs — 核心数据模型（40.5KB，1153 行）"
- **Verdict**: stale
- **Source evidence**: `ls -la src-tauri/src/provider.rs` → 40.6KB. Line count 1153 is correct.
- **Exact replacement**: "provider.rs — 核心数据模型（40.6KB，1153 行）"
- **Severity**: low

---

## Verified OK (spot-checked)

| Claim | Source | Status |
|-------|--------|--------|
| `AppError` enum at `error.rs:6` (derive) / `:7` (enum) | `error.rs:6-63` | ✓ |
| All 16 AppError variant names and line numbers | `error.rs:7-63` | ✓ |
| `Localized { key: &'static str, zh, en }` | `error.rs:50-54` | ✓ |
| `From<PoisonError<T>>` at `:96`, `From<rusqlite::Error>` at `:102` | `error.rs:96,102` | ✓ |
| `impl Serialize` at `:114` | `error.rs:114` | ✓ |
| `get_home_dir()` supports `CC_SWITCH_TEST_HOME` | `config.rs:22-34` | ✓ |
| `get_claude_config_dir()` at `:37` | `config.rs:37` | ✓ |
| `get_claude_settings_path()` at `:74` | `config.rs:74` | ✓ |
| `get_app_config_dir()` at `:90` | `config.rs:90` | ✓ |
| `read_json_file` at `:153`, `write_json_file` at `:181` | `config.rs:153,181` | ✓ |
| `atomic_write` at `:204`, `write_text_file` at `:196` | `config.rs:204,196` | ✓ |
| `copy_file` at `:394`, `delete_file` at `:403` | `config.rs:394,403` | ✓ |
| `sort_json_keys` at `:164` | `config.rs:164` | ✓ |
| `AppType` enum at `app_config.rs:341` with 7 variants | `app_config.rs:341-354` | ✓ |
| `AppType::as_str()` at `:357`, `is_additive_mode()` at `:373` | `app_config.rs:357,373` | ✓ |
| `AppType::all()` at `:381`, `FromStr` at `:395` | `app_config.rs:381,395` | ✓ |
| `McpApps` at `:9`, `SkillApps` at `:78` | `app_config.rs:9,78` | ✓ |
| `InstalledSkill` at `:169`, `McpServer` at `:222` | `app_config.rs:169,222` | ✓ |
| `McpRoot` at `:254`, `PromptConfig` at `:304`, `PromptRoot` at `:311` | `app_config.rs:254,304,311` | ✓ |
| `CommonConfigSnippets` at `:419`, `MultiAppConfig` at `:469` | `app_config.rs:419,469` | ✓ |
| `Provider` struct at `provider.rs:10-43` (all fields match) | `provider.rs:10-43` | ✓ |
| `ProviderManager` at `:114`, `UsageScript` at `:121` | `provider.rs:114,121` | ✓ |
| `CustomEndpoint` at `settings.rs:14`, `VisibleApps` at `:28` | `settings.rs:14,28` | ✓ |
| `WebDavSyncStatus` at `:82`, `LocalMigrations` at `:184` | `settings.rs:82,184` | ✓ |
| `SETTINGS_STORE` at `:519`, `settings_store()` at `:521` | `settings.rs:519,521` | ✓ |
| `mutate_settings(mutator)` at `:574` (private, param name `mutator`) | `settings.rs:574` | ✓ |
| Line counts for config.rs (424), error.rs (146), app_config.rs (1183), provider.rs (1153) | `wc -l` | ✓ |
