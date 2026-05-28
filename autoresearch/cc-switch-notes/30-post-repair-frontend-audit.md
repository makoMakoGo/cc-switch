# Post-Repair Frontend Audit

Date: 2026-05-28
Scope: Chapter 5 frontend claims; frontend-related Chapter 1, 6, and 7 claims
Method: Every claim below was verified against source code via `wc -l`, `wc -c`, `grep`, and direct file reads.

---

## Verdict: FAIL — 4 unresolved issues remain

---

## Unresolved Must-Fix Issues

### U1. §1.3 — Duplicate `useProxyStatus()` entry (lines 206–207)

The §1.3 state-management tree has two `useProxyStatus()` lines:

```
  └─ useProxyStatus()                 ← 轮询代理状态（每 5 秒）       ← WRONG, leftover
  └─ useProxyStatus()                 ← 轮询代理状态（运行时每 2 秒） ← correct
```

Source (`src/hooks/useProxyStatus.ts:28`): `refetchInterval: (query) => (query.state.data?.running ? 2000 : false)` — 2s when running.

The repair added the corrected line 207 but did not remove the incorrect line 206. Line 206 must be deleted.

### U2. §1.4 — lib.rs module count still says 34 (line 246)

```
│   lib.rs    │  1825 行，声明 34 个模块 │
```

Actual count: 35 `mod` declarations in `lib.rs:1–36` (lines 1–33, 35–36; line 19 is `#[cfg]` attribute, not a module). The §6.4 table (line 5194) was correctly repaired to "35 个 mod 声明", but §1.4 was not updated. Change 34 → 35.

### U3. §1.4 — Duplicate commands/ submodule count (lines 253–254)

```
   │  commands/  │  │  services/ │  │   proxy/    │
   │ 34 个子模块 │
   │ 31 个子模块 │
```

Source: `grep -c '^pub mod\|^mod ' commands/mod.rs` = 31. The repair added the corrected "31 个子模块" line but did not remove the incorrect "34 个子模块" line. Delete line 253.

### U4. §6.4 — Preset file count/size mismatch (line 5232)

```
- 9 个 preset 文件（237KB）— 结构几乎一样但没有抽取公共模板
```

The §5.3 table lists exactly 8 provider presets totaling 237.3KB. The 9th file, `mcpPresets.ts` (3.2KB), has a completely different structure (exports `McpPreset[]`, not provider presets). Two problems:

1. The 237KB figure only covers the 8 provider presets, not all 9 files (real total ≈ 240.5KB).
2. "结构几乎一样" is false for the full set of 9 — `mcpPresets.ts` is structurally different from the provider presets.

This line should either say "8 个 provider preset 文件（237KB）— 结构几乎一样" or acknowledge that mcpPresets.ts is structurally distinct.

---

## Evidence-Backed Suggested Edits

### S1. §1.3 tree diagrams — `localStorage("currentView")` is misleading (lines 203, 232)

Both tree diagrams in §1.3 show `localStorage("currentView")`. The actual storage key is `"cc-switch-last-view"` (`src/App.tsx:138`). The §5.1 section correctly documents the real key. This is a simplification that could confuse a maintainer looking for the key in source. Suggest changing to `localStorage("cc-switch-last-view")`.

### S2. §5.3 / §6.4 — Inconsistent "8 vs 9 preset files" terminology

§5.3 table and AI Slop (line 5115) refer to "8 个文件" (provider presets). §6.4 (line 5232) and §7.1 (line 5250) say "9 个 preset 文件" (including mcpPresets.ts). Both counts are defensible for different scopes, but the inconsistency could confuse readers. Recommend standardizing: "8 个 provider preset 文件" when referring to the provider presets specifically, "9 个 preset 文件" when including mcpPresets.ts, and adjusting the size accordingly.

---

## False Alarms Checked and Rejected

### F1. §5.2 descriptions have ±1 line count discrepancies

Six hooks have descriptions that say N+1 lines while the table and `wc -l` say N: useDragSort (120 vs 119), useImportExport (204 vs 203), useHermes (175 vs 174), usePromptActions (153 vs 152), useSkills (359 vs 358), useStreamCheck (141 vs 140). The table values match `wc -l` exactly. The descriptions are off by 1, consistent with trailing-newline convention. Repair-log item "intentionally left unchanged #8" covers this. **Not a must-fix.**

