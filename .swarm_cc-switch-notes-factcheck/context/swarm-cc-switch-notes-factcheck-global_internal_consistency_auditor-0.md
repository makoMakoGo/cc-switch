{
  "findings_file": "autoresearch/cc-switch-notes/24-global-consistency-findings.md",
  "total_findings": 13,
  "high_severity": 3,
  "medium_severity": 4,
  "low_severity": 6,
  "summary": "Found 13 consistency issues. High: DAO bullet sizes are wrong (service-module sizes pasted instead), massive verbatim duplication (~7100 lines repeated 6-7x), terminology inconsistency. Medium: duplicate heading '### 4.3' at lines 3877/3964, commands/mod.rs module count 33 claimed vs 31 actual, useProxyStatus polling 5s claimed vs 2s actual. Low: stale file sizes for settings.rs, services/proxy.rs, claude_desktop_config.rs; verified correct claims for ProxyState (10 fields), RequestForwarder (16 fields), lib.rs (34 modules), command count (271)."
}