# Chapter 6 Evidence Findings: AI Slop 特征模式识别

Every claim in 第 6 章 (lines 5093–5191) verified against source code. 28 findings total.

---

## Finding 1 — lib.rs mod declaration count

**Note location**: §6.4 具体案例清单 — `lib.rs:1-36` | "34 个 mod 声明"

**Verdict**: ok

**Source evidence**: `grep -c "^mod \|^pub mod " src-tauri/src/lib.rs` → 34. All 34 declarations fall within lines 1–36 (lines 1–33, blank at 34, lines 35–36). Count is exact.

**Severity**: no issue

---

## Finding 2 — lib.rs line count

**Note location**: §6.1 table, §6.4, Appendix — "lib.rs | 1825 行"

**Verdict**: ok

**Source evidence**: `wc -l src-tauri/src/lib.rs` → 1825. The `read` tool reports "of 1826" (trailing newline). 1825 content lines is the correct count.

**Severity**: no issue

---

## Finding 3 — services/proxy.rs size

**Note location**: §6.1 — "services/proxy.rs | 141.3KB (3909 行)"

**Verdict**: stale (minor)

**Source evidence**: `wc -lc` → 3909 lines, 144756 bytes. 144756/1024 = **141.36 KB**. Note says 141.3KB; ls rounds to 141.4KB. Line count exact.

**Severity**: low

---

## Finding 4 — proxy/forwarder.rs size

**Note location**: §6.1 — "proxy/forwarder.rs | 122.1KB (3100 行)"

**Verdict**: stale (minor)

**Source evidence**: `wc -lc` → 3100 lines, 125105 bytes. 125105/1024 = **122.17 KB**. Note says 122.1KB; ls rounds to 122.2KB. Line count exact.

**Severity**: low

---

## Finding 5 — claude_desktop_config.rs size in §7.2 refactoring table

**Note location**: §7.2 — "claude_desktop_config.rs（14.0KB）→ claude_desktop/ 目录"

**Verdict**: wrong

**Source evidence**: `wc -lc src-tauri/src/claude_desktop_config.rs` → 1826 lines, 62939 bytes = **61.46 KB**. The §6.1 table and Appendix correctly say 61.4KB. But §7.2 says **14.0KB** — off by ~47KB. This is a copy-paste or lookup error.

**Exact replacement**: `claude_desktop_config.rs（61.4KB）→ claude_desktop/ 目录`

**Severity**: medium (misleading file-size in refactoring section could skew effort estimates)

---

## Finding 6 — Hook line counts are systematically wrong

**Note location**: §1.3 状态管理, hooks table (lines 208–213)

**Verdict**: wrong (4 of 5 entries)

| Hook | Note claims | Actual (`wc -l`) | Delta |
|------|-------------|-------------------|-------|
| `useSettings.ts` | 512 | 505 | +7 |
| `useProviderActions.ts` | 385 | 385 | 0 ✓ |
| `useProxyStatus.ts` | 185 | 245 | −60 |
| `useDirectorySettings.ts` | 275 | 373 | −98 |
| `useDragSort.ts` | 95 | 119 | −24 |

**Source evidence**: `wc -l src/hooks/useSettings.ts src/hooks/useProviderActions.ts src/hooks/useProxyStatus.ts src/hooks/useDirectorySettings.ts src/hooks/useDragSort.ts` → 505, 385, 245, 373, 119.

**Exact replacement**:
- `useSettings.ts (512 行)` → `useSettings.ts (505 行)`
- `useProxyStatus.ts (185 行)` → `useProxyStatus.ts (245 行)`
- `useDirectorySettings.ts (275 行)` → `useDirectorySettings.ts (373 行)`
- `useDragSort.ts (95 行)` → `useDragSort.ts (119 行)`

**Severity**: medium (stale numbers could mislead refactoring estimates)

---

## Finding 7 — Query file line counts off by exactly 1

**Note location**: §1.3 状态管理, lib/query/ table (lines 215–221)

**Verdict**: wrong (all 6 entries off by exactly 1)

