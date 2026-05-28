# Chapter 5 Component/Config Findings

## Finding 1: UseSettingsResult interface missing 6 fields
- **Location**: 第 5 章 / 5.2 hooks/ — useSettings 接口
- **Claim**: `UseSettingsResult` has 10 fields
- **Verdict**: wrong
- **Evidence**: `src/hooks/useSettings.ts:21-35` — actual has 15+ fields
- **Missing**: `updateAppConfigDir`, `browseAppConfigDir`, `resetDirectory`, `resetAppConfigDir`, `saveSettings`, `autoSaveSettings`
- **Severity**: HIGH

## Finding 2: UseImportExportResult interface missing 2 fields
- **Location**: 第 5 章 / 5.2 hooks/ — useImportExport
- **Claim**: `UseImportExportResult` has 8 fields
- **Verdict**: wrong
- **Evidence**: `src/hooks/useImportExport.ts:18-29` — actual has 10 fields
- **Missing**: `clearSelection`, `resetStatus`
- **Severity**: HIGH

## Finding 3: providersApi.add signature wrong
- **Location**: 第 5 章 / 5.2 hooks/ — providersApi
- **Claim**: `add(appId, provider: Omit<Provider, "id">): Promise<Provider>`
- **Verdict**: wrong
- **Evidence**: `src/lib/api/providers.ts:59-64` — actual: `add(provider: Provider, appId, addToLive?): Promise<boolean>`
- **Severity**: HIGH

## Finding 4: providersApi.update signature wrong
- **Location**: 第 5 章 / 5.2 hooks/ — providersApi
- **Claim**: `update(provider): Promise<void>`
- **Verdict**: wrong
- **Evidence**: `src/lib/api/providers.ts:66-73` — actual: `update(provider, appId, originalId?): Promise<boolean>`
- **Severity**: HIGH

## Finding 5: providersApi.remove method name wrong
- **Location**: 第 5 章 / 5.2 hooks/ — providersApi
- **Claim**: `remove(providerId): Promise<void>`
- **Verdict**: wrong
- **Evidence**: `src/lib/api/providers.ts:78-80` — actual: `delete(id, appId): Promise<boolean>`
- **Severity**: HIGH

## Finding 6: providersApi.switch signature wrong
- **Location**: 第 5 章 / 5.2 hooks/ — providersApi
- **Claim**: `switch(appType, providerId)`
- **Verdict**: wrong
- **Evidence**: `src/lib/api/providers.ts:91-93` — actual: `switch(id, appId)`
- **Severity**: MEDIUM

## Finding 7: Query layer file sizes all wrong
- **Location**: 第 5 章 / 5.2 hooks/ — 前端 Query 层
- **Claim**: 6 file sizes
- **Verdict**: wrong
- **Evidence**: `ls -la src/lib/query/*.ts`
- copilot.ts: 1.7K (notes: 5.9K), failover.ts: 7.9K (notes: 2.7K), usage.ts: 8.5K (notes: 6.0K), subscription.ts: 2.1K (notes: 0.6K), omo.ts: 2.6K (notes: 12.1K), proxy.ts: 6.5K (notes: 3.2K)
- **Severity**: MEDIUM

## Finding 8: Config preset file sizes slightly off
- **Location**: 第 5 章 / 5.3 config/
- **Verdict**: stale
- **Evidence**: `ls -la src/config/*ProviderPresets.ts`
- claudeDesktop: 27.0K (notes: 26.9K), hermes: 35.2K (notes: 35.1K), gemini: 9.3K (notes: 9.2K), total: 237.6K (notes: 237.3K)
- **Severity**: LOW

## Finding 9: Hook prose line counts off by +1 (10 hooks)
- **Location**: 第 5 章 / 5.2 hooks/
- **Verdict**: stale
- **Evidence**: `wc -l src/hooks/*.ts` — table values correct, prose adds +1
- useSkills 358, useHermes 174, useGlobalProxy 109, useOpenClaw 144, useImportExport 203, useDirectorySettings 373, useSettingsForm 203, usePromptActions 152, useDragSort 119, useStreamCheck 140
- **Severity**: LOW

## Finding 10-17: Various file line counts off by 1
- providers.ts 236 (237), mutations.ts 356 (357), queries.ts 155 (156), copilot.ts API 258 (259), proxy/types.rs 495 (496), omo.ts 433 (434), proxy.ts 140 (141), usage.ts 246 (247)
- **Severity**: LOW

## Finding 18: CopilotOptimizerConfig field name wrong
- **Location**: 第 5 章 / 5.2 hooks/ — CopilotOptimizerConfig
- **Claim**: `x_initiator: bool`
- **Verdict**: wrong
- **Evidence**: `src-tauri/src/proxy/types.rs:285` — actual: `request_classification: bool`
- **Severity**: MEDIUM

## Finding 19: hermesKeys missing memoryLimits key
- **Location**: 第 5 章 / 5.2 hooks/ — useHermes
- **Claim**: 4 keys
- **Verdict**: wrong
- **Evidence**: `src/hooks/useHermes.ts:26-32` — actual has 5 keys (includes `memoryLimits`)
- **Severity**: MEDIUM

## Finding 20: Component directories incomplete
- **Location**: 第 5 章 / 5.4
- **Claim**: 8 directories
- **Verdict**: ambiguous
- **Evidence**: `ls -1 src/components/` — actual: 17 directories
- **Severity**: LOW

## Finding 21: useGlobalProxy function names misleading
- **Location**: 第 5 章 / 5.2 hooks/
- **Claim**: testProxyUrl, getUpstreamProxyStatus, scanLocalProxies
- **Verdict**: ambiguous
- **Evidence**: `src/hooks/useGlobalProxy.ts:10-15` — these are imports, not hooks (actual: useTestProxy, useUpstreamProxyStatus, useScanProxies)
- **Severity**: LOW

## Finding 22: useStreamCheck states oversimplified
- **Location**: 第 5 章 / 5.2 hooks/
- **Claim**: operational/degraded/error
- **Verdict**: ambiguous
- **Evidence**: `src/hooks/useStreamCheck.ts:26-79` — actual has modelNotFound, quotaExceeded categories
- **Severity**: LOW

## Finding 23-24: Query file line counts off by 1
- usage.ts 319 (320), failover.ts 288 (289)
- **Severity**: LOW
