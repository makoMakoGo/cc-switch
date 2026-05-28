# Post-Repair Skeptic Audit — docs/cc-switch-source-notes.md

Date: 2026-05-28
Auditor: post-repair-skeptic
Scope: Full document (8283 lines), focusing on first-unique-copy claims and any new hallucination introduced by the repair itself.

---

## Verdict: FAIL — 3 unresolved must-fix issues in first unique copy

---

## 1. Unresolved Must-Fix Issues (in first unique copy)

### Issue A: localStorage key not repaired in §1.3

| Field | Detail |
|-------|--------|
| Location | Lines 203, 232 |
| Document says | `localStorage("currentView")` |
| Source says | `VIEW_STORAGE_KEY = "cc-switch-last-view"` (App.tsx:138) |
| Repair log | Entry #43 claims "currentView → cc-switch-last-view" |
| Reality | Repair only applied at line 4140 (Ch5 code block). Lines 203 and 232 still show the wrong key. |

**Fix**: Replace `localStorage("currentView")` → `localStorage("cc-switch-last-view")` at lines 203 and 232.

---

### Issue B: Polling interval botched — contradictory claims coexist

| Field | Detail |
|-------|--------|
| Location | Lines 206-207 |
| Line 206 says | `useProxyStatus() ← 轮询代理状态（每 5 秒）` |
| Line 207 says | `useProxyStatus() ← 轮询代理状态（运行时每 2 秒）` |
| Source says | `refetchInterval: (query) => (query.state.data?.running ? 2000 : false)` (useProxyStatus.ts:28) — 2s when running, false otherwise |
| Repair log | Entry #9 claims "useProxyStatus 5s → 2s" |
| Reality | Repair ADDED line 207 ("每 2 秒") without DELETING line 206 ("每 5 秒"). Document now has two contradictory claims. |

**Fix**: Delete line 206 ("每 5 秒"), keep line 207 ("运行时每 2 秒"). Or merge into single line.

---

### Issue C: commands/ submodule count wrong in §1.4 diagram

| Field | Detail |
|-------|--------|
| Location | Line 253 |
| Document says | `│ 34 个子模块 │` (for commands/ box in ASCII diagram) |
| Source says | commands/mod.rs has 31 submodule declarations (lines 3-34, excluding blank line 30) |
| Repair log | Entry #12 claims "commands/mod 34 → 31 submodules" |
| Reality | Textual list at line 683 was fixed to 31, but the diagram at line 253 still shows 34. |

**Fix**: Change line 253 from "34 个子模块" to "31 个子模块".

---

## 2. Duplicate-Block Issues (repair intentionally deferred)

These appear in verbatim-copied duplicate blocks the repair acknowledged as out-of-scope (repair log item #1). They still carry wrong values:

| Line(s) | Claim | Should be | Source |
|---------|-------|-----------|--------|
| 1650, 3013, 5520, 6956 | "33 个子模块声明（commands/mod.rs:3-34）" | "31 个子模块声明" | commands/mod.rs = 31 |
| 232 | `localStorage("currentView")` | `localStorage("cc-switch-last-view")` | App.tsx:138 |

Severity: Low for the four duplicate copies (first copy is authoritative), but line 232 is in §1.3 which is high-traffic.

---

## 3. False Alarms — Checked and Rejected

| Claim | Location | Source check | Verdict |
|-------|----------|--------------|---------|
| lib.rs "声明 34 个模块" | line 246, 756, 1723, 3086, 5593, 7029 | Counted 34 mod declarations in lib.rs:1-36 | ✓ CORRECT (repair log entry #50 tried 34→35 but 34 is actually correct) |
| schema.rs 23 tables | multiple | `grep -c "CREATE TABLE" schema.rs` = 23 | ✓ CORRECT |
| useSettings.ts 505 行 | line 210 | `wc -l` = 505 | ✓ CORRECT |
| useProxyStatus.ts 245 行 | line 212 | `wc -l` = 245 | ✓ CORRECT |
| useDirectorySettings.ts 373 行 | line 213 | `wc -l` = 373 | ✓ CORRECT |
| useDragSort.ts 119 行 | line 214 | `wc -l` = 119 | ✓ CORRECT |
| queries.ts 155 行 | line 217 | `wc -l` = 155 | ✓ CORRECT |
| mutations.ts 356 行 | line 218 | `wc -l` = 356 | ✓ CORRECT |
| proxy.ts 243 行 | line 219 | `wc -l` = 243 | ✓ CORRECT |
| failover.ts 288 行 | line 220 | `wc -l` = 288 | ✓ CORRECT |
| usage.ts 319 行 | line 221 | `wc -l` = 319 | ✓ CORRECT |
| subscription.ts 63 行 | line 222 | `wc -l` = 63 | ✓ CORRECT |
| App.tsx 1604 行 | line 202 | `wc -l` = 1604 | ✓ CORRECT |
| 14 个视图 | line 203 | View type has 14 variants (App.tsx:94-108) | ✓ CORRECT |
| 25 个 hooks | line 209 | `ls hooks/*.ts | wc -l` = 25 | ✓ CORRECT |
| lib/query 10 个文件 | line 216 | `ls lib/query/*.ts | wc -l` = 10 | ✓ CORRECT |
| serde(alias = "reasoning_content") | Ch2 table | `proxy/providers/streaming.rs:37` confirmed | ✓ CORRECT |
| commands/mod 66 行 | line 683 | `wc -l` = 66 | ✓ CORRECT |
| proxy/mod 31 submodules | line 683 | Counted lines 5-35 in proxy/mod.rs = 31 | ✓ CORRECT |
| lock_conn! at database/mod.rs:61 | line 299 | `grep -n "macro_rules! lock_conn"` = line 61 | ✓ CORRECT |
| handlers.rs is a file, not directory | §4.1 tree | `ls proxy/handlers*` = handlers.rs (43.6KB) | ✓ KNOWN (acknowledged in repair log #9) |
| No unsafe blocks | line 297 | Searched codebase, no actual `unsafe` blocks | ✓ CORRECT |
| lib.rs 1825 行 | line 61 | `wc -l` = 1825 | ✓ CORRECT |

---

## 4. Summary

- **3 must-fix issues** in the first unique copy (lines 203, 206, 253)
- **5 additional issues** in duplicate blocks (lines 232, 1650, 3013, 5520, 6956)
- **17 claims verified correct** — false alarms rejected
- Root cause: repair applied to some occurrences but missed others in the same section, or botched in-place edits (adding instead of replacing)

---

## 5. Recommended Edit Priorities

1. **High**: Fix line 206 — delete "每 5 秒" line (contradicts "每 2 秒" on next line)
2. **High**: Fix line 203 — `localStorage("currentView")` → `localStorage("cc-switch-last-view")`
3. **Medium**: Fix line 253 — diagram commands/ count 34 → 31
4. **Low**: Fix line 232 — duplicate localStorage key in §1.3
5. **Deferred**: Duplicate blocks at lines 1650, 3013, 5520, 6956 (structural duplication issue)