| File | Note claims | Actual (`wc -l`) |
|------|-------------|-------------------|
| `queries.ts` | 156 | 155 |
| `mutations.ts` | 357 | 356 |
| `proxy.ts` | 244 | 243 |
| `failover.ts` | 289 | 288 |
| `usage.ts` | 320 | 319 |
| `subscription.ts` | 64 | 63 |

**Source evidence**: `wc -l src/lib/query/*.ts` → 155, 356, 243, 288, 319, 63. Every entry is +1 in the note, consistent with counting a trailing newline.

**Exact replacement**: Subtract 1 from each: `155, 356, 243, 288, 319, 63`.

**Severity**: low (systematic off-by-one)

---

## Finding 8 — `tool_config_xxx` vs `xxx_config` naming claim is fabricated

**Note location**: §6.3 命名和组织问题 — "有的用 `tool_config_xxx`，有的用 `xxx_config`"

**Verdict**: hallucination

**Source evidence**: `grep -rn "tool_config" src-tauri/src/ --include="*.rs"` → only 2 matches, both in `proxy/providers/transform_gemini.rs:94-95`:
```rust
if let Some(tool_config) = map_tool_choice(body.get("tool_choice"))? {
    result["toolConfig"] = tool_config;
```
This is a local variable mapping to a Gemini API JSON field name — NOT a cc-switch naming convention. No function, type, or module uses `tool_config_xxx` naming. The note presents this as a naming inconsistency in cc-switch's own code, which is false.

**Exact replacement**: Remove the `tool_config_xxx` bullet entirely. Real naming inconsistencies are `read_live_settings` vs `get_custom_endpoints` vs `get_universal` in `services/provider/mod.rs`.

**Severity**: high (hallucinated code pattern presented as fact)

---

## Finding 9 — proxy_request_logs column count wrong

**Note location**: §6.3 数据库层 AI Slop — "`proxy_request_logs` 表（`schema.rs:184`）有 15 列"

**Verdict**: wrong

**Source evidence**: `src-tauri/src/database/schema.rs:184-196` defines the table with 25 columns:
1. request_id, 2. provider_id, 3. app_type, 4. model, 5. request_model, 6. input_tokens, 7. output_tokens, 8. cache_read_tokens, 9. cache_creation_tokens, 10. input_cost_usd, 11. output_cost_usd, 12. cache_read_cost_usd, 13. cache_creation_cost_usd, 14. total_cost_usd, 15. latency_ms, 16. first_token_ms, 17. duration_ms, 18. status_code, 19. error_message, 20. session_id, 21. provider_type, 22. is_streaming, 23. cost_multiplier, 24. created_at, 25. data_source

**Exact replacement**: `proxy_request_logs` 表（`schema.rs:184`）有 25 列

**Severity**: medium (significantly understates table complexity)

---

## Finding 10 — copilot_auth.rs and codex_oauth_auth.rs paths incomplete

**Note location**: §6.3 — "copilot_auth.rs（2094 行）+ codex_oauth_auth.rs（1133 行）"

**Verdict**: ambiguous

**Source evidence**: Files are at `src-tauri/src/proxy/providers/copilot_auth.rs` (2094 lines) and `src-tauri/src/proxy/providers/codex_oauth_auth.rs` (1133 lines). The note omits the `providers/` subdirectory. Line counts are exact.

**Exact replacement**: `proxy/providers/copilot_auth.rs（2094 行）+ proxy/providers/codex_oauth_auth.rs（1133 行）`

**Severity**: low (path ambiguity, line counts correct)

---

## Finding 11 — PROXY_AUTH_PLACEHOLDER path incomplete

**Note location**: §6.3 — "`PROXY_AUTH_PLACEHOLDER`（`forwarder.rs:35`）"

**Verdict**: ambiguous

**Source evidence**: `src-tauri/src/proxy/forwarder.rs:35` → `const PROXY_AUTH_PLACEHOLDER: &str = "PROXY_MANAGED";`. Line number and value correct. The companion `PROXY_TOKEN_PLACEHOLDER` at `services/proxy.rs:22` is also correct. Both resolve to `"PROXY_MANAGED"` — the claim is verified.

