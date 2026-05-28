# Chapter 5 IPC/State Findings

Scope: 第 5 章：前端架构 (lines 4089–5091) — App.tsx, hooks, IPC, React Query/state, command names.

---

## Finding 1 — `currentView` initialization code is fabricated

**Note location:** §5.1, lines 4113–4117
**Quoted claim:**
```typescript
const [currentView, setCurrentView] = useState(
  localStorage.getItem("currentView") || "providers"
);
```

**Verdict:** wrong

**Source evidence:** `src/App.tsx:138,156-162,171`

Actual implementation uses a dedicated constant and validation function:
```typescript
const VIEW_STORAGE_KEY = "cc-switch-last-view";          // line 138

const getInitialView = (): View => {                     // line 156
  const saved = localStorage.getItem(VIEW_STORAGE_KEY) as View | null;
  if (saved && VALID_VIEWS.includes(saved)) {
    return saved;
  }
  return "providers";
};

const [currentView, setCurrentView] = useState<View>(getInitialView);  // line 171
```

Two errors:
1. localStorage key is `"cc-switch-last-view"` not `"currentView"`
2. Initialization uses a typed getter function with `VALID_VIEWS` validation, not a bare `localStorage.getItem`

**Severity:** high — misleading for anyone trying to understand or modify view persistence.

**Replacement:**
```typescript
const VIEW_STORAGE_KEY = "cc-switch-last-view";
const [currentView, setCurrentView] = useState<View>(getInitialView);
```

---

## Finding 2 — `providersApi.add()` signature is fabricated

**Note location:** §5.2, lines 4991–4992
**Quoted claim:**
```typescript
async add(appId: AppId, provider: Omit<Provider, "id">): Promise<Provider> {
    return await invoke("add_provider", { app: appId, ...provider });
},
```

**Verdict:** wrong

**Source evidence:** `src/lib/api/providers.ts:58-64`
```typescript
async add(
    provider: Provider,
    appId: AppId,
    addToLive?: boolean,
): Promise<boolean> {
    return await invoke("add_provider", { provider, app: appId, addToLive });
},
```

Three errors:
1. Parameter order reversed: actual is `(provider, appId, addToLive?)`, notes show `(appId, provider)`
2. Return type wrong: actual is `Promise<boolean>`, notes claim `Promise<Provider>`
3. Missing `addToLive?: boolean` parameter

**Severity:** high — anyone implementing against these signatures will get compile errors.

**Replacement:**
```typescript
async add(
    provider: Provider,
    appId: AppId,
    addToLive?: boolean,
): Promise<boolean> {
    return await invoke("add_provider", { provider, app: appId, addToLive });
},
```

---

## Finding 3 — `providersApi.update()` signature is fabricated

**Note location:** §5.2, lines 4994–4995
**Quoted claim:**
```typescript
async update(provider: Provider): Promise<void> {
    return await invoke("update_provider", { provider });
},
```

**Verdict:** wrong

**Source evidence:** `src/lib/api/providers.ts:66-76`
```typescript
async update(
    provider: Provider,
    appId: AppId,
    originalId?: string,
): Promise<boolean> {
    return await invoke("update_provider", {
        provider,
        app: appId,
        originalId,
    });
},
```

Errors: missing `appId` required parameter, missing optional `originalId`, return type `Promise<boolean>` not `Promise<void>`.

**Severity:** high

**Replacement:**
```typescript
async update(
    provider: Provider,
    appId: AppId,
    originalId?: string,
): Promise<boolean> {
    return await invoke("update_provider", {
        provider,
        app: appId,
        originalId,
    });
},
```

---

## Finding 4 — `providersApi.remove()` does not exist; actual method is `delete()`

**Note location:** §5.2, lines 4997–4998
**Quoted claim:**
```typescript
async remove(providerId: string): Promise<void> {
    return await invoke("delete_provider", { providerId });
},
```

