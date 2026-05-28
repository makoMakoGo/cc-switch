# Ch 7 Skeptic Findings — 重构路线图

Reviewed: `docs/cc-switch-source-notes.md` §7 (lines 5193–5275) and the appendix table (lines 5279–5492).
Source of truth: `src-tauri/src/` and `src/`.

---

## Finding 1 — Wrong line reference for "duplicate pub use"

| Field | Value |
|-------|-------|
| Note location | §7.1, line 5200: `删除 lib.rs:38 里重复的 pub use 导出` |
| Verdict | **wrong** |
| Severity | medium |

The note points to `lib.rs:38` as the location of a duplicate `pub use`. Line 38 is:

```
pub use app_config::{AppType, InstalledSkill, McpApps, McpServer, MultiAppConfig, SkillApps};
```

This is **not** a duplicate — it is the sole re-export of those symbols. The actual redundancy is at **lines 40–41**:

```
40: pub use commands::open_provider_terminal;
41: pub use commands::*;
```

Line 40 is subsumed by the wildcard on line 41. `open_provider_terminal` is defined at `commands/misc.rs:2174` and re-exported via `commands/mod.rs:49` (`pub use misc::*`).

**Replacement text:**
> 删除 `lib.rs:40` 里重复的 `pub use` 导出（`open_provider_terminal` 已被 `commands::*` 覆盖）

---

## Finding 2 — Preset file count is 9, not 8

| Field | Value |
|-------|-------|
| Note location | §7.1, line 5208: `8 个 preset 文件的结构抽取为公共模板` |
| Verdict | **wrong** |
| Severity | medium |

Actual preset files in `src/config/`:

| # | File | Size |
|---|------|------|
| 1 | `claudeProviderPresets.ts` | 35.6 KB |
| 2 | `claudeDesktopProviderPresets.ts` | 27.0 KB |
| 3 | `codexProviderPresets.ts` | 32.5 KB |
| 4 | `geminiProviderPresets.ts` | 9.3 KB |
| 5 | `hermesProviderPresets.ts` | 35.2 KB |
| 6 | `openclawProviderPresets.ts` | 52.4 KB |
| 7 | `opencodeProviderPresets.ts` | 42.6 KB |
| 8 | `universalProviderPresets.ts` | 3.0 KB |
| 9 | `mcpPresets.ts` | 3.2 KB |

**Replacement text:**
> 9 个 preset 文件的结构抽取为公共模板

---

## Finding 3 — claude_desktop_config.rs is 61.5 KB, not 14.0 KB

| Field | Value |
|-------|-------|
| Note location | §7.2, line 5229: `claude_desktop_config.rs（14.0KB）→ claude_desktop/ 目录` |
| Verdict | **stale** |
| Severity | high |

The note's own appendix (line 5315) correctly says `61.4 KB | 1826 lines`. The inline claim of `14.0 KB` is off by ~4.4× and would mislead anyone triaging refactor priorities.

Source: `ls -lh` → 61.5 KB; `wc -l` → 1826 lines.

**Replacement text:**
> `claude_desktop_config.rs`（61.5 KB，1826 行）→ `claude_desktop/` 目录

---

## Finding 4 — ProviderManager already exists as a struct

| Field | Value |
|-------|-------|
| Note location | §7.3, lines 5257–5259: `定义 ProviderManager trait` |
| Verdict | **unsupported** |
| Severity | high |

The roadmap proposes "定义 `ProviderManager` trait" as if this abstraction does not yet exist. In fact, `ProviderManager` is already a concrete struct:

`provider.rs:112–117`:
```rust
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ProviderManager {
    pub providers: IndexMap<String, Provider>,
    pub current: String,
}
```

With an `impl` block at `provider.rs:406` and usage throughout `app_config.rs` (lines 474, 499–505, 590, 641, 646, 654). The roadmap should acknowledge the existing struct and propose converting or extending it, not creating something from scratch.

**Replacement text:**
> 将现有 `ProviderManager` struct（`provider.rs:114`）重构为 trait 或为其添加 trait 接口，统一各 config 模块的切换逻辑

---

## Finding 5 — commands/mod.rs has 31 submodules, not 33

| Field | Value |
|-------|-------|
| Note location | Appendix, line 5478: `33 个子模块声明（commands/mod.rs:3-34）` |
| Verdict | **wrong** |
| Severity | medium |

Actual count in `commands/mod.rs:3–34`: 30 `mod` declarations + 1 `pub mod skill` = **31** submodules.

**Replacement text:**
> 31 个子模块声明（commands/mod.rs:3–34）

---

## Finding 6 — cleanup range off-by-one

| Field | Value |
|-------|-------|
| Note location | §7.2, line 5218: `cleanup_before_exit() 和 restore_proxy_state_on_startup()（lib.rs:1513-1598）` |
| Verdict | **wrong** |
| Severity | low |

`cleanup_before_exit` spans lines 1513–1548. `restore_proxy_state_on_startup` spans lines 1558–1599 (closing `}` on line 1599). The combined range is 1513–1599, not 1513–1598.

**Replacement text:**
> `cleanup_before_exit()` 和 `restore_proxy_state_on_startup()`（`lib.rs:1513-1599`）

---

## Finding 7 — commands/mod.rs is 66 lines, not 67

| Field | Value |
|-------|-------|
| Note location | Appendix, line 5457: `commands/mod.rs（src-tauri/src/commands/mod.rs，67 行）` |
| Verdict | **wrong** |
| Severity | low |

`wc -l` returns 66. The file has a trailing newline but no 67th line of content.

**Replacement text:**
> `commands/mod.rs`（`src-tauri/src/commands/mod.rs`，66 行）

---

## Cross-reference: Verified OK claims in §7

| Claim | Note line | Actual |
|-------|-----------|--------|
| `lib.rs` 1825 lines | 5214 | 1825 ✓ |
| `.setup()` closure at 284–1070 | 5216 | 284–1070 ✓ |
| `.invoke_handler()` at 1072–1377 | 5217 | 1072–1377 ✓ |
| `services/proxy.rs` 141.3 KB, 3909 lines | 5220 | 141.4 KB, 3909 ✓ |
| `provider/mod.rs` 105.5 KB | 5225 | 105.5 KB ✓ |
| `App.tsx` 1604 lines | 5226 | 1604 ✓ |
| `codex_config.rs` 66.4 KB | 5227 | 66.5 KB ✓ |
| `hermes_config.rs` 69.0 KB | 5228 | 69.0 KB ✓ |
| `forwarder.rs` 122.1 KB, 3100 lines | 5262 | 122.2 KB, 3100 ✓ |
| `Provider.settings_config` is `serde_json::Value` | 5275 | `provider.rs:14` ✓ |
| `initialize_common_config_snippets()` at 1601 | 5219 | 1601 ✓ |
| 7 config modules exist | 5207 | 7 `*_config.rs` files ✓ |
| `#[allow(dead_code)]` annotations exist | 5198 | 80+ instances ✓ |
| `stop_with_restore_keep_state()` exists | 5224 | `services/proxy.rs:1027` ✓ |
| 25 hooks | Appendix | 25 `.ts` files in `src/hooks/` ✓ |
| 34 modules in lib.rs | Appendix | 34 `mod`/`pub mod` declarations ✓ |
| `error.rs` 146 lines, 3.4 KB | Appendix | 146 lines ✓ |
| `settings.rs` 876 lines | Appendix | 876 lines ✓ |