**Exact replacement**: `PROXY_AUTH_PLACEHOLDER（proxy/forwarder.rs:35）` — add path prefix.

**Severity**: low

---

## Finding 12 — 7 config modules count

**Note location**: §6.1 — "7 个工具的 config 模块结构几乎一样"; §6.4 — "7 个 config 模块"

**Verdict**: wrong

**Source evidence**: `ls src-tauri/src/*_config.rs` → 7 files:
1. `app_config.rs` (41.0KB) — shared config (AppType enum, McpApps, CommonConfigSnippets), NOT a tool-specific config
2. `claude_desktop_config.rs` (61.5KB) — tool-specific
3. `codex_config.rs` (66.5KB) — tool-specific
4. `gemini_config.rs` (20.4KB) — tool-specific
5. `hermes_config.rs` (69.0KB) — tool-specific
6. `openclaw_config.rs` (35.0KB) — tool-specific
7. `opencode_config.rs` (6.9KB) — tool-specific

The note says "7 个工具的 config 模块" (7 *tool* config modules). There are 6 tool-specific config modules and 1 shared config module. `app_config.rs` has a fundamentally different role — it defines `AppType`, `McpApps`, `CommonConfigSnippets`, `SkillApps`, etc. — and does NOT follow the `read → parse → modify → write` pattern the note describes.

**Exact replacement**: "6 个工具级 config 模块结构几乎一样" (or keep "7" with footnote including `app_config.rs`)

**Severity**: low (the pattern observation is correct; only the count is debatable)

---

## Finding 13 — error.rs:8 Config(String) line reference

**Note location**: §6.4 table — "error.rs:8 | Config(String) 太宽泛"

**Verdict**: ok (with nuance)

**Source evidence**: `src-tauri/src/error.rs:8` → `#[error("配置错误: {0}")]`, line 9 → `Config(String),`. The note says "error.rs:8" which points to the `#[error]` attribute. The variant definition is at line 9. The criticism is valid.

**Severity**: no issue

---

## Finding 14 — error.rs:50 Localized variant

**Note location**: §6.3 — "error.rs:50 的 Localized 变体试图解决这个问题，但不彻底"

**Verdict**: ok

**Source evidence**: `src-tauri/src/error.rs:49-54`:
```
49:    #[error("{zh} ({en})")]
50:    Localized {
51:        key: &'static str,
52:        zh: String,
53:        en: String,
54:    },
```
Line 50 is the `Localized` field name. Note's reference is correct.

**Severity**: no issue

---

## Finding 15 — settings.rs:519 and mutate_settings claims

**Note location**: §6.4 — "settings.rs:519 | OnceLock<RwLock<>> + unwrap_or_else | 用 parking_lot::RwLock 避免 poisoned panic"

**Verdict**: ok

**Source evidence**:
- `src-tauri/src/settings.rs:519`: `static SETTINGS_STORE: OnceLock<RwLock<AppSettings>> = OnceLock::new();` ✓
- `src-tauri/src/settings.rs:574`: `fn mutate_settings<F>(mutator: F)` — parameter named `mutator` ✓
- Line 578: `.unwrap_or_else(|e| { ... e.into_inner() })` — poisoned-panic recovery present ✓

**Severity**: no issue

---

## Finding 16 — Provider.settings_config: Value at provider.rs:14

**Note location**: §6.2 — "Provider.settings_config: Value（provider.rs:14）是 serde_json::Value"

**Verdict**: ok

**Source evidence**: `src-tauri/src/provider.rs:13-14`:
```rust
#[serde(rename = "settingsConfig")]
pub settings_config: Value,
```
`Value` is `serde_json::Value` (imported at line 3). Line 14 exact.

**Severity**: no issue

---

## Finding 17 — Provider Option fields line range

**Note location**: §6.2 — "Provider 结构体里很多字段都是 Option<T>（provider.rs:15-38）"