**Verdict:** wrong

**Source evidence:** `src/lib/api/providers.ts:78-80`
```typescript
async delete(id: string, appId: AppId): Promise<boolean> {
    return await invoke("delete_provider", { id, app: appId });
},
```

Errors: method name is `delete` not `remove`; requires `appId` as second parameter; return type is `Promise<boolean>` not `Promise<void>`; invoke payload uses `id` not `providerId`.

**Severity:** high

**Replacement:**
```typescript
async delete(id: string, appId: AppId): Promise<boolean> {
    return await invoke("delete_provider", { id, app: appId });
},
```

---

## Finding 5 — `providersApi.switch()` parameter names and order wrong

**Note location:** §5.2, lines 5000–5001
**Quoted claim:**
```typescript
async switch(appType: AppId, providerId: string): Promise<SwitchResult> {
    return await invoke("switch_provider", { appType, providerId });
},
```

**Verdict:** wrong

**Source evidence:** `src/lib/api/providers.ts:90-92`
```typescript
async switch(id: string, appId: AppId): Promise<SwitchResult> {
    return await invoke("switch_provider", { id, app: appId });
},
```

Parameter order reversed. Invoke payload uses `{ id, app: appId }` not `{ appType, providerId }`.

**Severity:** high

**Replacement:**
```typescript
async switch(id: string, appId: AppId): Promise<SwitchResult> {
    return await invoke("switch_provider", { id, app: appId });
},
```

---

## Finding 6 — `proxyApi.updateProxyConfigForApp()` has fabricated `appType` parameter

**Note location:** §5.2, lines 4698–4699
**Quoted claim:**
```typescript
async updateProxyConfigForApp(appType: string, config: AppProxyConfig): Promise<void> {
    return invoke("update_proxy_config_for_app", { appType, config });
},
```

**Verdict:** wrong

**Source evidence:** `src/lib/api/proxy.ts:92-94`
```typescript
async updateProxyConfigForApp(config: AppProxyConfig): Promise<void> {
    return invoke("update_proxy_config_for_app", { config });
},
```

The method takes only `config: AppProxyConfig`. The `appType` parameter does not exist. The `appType` is embedded inside the `AppProxyConfig` struct.

**Severity:** high

**Replacement:**
```typescript
async updateProxyConfigForApp(config: AppProxyConfig): Promise<void> {
    return invoke("update_proxy_config_for_app", { config });
},
```

---

## Finding 7 — `UseSettingsResult` interface omits 8 members

**Note location:** §5.2, lines 4257–4269
**Quoted claim:** Interface shows 10 members ending at `browseDirectory`.

**Verdict:** wrong

**Source evidence:** `src/hooks/useSettings.ts:21-45`

Actual interface has 18 members. The notes omit:
- `updateAppConfigDir: (value?: string) => void` (line 31)
- `browseAppConfigDir: () => Promise<void>` (line 33)
- `resetDirectory: (app: DirectoryAppId) => Promise<void>` (line 34)
- `resetAppConfigDir: () => Promise<void>` (line 35)
- `saveSettings: (overrides?, options?) => Promise<SaveResult | null>` (lines 36-39)
- `autoSaveSettings: (updates) => Promise<SaveResult | null>` (lines 40-42)
- `resetSettings: () => void` (line 43)
- `acknowledgeRestart: () => void` (line 44)

**Severity:** medium — anyone implementing a hook consumer would miss 8 available methods.

**Replacement:** Replace the truncated interface with the full version from `src/hooks/useSettings.ts:21-45`.

---

## Finding 8 — `UseImportExportResult` interface omits 2 members

**Note location:** §5.2, lines 4216–4225
**Quoted claim:** Interface shows 8 members.

**Verdict:** wrong

**Source evidence:** `src/hooks/useImportExport.ts:18-29`

Actual interface has 10 members. Missing:
- `clearSelection: () => void` (line 25)
- `resetStatus: () => void` (line 28)

