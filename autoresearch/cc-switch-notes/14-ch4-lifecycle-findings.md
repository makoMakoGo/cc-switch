# Chapter 4 Lifecycle Findings

Goal: Verify ProxyServer lifecycle, ProxyState, startup/shutdown, takeover, and restore behavior.

---

## Finding 1: handlers/ is a file, not a directory

**Note location**: 4.1 proxy/ 目录结构, line 3673

**Quoted claim**:
```
├── handlers/           # 请求处理器
```

**Verdict**: hallucination

**Source evidence**: 
- `src-tauri/src/proxy/handlers.rs` is a single file (1267 lines, 43.6KB), not a directory
- Directory listing shows `handlers.rs` at file level
- Line 3893 in notes correctly refers to `handlers.rs` (not `handlers/`)

**Exact replacement text**:
```
├── handlers.rs         # 1267 行，请求处理器
```

**Severity**: medium (structural misrepresentation)

---

## Finding 2: ProxyConfig fields verified ✓

**Note location**: 4.2 ProxyConfig 配置

**Quoted claim**:
```rust
pub struct ProxyConfig {
    pub listen_address: String,
    pub listen_port: u16,
    pub max_retries: u8,
    pub request_timeout: u64,
    pub enable_logging: bool,
    pub live_takeover_active: bool,
    pub streaming_first_byte_timeout: u64,
    pub streaming_idle_timeout: u64,
    pub non_streaming_timeout: u64,
}
```

**Verdict**: ok

**Source evidence**: `src-tauri/src/proxy/types.rs:5-28` matches exactly.

**Severity**: n/a

---

## Finding 3: ProxyConfig defaults verified ✓

**Note location**: 4.2

**Claims verified**:
- Default listen address `127.0.0.1` at `types.rs:45` ✓
- Default port `15721` at `types.rs:46` ✓
- `max_retries = 3` at `types.rs:47` ✓
- `streaming_first_byte_timeout = 60` at `types.rs:51` ✓
- `streaming_idle_timeout = 120` at `types.rs:52` ✓
- `non_streaming_timeout = 600` at `types.rs:53` ✓
- `request_timeout` deprecated at `types.rs:12` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 4: ProxyServer struct verified ✓

**Note location**: 4.1.3

**Claims verified**:
- `start()` at `server.rs:94` ✓
- Check if already running (`shutdown_tx.read().await.is_some()`) at `server.rs:96` ✓
- Parse listen address at `server.rs:100-103` ✓
- Create shutdown channel (`oneshot::channel()`) at `server.rs:106` ✓
- Build router (`build_router()`) at `server.rs:109` ✓
- Bind TCP listener at `server.rs:112-114` ✓
- Set global proxy port at `server.rs:119` ✓
- Update status (`running = true`) at `server.rs:125-129` ✓
- Spawn HTTP/1.1 accept loop at `server.rs:137` ✓
- `preserve_header_case(true)` at `server.rs:191` ✓

- `stop()` at `server.rs:221` ✓
- Send shutdown signal at `server.rs:223-224` ✓
- Wait for server task with 5-second timeout at `server.rs:230-231` ✓
- Update status (`running = false`) at `server.rs:207` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 5: ProxyState struct verified ✓

**Note location**: 4.3

**Claims verified** (from `server.rs:34-51`):
- `db: Arc<Database>` ✓
- `config: Arc<RwLock<ProxyConfig>>` ✓
- `status: Arc<RwLock<ProxyStatus>>` ✓
- `start_time: Arc<RwLock<Option<Instant>>>` ✓
- `current_providers: Arc<RwLock<HashMap<String, (String, String)>>>` ✓
- `provider_router: Arc<ProviderRouter>` ✓
- `gemini_shadow: Arc<GeminiShadowStore>` ✓
- `codex_chat_history: Arc<CodexChatHistoryStore>` ✓
- `app_handle: Option<tauri::AppHandle>` ✓
- `failover_manager: Arc<FailoverSwitchManager>` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 6: RequestForwarder struct verified ✓

