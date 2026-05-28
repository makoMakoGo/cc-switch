{
  "findings_file": "autoresearch/cc-switch-notes/16-ch5-ipc-state-findings.md",
  "total_findings": 15,
  "high_severity": 6,
  "medium_severity": 5,
  "low_severity": 4,
  "summary": "Chapter 5 has 6 high-severity factual errors, all in §5.1 and §5.2. The `providersApi` signatures (add, update, delete, switch) are fabricated — parameter order, types, method names, and return types are all wrong. The `currentView` initialization code is fabricated (wrong localStorage key, missing validation function). `proxyApi.updateProxyConfigForApp()` has a nonexistent `appType` parameter. `UseSettingsResult` is missing 8 of 18 interface members. `UseImportExportResult` is missing 2 members. Cross-chapter: ch1 §1.3 hook line counts are all stale/wrong, and useProxyStatus polling is claimed as 5s but actual is 2s."
}