**Severity:** low

---

## Finding 9 — Cross-chapter: useProxyStatus polling interval inconsistency

**Note location:** §1.3 line 206 says "每 5 秒"; §5.2 line 4136 says "每 2 秒"

**Verdict:** wrong (ch1 is wrong, ch5 is correct)

**Source evidence:** `src/hooks/useProxyStatus.ts:28`
```typescript
refetchInterval: (query) => (query.state.data?.running ? 2000 : false),
```

Actual polling is 2000ms = 2 seconds when running, `false` when not. The ch5 claim of "每 2 秒" is correct. The ch1 claim of "每 5 秒" is wrong.

**Severity:** medium (ch1 issue, flagged here because both reference the same hook)

---

## Finding 10 — `proxyApi` description is incomplete (missing 2 method groups)

**Note location:** §5.2, line 4703
**Quoted claim:** "4 个 API 分组：代理服务器控制、接管状态、全局代理配置、每应用代理配置"

**Verdict:** wrong

**Source evidence:** `src/lib/api/proxy.ts:1-121`

Actual `proxyApi` has 6 groups, not 4:
1. 代理服务器控制 (lines 12-45)
2. 接管状态 (lines 47-60)
3. Legacy 代理配置 (lines 62-72) — `getProxyConfig`, `updateProxyConfig`
4. v3+ 全局/应用级配置 (lines 74-94)
5. 计费默认配置 (lines 96-109) — `getDefaultCostMultiplier`, `setDefaultCostMultiplier`
6. 计费模式来源 (lines 111-119) — `getPricingModelSource`, `setPricingModelSource`

Also missing from notes: `setProxyTakeoverForApp()` (line 55).

**Severity:** medium

**Replacement:** "6 个 API 分组：代理服务器控制、接管状态、Legacy 代理配置（v2 兼容）、v3+ 全局/应用级配置、计费默认配置、计费模式来源"

---

## Finding 11 — Internal inconsistency: hooks table vs detail sections for line counts

**Note location:** §5.2, multiple lines
**Quoted claims vs actual:**

| Hook | Table (§5.2) | Detail section | Actual (read tool) |
|------|-------------|----------------|-------------------|
| useDragSort | 119 (line 4143) | 120 (line 4157) | 120 (file ends at line 120, no trailing newline) |
| useSkills | 358 (line 4135) | 359 (line 4229) | 359 (file ends at line 359, no trailing newline) |
| useMcp | 74 (line 4145) | 75 (line 4170) | 75 (file ends at line 75, no trailing newline) |
| useGlobalProxy | 109 (line 4144) | 110 (line 4175) | 110 (file ends at line 110, no trailing newline) |
| useOpenClaw | 144 (line 4141) | 145 (line 4186) | 145 (file ends at line 145, no trailing newline) |
| useHermes | 174 (line 4139) | 175 (line 4201) | 175 (file ends at line 175, no trailing newline) |
| useStreamCheck | 140 (line 4142) | 141 (line 4181) | 141 (file ends at line 141, no trailing newline) |

`wc -l` counts newline characters, so files without trailing newline report N-1. The `read` tool confirms the detail sections are correct in all cases. The table consistently undercounts by 1.

**Verdict:** wrong (internal inconsistency — table values are off by 1)

**Severity:** low — line counts are approximate, but the inconsistency is confusing.

---

## Finding 12 — `failover.ts` `useResetCircuitBreaker` code snippet uses fabricated placeholders

**Note location:** §5.2, lines 4550–4562
**Quoted claim:**
```typescript
export function useResetCircuitBreaker() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ providerId, appType }) =>
            failoverApi.resetCircuitBreaker(providerId, appType),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["providerHealth", ...] });
            queryClient.invalidateQueries({ queryKey: ["providers", ...] });
            queryClient.invalidateQueries({ queryKey: ["proxyStatus"] });
        },
    });
}
```

