{
  "findings_file": "autoresearch/cc-switch-notes/10-ch3-database-findings.md",
  "total_findings": 20,
  "high_severity": 6,
  "medium_severity": 9,
  "low_severity": 5,
  "findings_summary": {
    "f1_proxy_config_missing_4_columns": {
      "verdict": "stale",
      "severity": "high",
      "evidence": "schema.rs:124-137 has enable_logging, streaming_idle_timeout, created_at, updated_at not in notes"
    },
    "f2_session_log_sync_missing_column": {
      "verdict": "stale",
      "severity": "high",
      "evidence": "schema.rs:284 has last_synced_at NOT NULL not in notes"
    },
    "f3_proxy_request_logs_missing_2_cost_columns": {
      "verdict": "stale",
      "severity": "medium",
      "evidence": "schema.rs:190 has cache_read_cost_usd and cache_creation_cost_usd not in notes"
    },
    "f4_init_error_handling_wrong": {
      "verdict": "wrong",
      "severity": "high",
      "evidence": "mod.rs:143-149 uses if-let-Err pattern not ? as notes claim"
    },
    "f5_missing_auto_vacuum_step": {
      "verdict": "stale",
      "severity": "medium",
      "evidence": "mod.rs:138-140 has ensure_incremental_auto_vacuum() between migrations and pricing"
    },
    "f6_missing_backup_step": {
      "verdict": "stale",
      "severity": "medium",
      "evidence": "mod.rs:122-135 has pre-migration backup logic not in notes"
    },
    "f7_f13_file_size_errors": {
      "verdict": "wrong",
      "severity": "medium",
      "count": 7,
      "evidence": "mod.rs listed as 1.1KB actual 8.9KB; schema.rs listed as 11.7KB actual 77.8KB; migration.rs listed as 28.3KB actual 9.2KB; plus 4 DAO files with wrong sizes contradicting their own tables"
    },
    "f14_wrong_dao_module_names": {
      "verdict": "wrong",
      "severity": "high",
      "evidence": "5 of 12 names are wrong: mcp_servers->mcp, proxy_config+proxy_request_logs->proxy, session_usage/subscription/usage_cache dont exist in dao/"
    },
    "f15_commands_count_off": {
      "verdict": "wrong",
      "severity": "low",
      "evidence": "grep counts 31 not 33"
    },
    "f16_services_table_sizes_off_30x_to_100x": {
      "verdict": "wrong",
      "severity": "high",
      "evidence": "11 services file sizes off by 30-100x (e.g. omo.rs listed 560B actual 19.1KB); 3 modules entirely missing"
    },
    "f17_internal_size_contradictions": {
      "verdict": "wrong",
      "severity": "medium",
      "evidence": "Inline module list and table in same section give different sizes for same files"
    },
    "f18_failover_drop_index_missing": {
      "verdict": "ambiguous",
      "severity": "low"
    },
    "f19_proxy_request_logs_index_incomplete": {
      "verdict": "stale",
      "severity": "low"
    },
    "f20_services_table_incomplete": {
      "verdict": "wrong",
      "severity": "medium",
      "evidence": "Table header says 25 submodules but first table shows only 1 entry"
    }
  }
}