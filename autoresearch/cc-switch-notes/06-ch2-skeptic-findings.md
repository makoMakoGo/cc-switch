# Chapter 2 Skeptic Findings — Tauri/Rust 基础速查

Scope: 第 2 章 (lines 267–403). Every repo-specific claim verified against source code.

---

## Finding 1 — serde alias example does not exist in codebase

- **note location**: § 2.4 "serde 属性速查", line 389
- **quoted claim**: `#[serde(alias = "claudeDesktop")]           // 支持多个别名`
- **verdict**: wrong
- **severity**: medium
- **source evidence**: No `alias = "claudeDesktop"` anywhere in `src-tauri/src/`. The only `#[serde(alias = …)]` in the project is `#[serde(default, alias = "reasoning_content")]` at `src-tauri/src/proxy/providers/streaming.rs:37`.
- **exact replacement**:
  ```
  #[serde(alias = "reasoning_content")]       // 支持多个别名（streaming.rs:37）
  ```

---

## All other claims — verified OK

Every other repo-specific claim in Chapter 2 was independently verified against source. All are accurate.

| Note line | Claim | Source verification |
|-----------|-------|---------------------|
| 275 | `AppState.db: Arc<Database>`（`store.rs:7`） | `src-tauri/src/store.rs:7` — `pub db: Arc<Database>` ✓ |
| 276 | `Database.conn: Mutex<Connection>`（`database/mod.rs:77`） | `src-tauri/src/database/mod.rs:77` — `pub(crate) conn: Mutex<Connection>` ✓ |
| 277 | `SETTINGS_STORE: OnceLock<RwLock<AppSettings>>`（`settings.rs:519`） | `src-tauri/src/settings.rs:519` — exact match ✓ |
| 280 | `let config = read_json_file(path)?;` pattern | `src-tauri/src/config.rs:158-160` — uses `map_err(|e| AppError::io(path, e))?` and `AppError::json(path, e)`, both constructors at `error.rs:66,73` ✓ |
| 281 | `#[tauri::command]` on commands/ functions | `src-tauri/src/commands/provider.rs:21` and throughout ✓ |
| 282 | `#[derive(Serialize, Deserialize)]` widespread | Verified across settings.rs, app_config.rs, provider.rs, etc. ✓ |
| 283 | `tokio::spawn` for async tasks | `src-tauri/src/proxy/forwarder.rs:192` — exact code match ✓ |
| 284 | `thiserror` auto-derives Error; `AppError` | `Cargo.toml:66` — `thiserror = "2.0"`. `error.rs:4,6,7` — use + derive + enum ✓ |
| 285 | `CircuitBreakerConfig::from(&AppProxyConfig)`（`circuit_breaker.rs:51`） | `src-tauri/src/proxy/circuit_breaker.rs:51-61` ✓ |
| 286 | `#[serde(rename_all)]` for camelCase | `settings.rs:13`, `app_config.rs:168`, `provider.rs:37`, etc. ✓ |
| 287 | `matches!` in `is_additive_mode()`（`app_config.rs:373`） | `src-tauri/src/app_config.rs:373-377` — exact match ✓ |
| 293 | Lifetime `'a` only in `tauri::State<'_, AppState>` | Commands use `State<'_, AppState>`. No explicit `<'a>` fn signatures found ✓ |
| 294 | `dyn Trait` used rarely | No `dyn Trait` matches found via AST search ✓ |
| 295 | `unsafe` not used in project | Only hit is a test fn name substring, not actual `unsafe` blocks ✓ |
| 297 | Only `lock_conn!` custom macro（`database/mod.rs:61`） | AST search found exactly one `macro_rules!` ✓ |
| 305 | `state: tauri::State<'_, AppState>` injection | `commands/provider.rs:2,23` — import + usage ✓ |
| 326 | 9 plugins listed | All 9 registered in `lib.rs:211-336` ✓ |
| 333-337 | Read config + map_err pattern | `config.rs:158-160` — exact match ✓ |
| 350-356 | `atomic_write`（`config.rs:204`） | `config.rs:204` — `pub fn atomic_write(path: &Path, data: &[u8]) -> Result<(), AppError>` ✓ |
| 358-367 | `tokio::spawn` example（`forwarder.rs:192`） | `forwarder.rs:192-201` — exact code match ✓ |
| 369-378 | `lock_conn!` macro body（`database/mod.rs:61`） | `database/mod.rs:61-67` — exact code match ✓ |
| 384-388 | serde derive, rename_all, skip_serializing_if, default, rename | All verified in codebase ✓ |
| 574-588 | `mutate_settings` private, param `mutator` | `settings.rs:574` — `fn mutate_settings<F>(mutator: F)` ✓ |
