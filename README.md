# Zephyr Scale Data Center MCP Server

This project provides a Model Context Protocol (MCP) server for integrating with SmartBear Zephyr Scale Data Center (formerly TM4J).
It empowers LLM-based systems, specifically **[OpenCode](https://opencode.ai)**, to interact with your Jira Data Center test management data.

## Requirements

- **Python Version**: Python 3.10 or higher (when running from source).
- **Jira Instance**: Jira Data Center / Server with Zephyr Scale plugin.
- **Standalone Mode**: A pre-compiled executable (`dist/zephyr-scale-mcp`) is provided for zero-dependency deployment without requiring a local Python installation.

---

## Features

### Test Cases & Test Scripts
- **Get Test Case**: Retrieve details for a specific Zephyr Scale test case.
- **List / Search Test Cases**: Search for all test cases within a project.
- **Create Test Case**: Create a new test case with status, priority, owner, and labels.
- **Update Test Case**: Update fields on an existing test case.
- **Get Test Script**: Retrieve step-by-step test script instructions for a test case.
- **Create or Update Test Script**: Save step-by-step script steps for a test case.
- **Link Test to Issue (Traceability)**: Link a test case to a Jira issue key.

### Test Cycles & Executions
- **Get Test Cycle**: Fetch details for a specific test cycle/run.
- **Search Test Cycles**: Search for test cycles in a project.
- **Create Test Cycle**: Create a new test cycle/run with planned dates and description.
- **Update Test Cycle**: Update name, description, status, or folder for a test cycle.
- **Create Test Execution**: Execute a test case and log status (PASS, FAIL, WIP, BLOCKED).
- **Get Test Execution**: Retrieve result details for a specific execution ID.
- **List Test Executions**: List execution history for a specific test case.

### Test Plans, Folders, Environments & Statuses
- **Get Test Plan**: Retrieve test plan details.
- **Search Test Plans**: Search test plans within a project.
- **Create Test Plan**: Create a new test plan.
- **List Folders**: List folder structures (TEST_CASE, TEST_CYCLE, TEST_PLAN).
- **Create Folder**: Create new folders for organizing test assets.
- **List Environments**: Retrieve configured environment names for a project.
- **List Statuses**: Retrieve configured execution status options for a project.

---

## Environment Variables

Before running the server, configure the connection parameters:

- `ZEPHYR_BASE_URL`: **(Mandatory)** The Base URL to your Jira instance (e.g. `https://jira.yourcompany.com`). No default is provided.
- `ZEPHYR_PAT`: **(Mandatory)** Your Jira Personal Access Token (PAT) used for authentication. Alternatively, `JIRA_PAT`, `ZEPHYR_API_KEY`, or `JIRA_API_TOKEN` are accepted.
- `ZEPHYR_SSL_VERIFY`: Optional. Set to `false` to disable SSL verification. By default, the server validates certificates against the operating system's native certificate store (via `truststore`).

---

## API Coverage

Here is the current implementation status of Zephyr Scale Data Center APIs in this MCP server:

| API Endpoint | Method | MCP Tool | Status |
|---|---|---|---|
| `/testcase` | POST | `create_test_case` | ✅ PASS |
| `/testcase/{key}` | GET | `get_test_case` | ✅ PASS |
| `/testcase/{key}` | PUT | `update_test_case` | ✅ PASS |
| `/testcase/{key}` | DELETE | `delete_test_case` | ✅ PASS |
| `/testcase/search` | GET | `list_test_cases` | ✅ PASS |
| `/testcase/link-issues` | POST | `bulk_link_test_cases_to_issues` | ✅ PASS |
| `/testcase/{key}/issue` | POST | `link_test_to_issue` | ✅ PASS |
| `/testcase/{key}/testresult/latest` | GET | `get_latest_test_result` | ✅ PASS |
| `/testrun` | POST | `create_test_cycle` | ✅ PASS |
| `/testrun/{key}` | GET | `get_test_cycle` | ✅ PASS |
| `/testrun/{key}` | PUT | `update_test_cycle` | ⚠️ EXPERIMENTAL / UNSUPPORTED – Zephyr Scale Server v1 API has no official cycle-update endpoint; MCP tool always raises `UpdateNotSupportedError` |
| `/testrun/{key}` | DELETE | `delete_test_cycle` | ✅ PASS |
| `/testrun/search` | GET | `search_test_cycles` | ✅ PASS |
| `/testrun/{key}/testresults` | GET | `list_test_executions` | ✅ PASS |
| `/testrun/{key}/testresults/page` | GET | `list_test_executions_page` | ✅ PASS |
| `/testrun/{key}/testcase/{caseKey}/testresult` | POST | `create_test_execution_in_cycle` | ✅ PASS |
| `/testresult` | POST | `create_test_execution` | ✅ PASS |
| `/testresult/{key}` | GET | `get_test_execution` | ⚠️ BEST-EFFORT – numeric ID lookup not guaranteed; prefer `get_latest_test_result` / `list_test_executions` |
| `/testplan` | POST | `create_test_plan` | ✅ PASS (description omitted; v1 API does not reliably support it) |
| `/testplan/{key}` | GET | `get_test_plan` | ✅ PASS |
| `/testplan/{key}` | PUT | `update_test_plan` | ✅ PASS (description update omitted; v1 API does not reliably support it) |
| `/testplan/{key}` | DELETE | `delete_test_plan` | ✅ PASS |
| `/testplan/search` | GET | `search_test_plans` | ✅ PASS |
| `/folder` | POST | `create_folder` | ✅ PASS |
| `/folder/{id}` | PUT | `update_folder` | ✅ PASS |
| `/folder` | GET (UI-backed, undocumented) | `list_folders` | ⚠️ BEST-EFFORT (UI-backed; may return 404/500 on some versions) |
| `/environments` | GET | `list_environments` | ✅ PASS |
| `/environments` | POST | `create_environment` | ✅ PASS |
| `/issuelink/{issueKey}/testcases` | GET | `get_test_cases_for_issue` | ✅ PASS |
| Statuses (UI-backed, unofficial API) | GET | `list_statuses` | ⚠️ BEST-EFFORT (UI-backed; may return 404/500 on some versions) |

### Known limitations / experimental tools
Some tools rely on undocumented or UI-backed APIs and exhibit inconsistent behavior depending on your Zephyr Scale Data Center version:
- **`update_test_cycle` (Z13)**: Experimental/unsupported. Zephyr Scale Server v1 exposes no official cycle-update endpoint; the MCP tool always raises `UpdateNotSupportedError`, so cycles are effectively immutable.
- **`list_folders` / `list_statuses`**: Best-effort UI-backed tools that depend on internal UI endpoints and may return 404/500 on some server versions.
- **`get_test_execution` (Z19)**: Best-effort. Numeric execution IDs may not resolve even for existing executions; prefer `get_latest_test_result(test_case_key)` or `list_test_executions(test_case_key)` for reliable behavior.

---

## OpenCode Integration Guide

To integrate this MCP server into OpenCode, configure it under the top-level `"mcp"` key in your OpenCode configuration file (`~/.config/opencode/opencode.json` or project-level `opencode.json`).

### Example OpenCode Configuration (`opencode.json`)

```json
{
  "mcp": {
    "zephyr-datacenter": {
      "type": "local",
      "command": ["/path/to/dist/zephyr-scale-mcp"],
      "environment": {
        "ZEPHYR_BASE_URL": "https://jira.yourcompany.com",
        "ZEPHYR_PAT": "{env:ZEPHYR_PAT}"
      },
      "enabled": true
    }
  }
}
```

> **Note**: OpenCode uses `{env:VAR_NAME}` for credentials interpolation from your environment shell.

---

## Developer Guide

For detailed build instructions, python environment setups (`pip` and `uv`), running unit tests, and PyInstaller executable building, please see [BUILD.md](BUILD.md).

### Quick Setup

#### Standard Python (`pip`):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
PYTHONPATH=. pytest tests/
```

#### Using `uv`:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
PYTHONPATH=. uv run pytest tests/
```

### Building Standalone Binary
```bash
./build.sh
```
The resulting executable will be created at `dist/zephyr-scale-mcp`.
