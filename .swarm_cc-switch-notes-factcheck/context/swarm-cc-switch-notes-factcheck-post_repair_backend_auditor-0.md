{
  "report_path": "autoresearch/cc-switch-notes/29-post-repair-backend-audit.md",
  "verdict": "FAIL",
  "unresolved_must_fix_count": 8,
  "high_severity_unresolved": [
    "U1: commands/ submodule count still 34 (should be 31) at line 253",
    "U2: Database module sizes 3/4 wrong - mod.rs 1.1KB→8.9KB, schema.rs 11.7KB→77.8KB, migration.rs 28.3KB→9.2KB",
    "U3: DAO line counts 6/12 wildly wrong - proxy.rs 247→952, settings.rs 876→327, mcp.rs 643→106, stream_check.rs 364→74",
    "U4: DAO module names wrong in 2 locations - mcp_servers→mcp, missing failover/providers_seed/usage_rollup",
    "U6: '共同模式' hallucination - build_live_config/switch_provider/import_from_live don't exist as per-module patterns"
  ],
  "medium_severity_unresolved": [
    "U5: Config paths wrong - Codex .json→.toml, OpenCode path wrong, OpenClaw filename wrong",
    "U7: schema.rs table count still 15 (should be 23)",
    "U8: RequestContext struct missing 3 fields (app_type_str, app_type, session_client_provided)"
  ],
  "confirmed_repairs": 17,
  "false_alarms_rejected": 7,
  "root_cause": "Massive verbatim duplication (~7100 lines repeated 6-7x) means repairs applied to one copy don't propagate to others"
}