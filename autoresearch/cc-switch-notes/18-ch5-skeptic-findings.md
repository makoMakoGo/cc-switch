# Chapter 5 — Frontend Architecture Skeptic Findings

Adversarial pass focused on: invented architecture, stale counts, wrong dependencies, unsupported UI flow claims.

---

## Finding 1 — `providersApi` signatures are fabricated

**Note location**: §5.2, "providersApi" block (lines ~4982–5004)

**Claimed**:
```typescript
async add(appId: AppId, provider: Omit<Provider, "id">): Promise<Provider> {
    return await invoke("add_provider", { app: appId, ...provider });
},
async update(provider: Provider): Promise<void> {
    return await invoke("update_provider", { provider });
},
async remove(providerId: string): Promise<void> {
    return await invoke("delete_provider", { providerId });
},
async switch(appType: AppId, providerId: string): Promise<SwitchResult> {
    return await invoke("switch_provider", { appType, providerId });
},
```

**Actual** (`src/lib/api/providers.ts:49–92`):
```typescript
async add(provider: Provider, appId: AppId, addToLive?: boolean): Promise<boolean> {
    return await invoke("add_provider", { provider, app: appId, addToLive });
},
async update(provider: Provider, appId: AppId, originalId?: string): Promise<boolean> {
    return await invoke("update_provider", { provider, app: appId, originalId });
},
async delete(id: string, appId: AppId): Promise<boolean> {
    return await invoke("delete_provider", { id, app: appId });
},
async switch(id: string, appId: AppId): Promise<SwitchResult> {
    return await invoke("switch_provider", { id, app: appId });
},
```

**Verdict**: **hallucination** — parameter order, method name (`remove` vs `delete`), return types (`Provider`/`void` vs `boolean`), and spread-vs-object arg pattern are all wrong. The notes appear to have been generated from a template rather than read from the source.

**Severity**: high — anyone coding against these signatures will get compile errors or silent bugs.

**Replacement**: Replace the entire `providersApi` code block with the actual signatures above.

---

## Finding 2 — `useProxyStatus` polling interval contradicts itself

**Note location**:
- §1.3 状态管理 (line ~206): `useProxyStatus() ← 轮询代理状态（每 5 秒）`
- §5.2 table (line ~4136): `useProxyStatus | useProxyStatus.ts | 245 | 代理状态轮询（每 2 秒）`

**Actual** (`src/hooks/useProxyStatus.ts:28`):
```typescript
refetchInterval: (query) => (query.state.data?.running ? 2000 : false),
```

**Verdict**: **stale** — the §1.3 claim of 5 seconds is wrong; the §5.2 claim of 2 seconds is correct. The polling is conditional on `running` state.

**Severity**: medium — contradicts actual behavior; the 5-second claim in Ch1 is misleading.

**Replacement**: In §1.3, change `轮询代理状态（每 5 秒）` → `轮询代理状态（运行时每 2 秒）`.

---

## Finding 3 — `hermesKeys` missing `memoryLimits` key

**Note location**: §5.2, "useHermes" block (line ~4204)

**Claimed**:
```typescript
export const hermesKeys = {  // useHermes.ts:26
    all: ["hermes"] as const,
    liveProviderIds: ["hermes", "liveProviderIds"] as const,
    modelConfig: ["hermes", "modelConfig"] as const,
    memory: (kind: HermesMemoryKind) => ["hermes", "memory", kind] as const,
};
```

**Actual** (`src/hooks/useHermes.ts:26–32`):
```typescript
export const hermesKeys = {
  all: ["hermes"] as const,
  liveProviderIds: ["hermes", "liveProviderIds"] as const,
  modelConfig: ["hermes", "modelConfig"] as const,
  memory: (kind: HermesMemoryKind) => ["hermes", "memory", kind] as const,
  memoryLimits: ["hermes", "memoryLimits"] as const,   // ← missing from notes
};
```

**Verdict**: **wrong** — `memoryLimits` key is omitted. This is a query key used for cache invalidation; omitting it misrepresents the cache topology.

**Severity**: medium — anyone relying on the notes to understand Hermes cache invalidation will miss `memoryLimits`.

**Replacement**: Add `memoryLimits: ["hermes", "memoryLimits"] as const,` to the code block.

---

## Finding 4 — `claude_desktop_config.rs` size contradicted between chapters

**Note location**:
- §6.1 (line ~5110): `claude_desktop_config.rs | 61.4KB | Claude Desktop 配置读写`
- §7.2 (line ~5229): `claude_desktop_config.rs（14.0KB）→ claude_desktop/ 目录`

**Actual**: `ls -la` shows 61.5KB (1826 lines).