### F2. §1.3 `localStorage("currentView")` — intentional simplification

The tree diagram uses "currentView" as a human-readable label. The real key "cc-switch-last-view" is documented in §5.1. This is a style choice, not an error. See S1 for a suggested improvement.

### F3. lib.rs 1825 vs 1826 lines

`wc -l` reports 1826 (trailing newline). Repair-log item "intentionally left unchanged #2" documents both conventions as defensible. The notes consistently use 1825. **Not a must-fix.**

### F4. `claude_desktop_config.rs` 61.4KB vs 61.5KB

Actual size: 62,939 bytes = 61.46KB. Both 61.4KB (§6.1, appendix) and 61.5KB (§7.2) are reasonable rounding. **Not a must-fix.**

### F5. `pub use` at lib.rs:40 is correctly identified

Source: `lib.rs:40` is `pub use commands::open_provider_terminal;`, immediately followed by `lib.rs:41` which is `pub use commands::*;`. The notes (§7.1, line 5242) correctly identify this as a duplicate. **No issue.**

---

## Verified Claims (spot-checked, all correct)

| Claim | Location | Source verification |
|-------|----------|-------------------|
| App.tsx = 1604 lines | §5.1, §6.1, §7.2 | `wc -l` = 1604 ✓ |
| View type at line 94, 14 views | §5.1 | `src/App.tsx:94-108` ✓ |
| VALID_APPS = 7 apps, line 120 | §5.1 | `src/App.tsx:120-128` ✓ |
| VIEW_STORAGE_KEY = "cc-switch-last-view" | §5.1 | `src/App.tsx:138` ✓ |
| DEFAULT_DRAG_BAR_HEIGHT line 116 | §5.1 | `src/App.tsx:116` ✓ |
| useProxyStatus = 245 lines | §5.2 table | `wc -l` = 245 ✓ |
| useSettings = 505 lines | §5.2 table | `wc -l` = 505 ✓ |
| useProviderActions = 385 lines | §5.2 table | `wc -l` = 385 ✓ |
| useDirectorySettings = 373 lines | §5.2 table | `wc -l` = 373 ✓ |
| useDragSort = 119 lines | §5.2 table | `wc -l` = 119 ✓ |
| All 25 hook line counts | §5.2 table | All match `wc -l` ✓ |
| providersApi.add signature | §5.2 | `providers.ts:58-64` ✓ |
| providersApi.update signature | §5.2 | `providers.ts:66-76` ✓ |
| providersApi.delete signature | §5.2 | `providers.ts:78-80` ✓ |
| providersApi.switch signature | §5.2 | `providers.ts:90-92` ✓ |
| proxyApi = 6 API groups, 121 lines | §5.2 | `proxy.ts:11-120` ✓ |
| proxyApi.updateProxyConfigForApp — no spurious appType | §5.2 | `proxy.ts:92-94` ✓ |
| UseSettingsResult interface (19 members) | §5.2 | `useSettings.ts:21-45` ✓ |
| UseImportExportResult (10 members) | §5.2 | `useImportExport.ts:18-28` ✓ |
| hermesKeys includes memoryLimits | §5.2 | `useHermes.ts:26-32` ✓ |
| CopilotOptimizerConfig has request_classification | §5.2 | `proxy/types.rs:284` ✓ |
| Query layer line counts (10 files) | §5.2 | `wc -l lib/query/*.ts` ✓ |
| Query layer file sizes (10 files) | §5.2 | `ls -la lib/query/*.ts` ✓ |
| API file sizes (25 files) | §5.2 table | `ls -la lib/api/` ✓ |
| ProxyConfig struct fields | §5.2 | `proxy/types.rs:5-14` ✓ |
| ProxyStatus struct fields | §5.2 | `proxy/types.rs:60-79` ✓ |
| commands/mod = 31 submodules | §1.4 (corrected line) | `grep -c` = 31 ✓ |
| lib.rs = 35 mod declarations | §6.4 | Counted lines 1-36 ✓ |
| lib.rs:40 duplicate pub use | §7.1 | `lib.rs:40-41` ✓ |
| 8 provider preset files | §5.3 table | `ls src/config/*ProviderPresets*` = 8 ✓ |
| mcpPresets.ts = 3.2KB | (not in §5.3 table) | `ls` = 3.2K ✓ |