**Verdict**: stale (minor)

**Source evidence**: `src-tauri/src/provider.rs:10-43` defines the Provider struct. First Option field attribute starts at line 15 (`#[serde(skip_serializing_if = "Option::is_none")]`), first Option field at line 17 (`website_url: Option<String>`). Last Option field is `icon_color: Option<String>` at line 38. The struct closes at line 43. The range "15-38" is defensible if counting from the first attribute.

**Severity**: no issue

---

## Finding 18 — AppType match locations

**Note location**: §6.1 — "AppType 的 match 在 McpApps（app_config.rs:24）、VisibleApps（settings.rs:66）、CommonConfigSnippets（app_config.rs:439）里重复出现"

**Verdict**: ok (one line off)

**Source evidence**:
- `app_config.rs:24`: `pub fn is_enabled_for(&self, app: &AppType) -> bool { match app {` (McpApps) ✓
- `settings.rs:66`: `pub fn is_visible(&self, app: &AppType) -> bool { match app {` (VisibleApps) ✓
- `app_config.rs:439`: `impl CommonConfigSnippets {` — the match is at line 441 (`pub fn get(&self, app: &AppType) -> Option<&String> { match app {`), not 439. Line 439 is the `impl` block start.

**Exact replacement**: `CommonConfigSnippets（app_config.rs:441）` (not 439)

**Severity**: low

---

## Finding 19 — "每次加新工具都要改 10+ 个 match"

**Note location**: §6.1 — "每次加新工具都要改 10+ 个 match"

**Verdict**: ok (likely understated)

**Source evidence**: `grep -rn "match.*app_type\|match.*app\b\|match.*AppType" src-tauri/src/ --include="*.rs` → 118 match statements. Key files: `app_config.rs` (155 AppType refs), `services/provider/mod.rs` (121), `services/proxy.rs` (83), `settings.rs` (29). The "10+" claim is conservative.

**Severity**: no issue

---

## Finding 20 — Preset file count and size

**Note location**: §6.4 — "8 个 preset 文件 | 237KB TypeScript 数据"

**Verdict**: stale (minor)

**Source evidence**: 8 files found. `wc -lc` total: 8604 lines, 243346 bytes = **237.6 KB**. Note says "237KB"; actual is 237.6KB (rounds to 238KB).

**Exact replacement**: `8 个 preset 文件 | 238KB TypeScript 数据` or keep "237KB" (difference negligible).

**Severity**: low

---

## Finding 21 — Streaming file line counts

**Note location**: §6.3 — "streaming.rs（1141 行）+ streaming_codex_chat.rs（1082 行）+ streaming_gemini.rs（1054 行）+ streaming_responses.rs（1185 行）"

**Verdict**: ok

**Source evidence**: `wc -l src-tauri/src/proxy/providers/streaming*.rs`:
- streaming.rs: 1141 ✓
- streaming_codex_chat.rs: 1082 ✓
- streaming_gemini.rs: 1054 ✓
- streaming_responses.rs: 1185 ✓

All exact.

**Severity**: no issue

---

## Finding 22 — transform_codex_chat.rs line count

**Note location**: §6.3 — "transform_codex_chat.rs（2073 行）"

**Verdict**: ok

**Source evidence**: `wc -l src-tauri/src/proxy/providers/transform_codex_chat.rs` → 2073 ✓

**Severity**: no issue

---

## Finding 23 — commands/misc.rs size

**Note location**: §6.3 — "commands/misc.rs（176.0KB）"

**Verdict**: ok

**Source evidence**: `wc -lc src-tauri/src/commands/misc.rs` → 4426 lines, 180271 bytes. 180271/1024 = **176.04 KB** ≈ 176.0KB ✓

**Severity**: no issue

---

## Finding 24 — Functions in lib.rs (放错地方的代码)

**Note location**: §6.3 — "cleanup_before_exit()（lib.rs:1513）", "restore_proxy_state_on_startup()（lib.rs:1558）", "is_chinese_locale()（lib.rs:1685）", "initialize_common_config_snippets()（lib.rs:1601）"