**Verdict**: **wrong** — the §7.2 claim of 14.0KB is fabricated. 14KB would be a trivially small file; the actual file is 61.5KB, consistent with the §6.1 claim.

**Severity**: high — anyone following the refactoring roadmap will underestimate the effort for this file by 4×.

**Replacement**: In §7.2, change `claude_desktop_config.rs（14.0KB）` → `claude_desktop_config.rs（61.4KB，1826 行）`.

---

## Finding 5 — `src/lib/api/types.ts` line count off by one

**Note location**: §5.2, "前端 API 类型" (line ~4447)

**Claimed**: `src/lib/api/types.ts，10 行`

**Actual**: File has 9 lines (line 9 is `| "hermes";`, no trailing newline). Confirmed by reading the entire file.

**Verdict**: **stale** — off by one.

**Severity**: low — trivial count error.

**Replacement**: Change `10 行` → `9 行`.

---

## Finding 6 — `hermes.ts` line count off by one

**Note location**: §5.2, "hermesApi" (line ~4605)

**Claimed**: `src/lib/api/hermes.ts，68 行`

**Actual**: File has 67 lines (last content at line 67: `};`). `wc -l` reports 67.

**Verdict**: **stale** — off by one.

**Severity**: low — trivial count error.

**Replacement**: Change `68 行` → `67 行`.

---

## Finding 7 — `UseImportExportResult` omits two methods

**Note location**: §5.2, "useImportExport" block (line ~4216)

**Claimed**:
```typescript
export interface UseImportExportResult {  // useImportExport.ts:18
    selectedFile: string;
    status: ImportStatus;
    errorMessage: string | null;
    backupId: string | null;
    isImporting: boolean;
    selectImportFile: () => Promise<void>;
    importConfig: () => Promise<void>;
    exportConfig: () => Promise<void>;
}
```

**Actual** (`src/hooks/useImportExport.ts:18–28`):
```typescript
export interface UseImportExportResult {
  selectedFile: string;
  status: ImportStatus;
  errorMessage: string | null;
  backupId: string | null;
  isImporting: boolean;
  selectImportFile: () => Promise<void>;
  clearSelection: () => void;        // ← missing from notes
  importConfig: () => Promise<void>;
  exportConfig: () => Promise<void>;
  resetStatus: () => void;           // ← missing from notes
}
```

**Verdict**: **wrong** — `clearSelection` and `resetStatus` methods are omitted. These are part of the public API surface.

**Severity**: medium — anyone implementing import/export UI will miss these lifecycle methods.

**Replacement**: Add the two missing methods to the interface listing.

---

## Finding 8 — `UseSettingsResult` omits two methods

**Note location**: §5.2, "useSettings 接口" (line ~4257)

**Claimed**:
```typescript
export interface UseSettingsResult {  // useSettings.ts:21
    settings: SettingsFormState | null;
    isLoading: boolean;
    isSaving: boolean;
    isPortable: boolean;
    appConfigDir?: string;
    resolvedDirs: ResolvedDirectories;
    requiresRestart: boolean;
    updateSettings: (updates: Partial<SettingsFormState>) => void;
    updateDirectory: (app: DirectoryAppId, value?: string) => void;
    browseDirectory: (app: DirectoryAppId) => Promise<void>;
}
```

**Actual** (`src/hooks/useSettings.ts:21–33`):
```typescript
export interface UseSettingsResult {
  settings: SettingsFormState | null;
  isLoading: boolean;
  isSaving: boolean;
  isPortable: boolean;
  appConfigDir?: string;
  resolvedDirs: ResolvedDirectories;
  requiresRestart: boolean;
  updateSettings: (updates: Partial<SettingsFormState>) => void;
  updateDirectory: (app: DirectoryAppId, value?: string) => void;
  updateAppConfigDir: (value?: string) => void;   // ← missing from notes
  browseDirectory: (app: DirectoryAppId) => Promise<void>;
  browseAppConfigDir: () => Promise<void>;         // ← missing from notes
}
```

**Verdict**: **wrong** — `updateAppConfigDir` and `browseAppConfigDir` methods are omitted.

**Severity**: medium — the app config directory is a distinct concept from per-app directories; omitting it misrepresents the settings API surface.

**Replacement**: Add the two missing methods to the interface listing.

---

## Finding 9 — `hermesApi` omits `setMemoryEnabled` method

**Note location**: §5.2, "hermesApi" block (line ~4607)

**Claimed**: 6 methods (getModelConfig, openWebUI, launchDashboard, getMemory, setMemory, getMemoryLimits)

