# Ch7 Source Support Findings: 重构路线图

Verifier: roadmap-source-support-fact-checker
Scope: 第 7 章 重构路线图 (lines 5193–5276) + 附录表 (lines 5279–5345)

---

## Finding 1

- **Location**: 7.2 中等重构, line 5229
- **Claim**: `claude_desktop_config.rs`（14.0KB）
- **Verdict**: wrong
- **Source evidence**: `ls -la src-tauri/src/claude_desktop_config.rs` → 61.5KB (62,939 bytes). `wc -l` → 1826 lines. The appendix table at line 5315 correctly states `61.4KB | 1826`.
- **Severity**: medium
- **Replacement**: `claude_desktop_config.rs`（61.5KB）

---

## Finding 2

- **Location**: 7.1 低风险清理, line 5200
- **Claim**: 删除 `lib.rs:38` 里重复的 `pub use` 导出
- **Verdict**: wrong
- **Source evidence**: `lib.rs:38` is `pub use app_config::{AppType, InstalledSkill, McpApps, McpServer, MultiAppConfig, SkillApps};` — not a duplicate. The actual redundancy is at lines 40–41: `pub use commands::open_provider_terminal;` followed by `pub use commands::*;`. Line 40 is subsumed by line 41.
- **Severity**: low
- **Replacement**: 删除 `lib.rs:40` 的冗余 `pub use commands::open_provider_terminal;`（已被 `lib.rs:41` 的 `pub use commands::*;` 覆盖）

---

## Finding 3

- **Location**: 7.1 低风险清理, line 5208
- **Claim**: 8 个 preset 文件的结构抽取为公共模板
- **Verdict**: wrong
- **Source evidence**: `ls src/config/*[Pp]reset*.ts` returns 9 files:
  - claudeDesktopProviderPresets.ts
  - claudeProviderPresets.ts
  - codexProviderPresets.ts
  - geminiProviderPresets.ts
  - hermesProviderPresets.ts
  - mcpPresets.ts
  - openclawProviderPresets.ts
  - opencodeProviderPresets.ts
  - universalProviderPresets.ts
- **Severity**: low
- **Replacement**: 9 个 preset 文件的结构抽取为公共模板

---

## Finding 4

- **Location**: 7.2 中等重构, line 5218
- **Claim**: `cleanup.rs` — `cleanup_before_exit()` 和 `restore_proxy_state_on_startup()`（`lib.rs:1513-1598`）
- **Verdict**: wrong
- **Source evidence**: `cleanup_before_exit()` spans lines 1513–1548. `restore_proxy_state_on_startup()` spans lines 1558–1599. The end boundary should be 1599, not 1598.
- **Severity**: low
- **Replacement**: `lib.rs:1513-1599`

---

## Finding 5

- **Location**: 7.2 中等重构, line 5220
- **Claim**: `services/proxy.rs`（141.3KB，3909 行）
- **Verdict**: ok
- **Source evidence**: `wc -c` → 144,756 bytes ≈ 141.4KB. `wc -l` → 3909. Close enough for a roadmap estimate.
- **Severity**: n/a

---

## Finding 6

- **Location**: 7.2 中等重构, line 5225
- **Claim**: `provider/mod.rs`（105.5KB）
- **Verdict**: ok
- **Source evidence**: `wc -c` → 108,053 bytes ≈ 105.5KB. `wc -l` → 2766.
- **Severity**: n/a

---

## Finding 7

- **Location**: 7.2 中等重构, line 5226
- **Claim**: `App.tsx`（1604 行）
- **Verdict**: ok
- **Source evidence**: `wc -l src/App.tsx` → 1604.
- **Severity**: n/a

---

## Finding 8

- **Location**: 7.2 中等重构, line 5227
- **Claim**: `codex_config.rs`（66.4KB）
- **Verdict**: ok
- **Source evidence**: `wc -c` → 68,053 bytes ≈ 66.5KB. `wc -l` → 2024.
- **Severity**: n/a