**Verdict**: ok

**Source evidence**:
- `lib.rs:1513`: `pub async fn cleanup_before_exit(app_handle: &tauri::AppHandle)` ✓
- `lib.rs:1558`: `async fn restore_proxy_state_on_startup(state: &store::AppState)` ✓
- `lib.rs:1685`: `fn is_chinese_locale() -> bool` ✓
- `lib.rs:1601`: `fn initialize_common_config_snippets(state: &store::AppState)` ✓

All line numbers exact. Architectural criticism is valid.

**Severity**: no issue

---

## Finding 25 — ".setup() 闭包 786 行" and invoke_handler 271 commands

**Note location**: §6.4 — "lib.rs:284-1070 | .setup() 闭包 786 行"; "lib.rs:1072-1377 | 271 个命令注册"

**Verdict**: ok

**Source evidence**:
- `.setup()` at lib.rs:284, ends around lib.rs:1070. 1070-284 = 786 lines ✓
- `.invoke_handler` at lib.rs:1072. `grep -c "commands::" lib.rs` → 271 ✓

**Severity**: no issue

---

## Finding 26 — 12 DAO modules

**Note location**: §6.3 — "12 个 DAO 模块各自实现 lock_conn! + SQL 查询"

**Verdict**: ok (with nuance)

**Source evidence**: `ls src-tauri/src/database/dao/*.rs | wc -l` → 12 files. These include `mod.rs` (re-export module) plus 11 actual DAO modules. The "12" count includes mod.rs.

**Exact replacement**: "12 个 DAO 模块" is defensible if counting mod.rs. "11 个 DAO 模块（不含 mod.rs）" would be more precise.

**Severity**: low

---

## Finding 27 — `pub use` duplication at lib.rs:38

**Note location**: §7.1 — "删除 lib.rs:38 里重复的 pub use 导出"

**Verdict**: ok (with line nuance)

**Source evidence**: `src-tauri/src/lib.rs:38-59` has 13 `pub use` statements. Line 40: `pub use commands::open_provider_terminal;` is redundant with line 41: `pub use commands::*;`. The note says "lib.rs:38" but the duplication is at lines 40–41.

**Exact replacement**: `lib.rs:40` 里重复的 pub use 导出

**Severity**: low

---

## Finding 28 — schema.rs and backup.rs sizes

**Note location**: §6.3 — "schema.rs（2050 行，77.8KB）", "backup.rs（860 行，31.7KB）"

**Verdict**: ok

**Source evidence**:
- `database/schema.rs`: `wc -l` → 2050, `wc -c` → 79691 bytes = 77.8KB ✓
- `database/backup.rs`: `wc -l` → 860, `wc -c` → 32495 bytes = 31.7KB ✓

**Severity**: no issue

---

## Summary

| Severity | Count | Key Issues |
|----------|-------|------------|
| **High** | **1** | `tool_config_xxx` naming pattern is hallucinated (Finding 8) |
| **Medium** | **4** | claude_desktop_config 14KB vs 61KB (5); hook line counts wrong (6); proxy_request_logs 15 vs 25 columns (9); hook line counts (6) |
| **Low** | **7** | Minor rounding (3, 4, 20), off-by-one query counts (7), path ambiguities (10, 11), config module count (12), CommonConfigSnippets line (18) |
| **OK** | **16** | Verified correct against source |

### Critical fix needed:
1. **Finding 8** (hallucination): Remove `tool_config_xxx` naming claim from §6.3. No such pattern exists in the codebase.

### High-priority fixes:
2. **Finding 5**: Fix `claude_desktop_config.rs（14.0KB）` → `（61.4KB）` in §7.2
3. **Finding 6**: Update 4 wrong hook line counts in §1.3: useSettings 505, useProxyStatus 245, useDirectorySettings 373, useDragSort 119
4. **Finding 9**: Fix `15 列` → `25 列` for proxy_request_logs in §6.3