**Actual** (`src/lib/api/hermes.ts:18–67`): 7 methods — the notes omit:
```typescript
async setMemoryEnabled(kind: HermesMemoryKind, enabled: boolean): Promise<void> {
    await invoke("set_hermes_memory_enabled", { kind, enabled });
},
```

**Verdict**: **wrong** — `setMemoryEnabled` is a write endpoint that toggles memory blob on/off. Omitting it from the API surface is incorrect.

**Severity**: low — the method exists and is callable from the UI.

**Replacement**: Add `setMemoryEnabled` to the hermesApi listing.

---

## Finding 10 — `mcpApi` code block omits deprecated methods and shows incomplete `upsertServer`

**Note location**: §5.2, "mcpApi" block (line ~4916)

**Claimed**:
```typescript
async upsertServer(id: string, spec: McpServerSpec): Promise<boolean> {
```

**Actual** (`src/lib/api/mcp.ts:20–24`):
```typescript
async upsertServer(
    id: string,
    spec: McpServerSpec | Record<string, any>,
): Promise<boolean> {
```

The `spec` parameter type is `McpServerSpec | Record<string, any>`, not just `McpServerSpec`. The notes also omit the `@deprecated` `getConfig()` and `upsertServerInConfig()` methods that are still present in the file.

**Verdict**: **wrong** — parameter type is narrower in the notes than in reality.

**Severity**: low — the union type is more permissive, so the note's version would cause unnecessary type errors.

**Replacement**: Change `spec: McpServerSpec` → `spec: McpServerSpec | Record<string, any>`.

---

## Finding 11 — Systematic off-by-one in hook detail sections

**Note location**: §5.2, individual hook descriptions

The table at the top of §5.2 has correct line counts (matching `wc -l`), but the detailed descriptions below it consistently report +1:

| Hook | Table says | Detail says | Actual (`read` tool) |
|------|-----------|-------------|---------------------|
| useDragSort | 119 | 120 | 120 |
| useSettingsForm | 203 | 204 | 204 |
| useImportExport | 203 | 204 | 204 |
| useSkills | 358 | 359 | 359 |
| useDirectorySettings | 373 | 374 | 374 |
| usePromptActions | 152 | 153 | 153 |
| useMcp | 74 | 75 | 75 |
| useGlobalProxy | 109 | 110 | 110 |
| useStreamCheck | 140 | 141 | 141 |
| useOpenClaw | 144 | 145 | 145 |
| useHermes | 174 | 175 | 175 |

**Verdict**: **stale** — the table uses `wc -l` (counts newlines), the detail sections use the `read` tool's count (includes trailing empty line). Both are internally consistent but the table and details disagree with each other. The detail sections are actually correct per the `read` tool; the table is off by −1.

**Severity**: low — confusing but not misleading.

**Replacement**: Either update the table to match the detail sections, or add a note that the table uses `wc -l` counts.

---

## Finding 12 — `proxy/types.rs` line count for `ProxyConfig` is off

**Note location**: §5.2, "Rust 代理类型" (line ~4290)

**Claimed**: `proxy/types.rs，496 行` for the file, `ProxyConfig` at `proxy/types.rs:5`

**Actual**: File is 496 lines ✓, `ProxyConfig` is at line 5 ✓. But the notes claim `request_timeout: u64` is "已废弃，保留兼容" — the actual code comment at line 12 says `/// 请求超时时间（秒）- 已废弃，保留兼容`. This is correct.

**Verdict**: **ok** — no issue here.

---

## Finding 13 — `ProxyTakeoverStatus` backend vs frontend mismatch is correctly documented

**Note location**: §5.2

The notes correctly show the backend `ProxyTakeoverStatus` (proxy/types.rs:112) has 5 fields (claude, codex, gemini, opencode, openclaw) and the frontend version (types/proxy.ts:44) adds `claude-desktop` and `hermes`. This is accurate.

**Verdict**: **ok** — no issue.

---

## Summary

| # | Location | Verdict | Severity |
|---|----------|---------|----------|
| 1 | §5.2 providersApi signatures | hallucination | high |
| 2 | §1.3 useProxyStatus interval | stale | medium |
| 3 | §5.2 hermesKeys missing key | wrong | medium |
| 4 | §7.2 claude_desktop_config.rs size | wrong | high |
| 5 | §5.2 types.ts line count | stale | low |
| 6 | §5.2 hermes.ts line count | stale | low |
| 7 | §5.2 UseImportExportResult missing methods | wrong | medium |
| 8 | §5.2 UseSettingsResult missing methods | wrong | medium |
| 9 | §5.2 hermesApi missing method | wrong | low |
| 10 | §5.2 mcpApi parameter type | wrong | low |
| 11 | §5.2 table vs detail line counts | stale | low |
