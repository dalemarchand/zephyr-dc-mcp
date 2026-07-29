import os
import ssl
import httpx
import truststore
from fastmcp import FastMCP

__version__ = "0.0.3"

# Initialize FastMCP server
mcp = FastMCP("zephyr-scale-datacenter")


def get_base_url() -> str:
    """Retrieve the Jira Data Center base URL dynamically from environment."""
    url = os.getenv("ZEPHYR_BASE_URL", "").rstrip("/")
    if not url:
        raise ValueError(
            "ZEPHYR_BASE_URL environment variable must be specified (e.g. 'https://jira.yourcompany.com')."
        )
    return url

def get_pat() -> str:
    """Retrieve the Jira Personal Access Token (PAT) dynamically from environment."""
    pat = os.getenv("ZEPHYR_PAT") or os.getenv("JIRA_PAT") or os.getenv("ZEPHYR_API_KEY") or os.getenv("JIRA_API_TOKEN")
    if not pat:
        raise ValueError(
            "ZEPHYR_PAT (or JIRA_PAT) environment variable must be specified with your Jira Data Center Personal Access Token."
        )
    return pat

def get_headers() -> dict[str, str]:
    """Retrieve HTTP headers dynamically using the Jira PAT."""
    pat = get_pat()
    return {
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def get_ssl_verify() -> bool | ssl.SSLContext | str:
    """Retrieve SSL verification configuration using OS certificate store via truststore."""
    verify_env = os.getenv("ZEPHYR_SSL_VERIFY")
    if verify_env is not None:
        if verify_env.lower() in ("false", "0", "no"):
            return False
        if verify_env.lower() in ("true", "1", "yes"):
            try:
                return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            except Exception:
                return True
        return verify_env
    
    ssl_cert = os.getenv("SSL_CERT_FILE")
    if ssl_cert:
        return ssl_cert

    # Default to OS certificate store via truststore
    try:
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:
        return True

def format_error(e: Exception) -> str:
    """Format HTTP, connection, or configuration errors for the LLM to understand."""
    if isinstance(e, ValueError):
        return f"Configuration Error: {e}"
    if isinstance(e, httpx.HTTPStatusError):
        return f"API Error {e.response.status_code}: {e.response.text}"
    if isinstance(e, httpx.RequestError):
        return f"Request Error: {e}"
    return f"Error: {e}"

async def _make_request(method: str, endpoint: str, params: dict = None, json: dict | list = None) -> str:
    """Internal helper to perform HTTP requests to Zephyr Scale Data Center API."""
    try:
        url = f"{get_base_url()}{endpoint}"
        headers = get_headers()
    except ValueError as e:
        return format_error(e)

    async with httpx.AsyncClient(verify=get_ssl_verify()) as client:
        try:
            response = await client.request(method, url, headers=headers, params=params, json=json)
            response.raise_for_status()
            return response.text
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            return format_error(e)

# --- Test Cases & Test Scripts ---

@mcp.tool()
async def get_test_case(test_case_key: str) -> str:
    """Fetch details for a specific Zephyr Scale test case (e.g. 'PROJ-T123')."""
    return await _make_request("GET", f"/rest/tests/1.0/testcase/{test_case_key}")

@mcp.tool()
async def list_test_cases(
    project_key: str,
    max_results: int = 20,
    fields: str = "id,key,name,status,priority,projectKey,folderId",
) -> str:
    """List test cases for a specific project in Zephyr Scale Data Center."""
    params = {"query": f"projectKey = '{project_key}'", "maxResults": max_results}
    if fields:
        params["fields"] = fields
    return await _make_request("GET", "/rest/tests/1.0/testcase/search", params=params)


@mcp.tool()
async def create_test_case(
    project_key: str,
    name: str,
    folder_id: int = None,
    status: str = None,
    priority: str = None,
    owner: str = None,
    labels: list[str] = None,
) -> str:
    """Create a new test case in Zephyr Scale Data Center."""
    payload = {"projectKey": project_key, "name": name}
    if folder_id is not None:
        payload["folderId"] = folder_id
    if status:
        payload["status"] = status
    if priority:
        payload["priority"] = priority
    if owner:
        payload["owner"] = owner
    if labels:
        payload["labels"] = labels
    return await _make_request("POST", "/rest/atm/1.0/testcase", json=payload)

@mcp.tool()
async def update_test_case(
    test_case_key: str,
    name: str = None,
    folder_id: int = None,
    status: str = None,
    priority: str = None,
    owner: str = None,
    labels: list[str] = None,
) -> str:
    """Update an existing test case in Zephyr Scale Data Center."""
    payload = {}
    if name:
        payload["name"] = name
    if folder_id is not None:
        payload["folderId"] = folder_id
    if status:
        payload["status"] = status
    if priority:
        payload["priority"] = priority
    if owner:
        payload["owner"] = owner
    if labels:
        payload["labels"] = labels
    return await _make_request("PUT", f"/rest/atm/1.0/testcase/{test_case_key}", json=payload)

@mcp.tool()
async def get_test_script(test_case_key: str) -> str:
    """Retrieve the step-by-step test script for a test case."""
    return await _make_request("GET", f"/rest/atm/1.0/testcase/{test_case_key}/testscript")

@mcp.tool()
async def create_or_update_test_script(test_case_key: str, steps: list[dict]) -> str:
    """Create or update step-by-step test script for a test case (steps format: [{"description": "Step 1", "expectedResult": "Result 1"}])."""
    payload = {"type": "STEP_BY_STEP", "steps": steps}
    return await _make_request("POST", f"/rest/atm/1.0/testcase/{test_case_key}/testscript", json=payload)

@mcp.tool()
async def link_test_to_issue(test_case_key: str, issue_key: str) -> str:
    """Link a Zephyr test case to a Jira issue for traceability."""
    return await _make_request("POST", f"/rest/tests/1.0/testcase/{test_case_key}/issueLinks", json=[issue_key])

# --- Test Cycles / Runs & Executions ---

@mcp.tool()
async def get_test_cycle(cycle_key: str) -> str:
    """Fetch details for a specific test cycle/run (e.g. 'PROJ-R123')."""
    return await _make_request("GET", f"/rest/atm/1.0/testrun/{cycle_key}")

@mcp.tool()
async def search_test_cycles(project_key: str, max_results: int = 20) -> str:
    """Search test cycles/runs for a project."""
    params = {"query": f"projectKey = '{project_key}'", "maxResults": max_results}
    return await _make_request("GET", "/rest/atm/1.0/testrun/search", params=params)

@mcp.tool()
async def create_test_cycle(
    project_key: str,
    name: str,
    folder_id: int = None,
    planned_start_date: str = None,
    planned_end_date: str = None,
    description: str = None,
) -> str:
    """Create a new test cycle/run."""
    payload = {"projectKey": project_key, "name": name}
    if folder_id is not None:
        payload["folderId"] = folder_id
    if planned_start_date:
        payload["plannedStartDate"] = planned_start_date
    if planned_end_date:
        payload["plannedEndDate"] = planned_end_date
    if description:
        payload["description"] = description
    return await _make_request("POST", "/rest/atm/1.0/testrun", json=payload)

@mcp.tool()
async def update_test_cycle(
    cycle_key: str,
    name: str = None,
    description: str = None,
    status: str = None,
    folder_id: int = None,
) -> str:
    """Update an existing test cycle/run."""
    payload = {}
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description
    if status:
        payload["status"] = status
    if folder_id is not None:
        payload["folderId"] = folder_id
    return await _make_request("PUT", f"/rest/atm/1.0/testrun/{cycle_key}", json=payload)

@mcp.tool()
async def create_test_execution(test_case_key: str, status: str = "PASS", cycle_key: str = None) -> str:
    """Create a test execution result for a test case (status: PASS, FAIL, WIP, BLOCKED)."""
    payload = {
        "testCaseKey": test_case_key,
        "status": status.upper() if isinstance(status, str) else status,
    }
    if cycle_key:
        payload["testCycleKey"] = cycle_key
    return await _make_request("POST", "/rest/tests/1.0/testexecution", json=payload)

@mcp.tool()
async def get_test_execution(execution_id: int) -> str:
    """Retrieve details for a specific test execution result by ID."""
    return await _make_request("GET", f"/rest/atm/1.0/testresult/{execution_id}")

@mcp.tool()
async def list_test_executions(test_case_key: str) -> str:
    """List execution history for a specific test case."""
    return await _make_request("GET", f"/rest/tests/1.0/testcase/{test_case_key}/testresults")

# --- Test Plans, Folders, Environments & Statuses ---

@mcp.tool()
async def get_test_plan(plan_key: str) -> str:
    """Fetch details for a specific test plan (e.g. 'PROJ-P123')."""
    return await _make_request("GET", f"/rest/atm/1.0/testplan/{plan_key}")

@mcp.tool()
async def search_test_plans(project_key: str, max_results: int = 20) -> str:
    """Search test plans for a project."""
    params = {"query": f"projectKey = '{project_key}'", "maxResults": max_results}
    return await _make_request("GET", "/rest/atm/1.0/testplan/search", params=params)

@mcp.tool()
async def create_test_plan(
    project_key: str,
    name: str,
    description: str = None,
    folder_id: int = None,
) -> str:
    """Create a new test plan."""
    payload = {"projectKey": project_key, "name": name}
    if description:
        payload["description"] = description
    if folder_id is not None:
        payload["folderId"] = folder_id
    return await _make_request("POST", "/rest/atm/1.0/testplan", json=payload)

@mcp.tool()
async def list_folders(project_key: str, folder_type: str = "TEST_CASE") -> str:
    """List folders for a project (folder_type: TEST_CASE, TEST_CYCLE, TEST_PLAN)."""
    params = {"projectKey": project_key, "type": folder_type}
    return await _make_request("GET", "/rest/atm/1.0/folder", params=params)

@mcp.tool()
async def create_folder(
    project_key: str,
    name: str,
    folder_type: str = "TEST_CASE",
    parent_id: int = None,
) -> str:
    """Create a folder for organizing test cases, cycles, or plans."""
    payload = {"projectKey": project_key, "name": name, "type": folder_type}
    if parent_id is not None:
        payload["parentId"] = parent_id
    return await _make_request("POST", "/rest/atm/1.0/folder", json=payload)

@mcp.tool()
async def list_environments(project_key: str) -> str:
    """List available environments for a project."""
    params = {"projectKey": project_key}
    return await _make_request("GET", "/rest/atm/1.0/environment", params=params)

@mcp.tool()
async def list_statuses(project_key: str) -> str:
    """List configured test execution statuses for a project."""
    params = {"projectKey": project_key}
    return await _make_request("GET", "/rest/atm/1.0/status", params=params)

if __name__ == "__main__":
    mcp.run()