**Note location**: 4.1.1

**Claims verified** (from `forwarder.rs:89-122`):
- All 17 fields match ✓
- `max_attempts = max_retries + 1` at `forwarder.rs:147` ✓
- `non_streaming_timeout` is `Duration` type ✓
- `streaming_first_byte_timeout` is `Duration` type ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 7: ActiveConnectionGuard RAII verified ✓

**Note location**: 4.1

**Claims verified** (from `forwarder.rs:61-87`):
- Struct with `status: Arc<RwLock<ProxyStatus>>` ✓
- `acquire()` increments `active_connections` ✓
- `Drop` impl uses `tokio::spawn` for async decrement ✓
- Uses `saturating_sub(1)` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 8: Placeholder constants verified ✓

**Note location**: 4.1

**Claims verified**:
- `PROXY_AUTH_PLACEHOLDER` at `forwarder.rs:35` = `"PROXY_MANAGED"` ✓
- `PROXY_TOKEN_PLACEHOLDER` at `services/proxy.rs:22` = `"PROXY_MANAGED"` ✓
- Both have same value but different names ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 9: Module file count verified ✓

**Note location**: 4.3, line 3892

**Quoted claim**:
```
proxy/ 目录统计：34 个模块文件 + 24 个 providers/ 文件 = 58 个 Rust 文件
```

**Verdict**: ok

**Source evidence**:
- `find src-tauri/src/proxy -name "*.rs" | wc -l` = 58
- `find src-tauri/src/proxy/providers -name "*.rs" | wc -l` = 24
- 58 - 24 = 34 (non-provider files)

**Severity**: n/a

---

## Finding 10: Line counts - minor discrepancies

**Note location**: 4.1

**Claims vs actual**:
- `forwarder.rs`: notes 3100, actual 3100 ✓
- `server.rs`: notes 388, actual 388 ✓
- `circuit_breaker.rs`: notes 495, actual 495 ✓
- `provider_router.rs`: notes 523, actual 523 ✓
- `session.rs`: notes 627, actual 626 (off by 1)
- `sse.rs`: notes 346, actual 345 (off by 1)
- `model_mapper.rs`: notes 313, actual 312 (off by 1)
- `transform.rs`: notes 1626, actual 1625 (off by 1)
- `transform_codex_chat.rs`: notes 2074, actual 2073 (off by 1)

**Verdict**: stale (minor, off by 1 line each)

**Source evidence**: `wc -l` output

**Exact replacement text**: Update line counts to match actual `wc -l` output.

**Severity**: low (off by 1 line is negligible)

---

## Finding 11: File sizes verified ✓

**Note location**: 4.1

**Claims vs actual** (in KB):
- `forwarder.rs`: notes 122.1, actual 122.2 ✓
- `transform_codex_chat.rs`: notes 71.1, actual 71.1 ✓
- `transform_gemini.rs`: notes 78.1, actual 78.1 ✓
- `transform_responses.rs`: notes 61.5, actual 61.5 ✓
- `transform.rs`: notes 58.3, actual 58.3 ✓
- `copilot_optimizer.rs`: notes 57.9, actual 57.9 ✓
- `thinking_rectifier.rs`: notes 23.0, actual 23.1 (off by 0.1)
- `thinking_budget_rectifier.rs`: notes 11.1, actual 11.1 ✓
- `body_filter.rs`: notes 10.5, actual 10.5 ✓
- `model_mapper.rs`: notes 10.4, actual 10.4 ✓

**Verdict**: ok (thinking_rectifier.rs off by 0.1KB is negligible)

**Severity**: n/a

---

## Finding 12: ProxyError enum verified ✓

**Note location**: 4.3, line 3878

**Quoted claim**: "20 个变体"

**Verdict**: ok

