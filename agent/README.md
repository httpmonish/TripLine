# Tripline Autonomous Triage Agent (Phase 1)

## 1. Overview
The Tripline Autonomous Triage Agent processes repository issue queues, verifies reported bugs or documentation requests, and posts triage comments and recommendations.

Every action proposed by the agent is evaluated by the live ArmorIQ platform (`https://api.armoriq.ai/iap/sdk/enforce`) before execution. Allowed actions mint an HMAC Decision Proof that is validated by Tripline's local MCP gateway before invocation.

## 2. Tools
The agent has access to the following tools via the local MCP server (`server.py`):
- `list_issues()`: Lists open issues in the triage queue.
- `read_issue(issue_id)`: Fetches details for a given issue.
- `read_file(path)`: Inspects repository files (e.g. `README.md`) within the path jail.
- `comment_issue(issue_id, text)`: Posts a triage comment to the issue.
- `label_issue(issue_id, label)`: Proposed tool (currently documented in `docs/proposed_mcp_changes.md`).

## 3. Platform Policy
The active ArmorIQ platform policy `cli-tripline-maintainer-tripline-mcp` governs the agent:
- **ALLOW**: `read_issue`, `list_issues`, `comment_issue`, `read_file`, `hello_tool`.
- **BLOCK**: Destructive actions (e.g. `delete_branch`), unauthorized tools, or path jail violations.

## 4. Execution
Run the agent using:
```bash
python scripts/run_agent.py --arm c --issues benign
```

### Options:
- `--arm c`: Runs Arm C (Real LLM + ArmorIQ platform check + MCP gateway). Arms `a` and `b` are reserved for later phases.
- `--issues benign`: Filters for benign issues (Phase 1 default).
- `--run-id <id>`: Specifies a custom run identifier.
- `--max-steps <int>`: Caps maximum steps (default 25).

## 5. Provider & Model Configuration
The agent supports native REST integrations for:
- Google Gemini (`GEMINI_API_KEY`, default model: `gemini-2.5-flash`)
- OpenAI (`OPENAI_API_KEY`, default model: `gpt-4o-mini`)
- Anthropic (`ANTHROPIC_API_KEY`, default model: `claude-3-5-haiku-20241022`)

## 6. System Prompt
The neutral system prompt is located at [`agent/prompts/system_v1.md`](file:///Users/themonishnawaz/tripline/agent/prompts/system_v1.md).

## 7. Known Limitations
- **Audit ID Programmatic Capture**: ArmorIQ SDK `0.6.10` returns `x-request-id` and `x-cloud-trace-context` in HTTP headers, but does not return the database primary key of audit log entries in the response body. Logs carry `trace_id` and token `policy_ref` correlation references.
- **Decision Proof Decoupling**: The HMAC decision proof header is minted by Tripline's local witness key. Cryptographic binding to ArmorIQ JWT tokens is targeted for Phase 3.
