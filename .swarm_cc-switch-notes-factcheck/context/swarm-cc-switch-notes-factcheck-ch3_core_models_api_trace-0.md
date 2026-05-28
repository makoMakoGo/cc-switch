{
  "findings_count": 7,
  "high_severity": 3,
  "medium_severity": 0,
  "low_severity": 4,
  "ok_claims": 27,
  "key_issues": [
    "UsageScript struct missing 5 of 11 fields (access_token, user_id, template_type, auto_query_interval, coding_plan_provider)",
    "AppSettings struct truncated to 10 of 38 fields",
    "AppSettings webdav field has wrong name (webdav vs webdav_sync) and wrong type (WebDavSyncSettings vs Option<WebDavSyncSettings>)"
  ],
  "output_file": "autoresearch/cc-switch-notes/07-ch3-core-api-findings.md"
}