**Verdict:** ambiguous

**Source evidence:** `src/lib/query/failover.ts:28-38` — the function exists and has the same shape, but the `onSuccess` uses `...` spread placeholders in query keys that are not valid TypeScript. The actual code has typed query key arrays.

**Severity:** low — the shape is correct enough to be useful, but the `...` placeholders are not valid TypeScript.

---

## Finding 13 — `mcpApi` description omits `deleteUnifiedServer` and `importFromApps`

**Note location:** §5.2, lines 4914–4948
**Quoted claim:** Notes show the unified v3.7.0+ API methods.

**Verdict:** ok (partially)

The notes correctly describe the unified methods. However, the actual file (`src/lib/api/mcp.ts`) also has current (non-deprecated) methods not listed:
- `deleteUnifiedServer()` — delete via unified API
- `importFromApps()` — import MCP servers from all apps

These are referenced by hooks (`useDeleteMcpServer`, `useImportMcpFromApps`) but not in the notes API listing.

**Severity:** low

---

## Finding 14 — `providersApi` table description mentions `remove` instead of `delete`

**Note location:** §5.2, line 4638
**Quoted claim:** "Provider API（getAll, getCurrent, add, update, remove, switch）"

**Verdict:** wrong

**Source evidence:** `src/lib/api/providers.ts:78` — method is named `delete`, not `remove`.

**Severity:** low (table entry vs code block)

**Replacement:** "Provider API（getAll, getCurrent, add, update, delete, switch）"

---

## Finding 15 — Ch1 state management claims are stale/wrong

**Note location:** §1.3, lines 200-213
**Quoted claims:**
- `App.tsx (1604 行)` — actual: 1605 lines (file ends at line 1605 per read tool, wc -l reports 1604 due to no trailing newline)
- `useSettings.ts (512 行)` — actual: 505 (wc -l) / 506 (read tool)
- `useProxyStatus.ts (185 行)` — actual: 245 (wc -l) / 246 (read tool)
- `useDirectorySettings.ts (275 行)` — actual: 373 (wc -l) / 374 (read tool)
- `useDragSort.ts (95 行)` — actual: 119 (wc -l) / 120 (read tool)
- `useProxyStatus() ← 轮询代理状态（每 5 秒）` — actual: 2 seconds (2000ms)

**Verdict:** stale

All five hook line counts are significantly wrong. The useProxyStatus polling interval is wrong (5s vs 2s).

**Severity:** medium — these are in ch1 but the hook line counts are so far off they could mislead someone estimating code complexity.

---

## Summary

| # | Finding | Verdict | Severity |
|---|---------|---------|----------|
| 1 | `currentView` init code fabricated | wrong | high |
| 2 | `providersApi.add()` signature fabricated | wrong | high |
| 3 | `providersApi.update()` signature fabricated | wrong | high |
| 4 | `providersApi.remove()` → actual is `delete()` | wrong | high |
| 5 | `providersApi.switch()` param order wrong | wrong | high |
| 6 | `proxyApi.updateProxyConfigForApp()` extra param | wrong | high |
| 7 | `UseSettingsResult` missing 8 members | wrong | medium |
| 8 | `UseImportExportResult` missing 2 members | wrong | low |
| 9 | Cross-chapter polling interval conflict (ch1 wrong) | wrong | medium |
| 10 | `proxyApi` groups undercounted (4 vs 6) | wrong | medium |
| 11 | Hooks table vs detail line count inconsistency | wrong | low |
| 12 | `failover.ts` snippet uses fabricated placeholders | ambiguous | low |
| 13 | `mcpApi` missing `deleteUnifiedServer`, `importFromApps` | ok (partial) | low |
| 14 | `providersApi` table says `remove` not `delete` | wrong | low |
| 15 | Ch1 hook line counts all stale/wrong | stale | medium |