**Source evidence**: `src-tauri/src/proxy/error.rs:10-77` contains exactly 20 variants:
1. AlreadyRunning
2. NotRunning
3. BindFailed(String)
4. StopTimeout
5. StopFailed(String)
6. ForwardFailed(String)
7. NoAvailableProvider
8. AllProvidersCircuitOpen
9. NoProvidersConfigured
10. ProviderUnhealthy(String)
11. UpstreamError { status: u16, body: Option<String> }
12. MaxRetriesExceeded
13. DatabaseError(String)
14. ConfigError(String)
15. TransformError(String)
16. InvalidRequest(String)
17. Timeout(String)
18. StreamIdleTimeout(u64)
19. AuthError(String)
20. Internal(String)

**Severity**: n/a

---

## Finding 13: CircuitBreaker struct verified ✓

**Note location**: 4.4

**Claims verified** (from `circuit_breaker.rs:76-93`):
- `state: Arc<RwLock<CircuitState>>` ✓
- `consecutive_failures: Arc<AtomicU32>` ✓
- `consecutive_successes: Arc<AtomicU32>` ✓
- `total_requests: Arc<AtomicU32>` ✓
- `failed_requests: Arc<AtomicU32>` ✓
- `last_opened_at: Arc<RwLock<Option<Instant>>>` ✓
- `config: Arc<RwLock<CircuitBreakerConfig>>` ✓
- `half_open_requests: Arc<AtomicU32>` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 14: CircuitBreakerConfig defaults verified ✓

**Note location**: 4.4

**Claims verified** (from `circuit_breaker.rs:63-72`):
- `failure_threshold: 4` ✓
- `success_threshold: 2` ✓
- `timeout_seconds: 60` ✓
- `error_rate_threshold: 0.6` ✓
- `min_requests: 10` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 15: AllowResult struct verified ✓

**Note location**: 4.4

**Claims verified** (from `circuit_breaker.rs:100-103`):
- `allowed: bool` ✓
- `used_half_open_permit: bool` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 16: ProviderRouter struct verified ✓

**Note location**: 4.3

**Claims verified** (from `provider_router.rs:16-21`):
- `db: Arc<Database>` ✓
- `circuit_breakers: Arc<RwLock<HashMap<String, Arc<CircuitBreaker>>>>` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 17: Routing logic verified ✓

**Note location**: 4.3

**Claims verified** (from `provider_router.rs:37`):
- `select_providers()` method ✓
- Failover off: returns only current provider ✓
- Failover on: returns providers in queue order (P1 → P2 → ...) ✓
- Circuit breaker key format: `app_type:provider_id` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 18: ClientFormat enum verified ✓

**Note location**: 4.1

**Claims verified** (from `session.rs:19-32`):
- Claude, Codex, OpenAI, Gemini, GeminiCli, Unknown variants ✓
- `from_path()` at `session.rs:37` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 19: RequestContext struct - partial match

**Note location**: 4.3, lines 3916-3929

**Quoted claim**:
```rust
pub struct RequestContext {
    pub start_time: Instant,
    pub app_config: AppProxyConfig,
    pub provider: Provider,
    providers: Vec<Provider>,
    pub current_provider_id: String,
    pub request_model: String,
    pub tag: &'static str,
    pub session_id: String,
    pub rectifier_config: RectifierConfig,
    pub optimizer_config: OptimizerConfig,
}
```

**Verdict**: ambiguous (subset shown)

**Source evidence**: `handler_context.rs:35-68` shows 13 fields, notes show 10. Missing fields:
- `app_type_str: &'static str`
- `app_type: AppType`
- `session_client_provided: bool`
- `copilot_optimizer_config: CopilotOptimizerConfig`

**Exact replacement text**: Add missing fields to the struct definition.

**Severity**: low (documentation shows subset, not misleading)

---

## Finding 20: StreamingTimeoutConfig verified ✓

**Note location**: 4.3

**Claims verified** (from `handler_context.rs:19-24`):
- `first_byte_timeout: u64` ✓
- `idle_timeout: u64` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 21: SSE module verified ✓

**Note location**: 4.3

**Claims verified** (from `sse.rs:1-36`):
- `strip_sse_field()` at line 2 ✓
- `take_sse_block()` at line 8 ✓
- `append_utf8_safe()` at line 36 ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 22: Transform module functions verified ✓