---

## Finding 9

- **Location**: 7.2 中等重构, line 5228
- **Claim**: `hermes_config.rs`（69.0KB）
- **Verdict**: ok
- **Source evidence**: `wc -c` → 70,689 bytes ≈ 69.0KB. `wc -l` → 1947.
- **Severity**: n/a

---

## Finding 10

- **Location**: 7.3 架构级重构, line 5262
- **Claim**: `forwarder.rs`（122.1KB，3100 行）
- **Verdict**: ok
- **Source evidence**: `wc -c` → 125,105 bytes ≈ 122.2KB. `wc -l` → 3100.
- **Severity**: n/a

---

## Finding 11

- **Location**: 7.2 中等重构, line 5215
- **Claim**: `lib.rs` — 仅模块声明（`lib.rs:1-36`）+ `run()` 函数骨架
- **Verdict**: ok
- **Source evidence**: `lib.rs` has 34 `mod` declarations spanning lines 1–36 (with a blank at line 34). `pub fn run()` starts at line 203. The claim that module declarations occupy lines 1–36 is accurate.
- **Severity**: n/a

---

## Finding 12

- **Location**: 7.2 中等重构, line 5216
- **Claim**: `init.rs` — `.setup()` 闭包逻辑（`lib.rs:284-1070`）
- **Verdict**: ok
- **Source evidence**: `.setup(|app| {` at line 284. `Ok(())` at line 1070, closing `})` at line 1071. The range 284–1070 covers the setup body.
- **Severity**: n/a

---

## Finding 13

- **Location**: 7.2 中等重构, line 5217
- **Claim**: `commands_register.rs` — `.invoke_handler()` 命令注册（`lib.rs:1072-1377`）
- **Verdict**: ok
- **Source evidence**: `.invoke_handler(tauri::generate_handler![` at line 1072. Closing `]);` at line 1377. 266 commands registered (the notes elsewhere say ~271, which is a Chapter 1 claim, not Chapter 7).
- **Severity**: n/a

---

## Finding 14

- **Location**: 7.1 低风险清理, line 5207
- **Claim**: 7 个 config 模块的 `read → parse → modify → write` 骨架抽取为公共函数
- **Verdict**: ok
- **Source evidence**: 7 `*_config.rs` files in `src-tauri/src/`: app_config.rs (41.0KB), claude_desktop_config.rs (61.5KB), codex_config.rs (66.5KB), gemini_config.rs (20.4KB), hermes_config.rs (69.0KB), openclaw_config.rs (35.0KB), opencode_config.rs (6.9KB).
- **Severity**: n/a

---

## Finding 15

- **Location**: 7.1 低风险清理, line 5204
- **Claim**: 错误消息统一为英文（或统一为中文）
- **Verdict**: ok
- **Source evidence**: Error messages are mixed. Examples: Chinese — `AppError::Message("供应商 {id} 不存在")` (provider/mod.rs:1574), `AppError::Config("无法获取用户主目录")` (settings.rs:486). English — `AppError::Message("No current provider")` (provider/mod.rs:1920), `AppError::Message("Serialization failed: {e}")` (provider/mod.rs:2008). The inconsistency is real and widespread.
- **Severity**: n/a

---

## Summary

| # | Verdict | Severity | Issue |
|---|---------|----------|-------|
| 1 | wrong | medium | `claude_desktop_config.rs` size says 14.0KB, actual is 61.5KB |
| 2 | wrong | low | `lib.rs:38` is not the duplicate; line 40 is |
| 3 | wrong | low | 9 preset files, not 8 |
| 4 | wrong | low | cleanup range end is 1599, not 1598 |
| 5–15 | ok | — | All other claims verified against source |

No hallucinations found. All recommendations are grounded in real code structure. The one medium-severity issue is the stale `claude_desktop_config.rs` size (14.0KB vs actual 61.5KB), which could mislead a maintainer into underestimating the refactoring effort.