**Note location**: 4.1

**Claims verified** (from `providers/transform.rs`):
- `strip_leading_anthropic_billing_header()` at line 18 ✓
- `is_openai_o_series()` at line 51 ✓
- `supports_reasoning_effort()` at line 62 ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 23: transform_codex_chat.rs verified ✓

**Note location**: 4.1

**Claims verified** (from `providers/transform_codex_chat.rs`):
- `EXTRA_CHAT_PASSTHROUGH_FIELDS` at line 20 ✓
- `responses_to_chat_completions()` at line 38 ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 24: ModelMapping struct verified ✓

**Note location**: 4.1

**Claims verified** (from `model_mapper.rs:10-15`):
- `haiku_model: Option<String>` ✓
- `sonnet_model: Option<String>` ✓
- `opus_model: Option<String>` ✓
- `default_model: Option<String>` ✓
- `from_provider()` at line 19 ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 25: Error classification verified ✓

**Note location**: 4.1.2, line 3831

**Claims verified** (from `forwarder.rs:223-227`):
- Provider errors: `Timeout`, `ForwardFailed`, `UpstreamError >= 500` → continue failover ✓
- Client errors: `UpstreamError < 500` → return immediately ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 26: forward_with_retry verified ✓

**Note location**: 4.1.2

**Claims verified** (from `forwarder.rs:275-303`):
- Function signature matches ✓
- Acquires `ActiveConnectionGuard` ✓
- Increments `total_requests` ✓
- Updates `last_request_at` ✓
- Injects guard into result ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 27: forward_with_retry_inner verified ✓

**Note location**: 4.1.2

**Claims verified** (from `forwarder.rs:315-341`):
- Gets adapter at line 326 ✓
- Checks empty providers at line 329 ✓
- Single provider bypasses circuit breaker at line 341 ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 28: Takeover mechanism verified ✓

**Note location**: 4.5

**Claims verified**:
- `set_takeover_for_app()` at `services/proxy.rs:535` ✓
- `hot_switch_provider()` at `services/proxy.rs:1811` ✓
- `stop_with_restore_keep_state()` at `services/proxy.rs:1027` ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 29: Restore mechanism verified ✓

**Note location**: 4.5

**Claims verified** (from `lib.rs`):
- `cleanup_before_exit()` at line 1513 ✓
- `stop_with_restore_keep_state()` at line 1531 ✓
- `restore_proxy_state_on_startup()` at line 1558 ✓
- Only restores claude, codex, gemini at line 1561 ✓

**Verdict**: ok

**Severity**: n/a

---

## Finding 30: handlers.rs function line numbers verified ✓

**Note location**: 4.3

**Claims verified** (from `handlers.rs`):
- `health_check()` at line 49 ✓
- `get_status()` at line 60 ✓
- `handle_messages()` at line 74 ✓
- `handle_claude_desktop_messages()` at line 81 ✓
- `handle_claude_desktop_models()` at line 97 ✓
- `handle_messages_for_app()` at line 113 ✓

**Verdict**: ok

**Severity**: n/a

---

## Summary

**Total findings**: 30
- **Hallucination**: 1 (Finding 1 - handlers/ directory claim)
- **Stale**: 1 (Finding 10 - line counts off by 1)
- **Ambiguous**: 1 (Finding 19 - RequestContext subset)
- **Ok**: 27 (all other claims verified)

**Critical issues**: 0
**Medium issues**: 1 (Finding 1 - structural misrepresentation)
**Low issues**: 2 (Finding 10 - line counts, Finding 19 - struct subset)

**Overall assessment**: Chapter 4 is highly accurate. The single hallucination about `handlers/` being a directory (vs `handlers.rs` file) is a structural error but does not affect understanding of the lifecycle mechanisms. All lifecycle, startup/shutdown, takeover, and restore behavior claims are verified against source code. Line counts have minor ±1 discrepancies which are negligible.
