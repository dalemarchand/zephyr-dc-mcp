# Zephyr Scale Data Center MCP server.
# Note: Zephyr Scale Server v1 has no official test-cycle update endpoint.

import json as json_lib
import os
import ssl
import httpx
import truststore
from fastmcp import FastMCP

__version__ = "0.2.0"


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
        body = e.response.text.strip() or f"HTTP {e.response.status_code}"
        return f"API Error {e.response.status_code}: {body}"
    if isinstance(e, httpx.RequestError):
        return f"Request Error: {e}"
    return f"Error: {e}"


class UpdateNotSupportedError(RuntimeError):
    """Raised when attempting to update test cycles on Zephyr Scale Server v1."""

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
            text = response.text
            if not text.strip() and response.status_code in (200, 201, 204):
                return json_lib.dumps({"status": "success", "statusCode": response.status_code})
            return text
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            return format_error(e)


# --- Test Cases & Test Scripts ---

@mcp.tool()
async def get_test_case(test_case_key: str) -> str:
    """Fetch details for a specific Zephyr Scale test case (e.g. 'PROJ-T123').
    
    Returns a comprehensive JSON object containing all test case metadata:
    - key, name, status, priority, owner, createdBy, createdOn, updatedBy, updatedOn
    - component, folder, labels, customFields (dict), issueLinks (list)
    - testScript (step-by-step steps), parameters (dict), majorVersion, latestVersion
    """
    return await _make_request("GET", f"/rest/atm/1.0/testcase/{test_case_key}")

@mcp.tool()
async def list_test_cases(project_key: str = None, query: str = None, max_results: int = 20) -> str:
    """List test cases for a specific project in Zephyr Scale Data Center."""
    if not query and project_key:
        query = f'projectKey = "{project_key}"'
    params = {"query": query or "", "maxResults": max_results}
    return await _make_request("GET", "/rest/atm/1.0/testcase/search", params=params)

@mcp.tool()
async def create_test_case(
    project_key: str,
    name: str,
    folder_id: int = None,
    folder: str = None,
    status: str = None,
    priority: str = None,
    owner: str = None,
    component: str = None,
    labels: list[str] = None,
    custom_fields: dict = None,
    issue_links: list[str] = None,
    precondition: str = None,
    objective: str = None,
    estimated_time: int = None,
    parameters: dict = None,
) -> str:
    """Create a new test case in Zephyr Scale Data Center.
    
    Supports setting optional metadata fields:
    - folder_id (int) or folder (str path e.g. "/Project/Subfolder")
    - status, priority, owner, component
    - labels (list of strings)
    - custom_fields (dict e.g. {"Linked Issues": "PROJ-123"})
    - issue_links (list of Jira issue keys e.g. ["PROJ-123"])
    - precondition (precondition text/markdown string)
    - objective (test case objective/description string)
    - estimated_time (execution time in milliseconds)
    - parameters (dict definition)
    """
    payload = {"projectKey": project_key, "name": name}
    if folder_id is not None:
        payload["folderId"] = folder_id
    if folder:
        payload["folder"] = folder
    if status:
        payload["status"] = status
    if priority:
        payload["priority"] = priority
    if owner:
        payload["owner"] = owner
    if component:
        payload["component"] = component
    if labels:
        payload["labels"] = labels
    if custom_fields:
        payload["customFields"] = custom_fields
    if issue_links:
        payload["issueLinks"] = issue_links
    if precondition:
        payload["precondition"] = precondition
    if objective:
        payload["objective"] = objective
    if estimated_time is not None:
        payload["estimatedTime"] = estimated_time
    if parameters:
        payload["parameters"] = parameters
    return await _make_request("POST", "/rest/atm/1.0/testcase", json=payload)

@mcp.tool()
async def update_test_case(
    test_case_key: str,
    name: str = None,
    folder_id: int = None,
    folder: str = None,
    status: str = None,
    priority: str = None,
    owner: str = None,
    component: str = None,
    labels: list[str] = None,
    custom_fields: dict = None,
    issue_links: list[str] = None,
    precondition: str = None,
    objective: str = None,
    estimated_time: int = None,
    parameters: dict = None,
) -> str:
    """Update an existing test case in Zephyr Scale Data Center."""
    payload = {}
    if name:
        payload["name"] = name
    if folder_id is not None:
        payload["folderId"] = folder_id
    if folder:
        payload["folder"] = folder
    if status:
        payload["status"] = status
    if priority:
        payload["priority"] = priority
    if owner:
        payload["owner"] = owner
    if component:
        payload["component"] = component
    if labels:
        payload["labels"] = labels
    if custom_fields:
        payload["customFields"] = custom_fields
    if issue_links:
        payload["issueLinks"] = issue_links
    if precondition:
        payload["precondition"] = precondition
    if objective:
        payload["objective"] = objective
    if estimated_time is not None:
        payload["estimatedTime"] = estimated_time
    if parameters:
        payload["parameters"] = parameters
    return await _make_request("PUT", f"/rest/atm/1.0/testcase/{test_case_key}", json=payload)

@mcp.tool()
async def delete_test_case(test_case_key: str) -> str:
    """Delete a test case by key. This is irreversible."""
    return await _make_request("DELETE", f"/rest/atm/1.0/testcase/{test_case_key}")

@mcp.tool()
async def get_test_script(test_case_key: str) -> str:
    """Retrieve the step-by-step test script for a test case."""
    res_text = await _make_request("GET", f"/rest/atm/1.0/testcase/{test_case_key}")
    try:
        data = json_lib.loads(res_text)
        if isinstance(data, dict):
            if "testScript" in data and data["testScript"]:
                return json_lib.dumps(data["testScript"], indent=2)
            return json_lib.dumps({"type": "NONE", "steps": []}, indent=2)
    except Exception:
        pass
    return res_text




@mcp.tool()
async def create_or_update_test_script(test_case_key: str, steps: list[dict]) -> str:
    """Create or update step-by-step test script for a test case (steps format: [{"description": "Step 1", "expectedResult": "Result 1"}])."""
    payload = {"testScript": {"type": "STEP_BY_STEP", "steps": steps}}
    res = await _make_request("PUT", f"/rest/atm/1.0/testcase/{test_case_key}", json=payload)
    if "404" in res and "Not Found" in res:
        legacy_payload = {"type": "STEP_BY_STEP", "steps": steps}
        return await _make_request("POST", f"/rest/atm/1.0/testcase/{test_case_key}/testscript", json=legacy_payload)
    return res


@mcp.tool()
async def link_test_to_issue(test_case_key: str, issue_key: str) -> str:
    """Link a Zephyr test case to a Jira issue for traceability."""
    payload = {"issueKey": issue_key}
    res = await _make_request("POST", f"/rest/atm/1.0/testcase/{test_case_key}/issue", json=payload)
    if "API Error 404" in res or "Not Found" in res:
        res = await _make_request("POST", f"/rest/atm/1.0/testcase/{test_case_key}/issueLinks", json=[issue_key])
    if "API Error 404" in res or "Not Found" in res:
        put_payload = {"issueLinks": [issue_key]}
        res = await _make_request("PUT", f"/rest/atm/1.0/testcase/{test_case_key}", json=put_payload)
    return res

@mcp.tool()
async def bulk_link_test_cases_to_issues(links: list[dict]) -> str:
    """Bulk-link multiple test cases to Jira issues in a single call.
    
    links format: [{"testCaseKey": "PROJ-T1", "issueKey": "PROJ-123"}, ...]
    Up to 2500 distinct test case keys per request.
    """
    payload = {"testCaseIssueLinkList": links}
    return await _make_request("POST", "/rest/atm/1.0/testcase/link-issues", json=payload)

@mcp.tool()
async def get_test_cases_for_issue(issue_key: str) -> str:
    """Retrieve all Zephyr test cases linked to a specific Jira issue (e.g. 'PROJ-123')."""
    return await _make_request("GET", f"/rest/atm/1.0/issuelink/{issue_key}/testcases")


# --- Test Cycles / Runs & Executions ---

@mcp.tool()
async def get_test_cycle(cycle_key: str) -> str:
    """Fetch details for a specific test cycle/run (e.g. 'PROJ-R123')."""
    return await _make_request("GET", f"/rest/atm/1.0/testrun/{cycle_key}")

@mcp.tool()
async def search_test_cycles(project_key: str = None, query: str = None, max_results: int = 20) -> str:
    """Search test cycles/runs for a project (query supports projectKey and folder filters)."""
    if not query and project_key:
        query = f'projectKey = "{project_key}"'
    params = {"query": query or "", "maxResults": max_results}
    return await _make_request("GET", "/rest/atm/1.0/testrun/search", params=params)

@mcp.tool()
async def create_test_cycle(
    project_key: str,
    name: str,
    folder_id: int = None,
    folder: str = None,
    planned_start_date: str = None,
    planned_end_date: str = None,
    description: str = None,
    status: str = None,
    owner: str = None,
    version: str = None,
    iteration: str = None,
    custom_fields: dict = None,
    issue_links: list[str] = None,
) -> str:
    """Create a new test cycle/run."""
    payload = {"projectKey": project_key, "name": name}
    if folder_id is not None:
        payload["folderId"] = folder_id
    if folder:
        payload["folder"] = folder
    if planned_start_date:
        payload["plannedStartDate"] = planned_start_date
    if planned_end_date:
        payload["plannedEndDate"] = planned_end_date
    if description:
        payload["description"] = description
    if status:
        payload["status"] = status
    if owner:
        payload["owner"] = owner
    if version:
        payload["version"] = version
    if iteration:
        payload["iteration"] = iteration
    if custom_fields:
        payload["customFields"] = custom_fields
    if issue_links:
        payload["issueLinks"] = issue_links
    return await _make_request("POST", "/rest/atm/1.0/testrun", json=payload)

def _map_folder_type(folder_type: str) -> str:
    ft = (folder_type or "testcase").lower().replace("_", "")
    if "case" in ft:
        return "testcase"
    if "cycle" in ft or "run" in ft:
        return "testrun"
    if "plan" in ft:
        return "testplan"
    return ft

@mcp.tool()
async def update_test_cycle(
    cycle_key: str,
    name: str = None,
    description: str = None,
    status: str = None,
    folder_id: int = None,
    project_key: str = None,
) -> str:
    """[EXPERIMENTAL / UNSUPPORTED] Attempt to update an existing test cycle/run.

    Zephyr Scale Server v1 does not provide an official PUT /testrun/{key} endpoint.
    This tool always raises UpdateNotSupportedError; treat test cycles as immutable and
    create a new cycle instead of updating an existing one.
    """
    raise UpdateNotSupportedError(
        "update_test_cycle is unsupported - Zephyr Scale Server v1 provides no PUT /testrun/{key} endpoint. "
        "Treat test cycles as immutable; create a new cycle instead."
    )

@mcp.tool()
async def delete_test_cycle(cycle_key: str) -> str:
    """Delete a test cycle/run by key. This is irreversible."""
    return await _make_request("DELETE", f"/rest/atm/1.0/testrun/{cycle_key}")

@mcp.tool()
async def create_test_execution(
    test_case_key: str,
    status: str = "Pass",
    cycle_key: str = None,
    project_key: str = None,
    comment: str = None,
    environment: str = None,
    executed_by: str = None,
    execution_time: int = None,
    custom_fields: dict = None,
    issue_links: list[str] = None,
    script_results: list[dict] = None,
    actual_start_date: str = None,
    actual_end_date: str = None,
) -> str:
    """Create a test execution result for a test case (status: Pass, Fail, In Progress, Blocked, Not Executed)."""
    if not project_key and "-" in test_case_key:
        project_key = test_case_key.split("-")[0]

    status_str = status.strip() if isinstance(status, str) else "Pass"
    status_map = {
        "PASS": "Pass",
        "PASSED": "Pass",
        "FAIL": "Fail",
        "FAILED": "Fail",
        "WIP": "In Progress",
        "IN PROGRESS": "In Progress",
        "BLOCKED": "Blocked",
        "NOT EXECUTED": "Not Executed",
        "UNEXECUTED": "Not Executed",
    }
    normalized_status = status_map.get(status_str.upper(), status_str)

    payload = {
        "projectKey": project_key,
        "testCaseKey": test_case_key,
        "status": normalized_status,
    }
    if cycle_key:
        payload["testCycleKey"] = cycle_key
    if comment:
        payload["comment"] = comment
    if environment:
        payload["environment"] = environment
    if executed_by:
        payload["executedBy"] = executed_by
    if execution_time is not None:
        payload["executionTime"] = execution_time
    if custom_fields:
        payload["customFields"] = custom_fields
    if issue_links:
        payload["issueLinks"] = issue_links
    if script_results:
        payload["scriptResults"] = script_results
    if actual_start_date:
        payload["actualStartDate"] = actual_start_date
    if actual_end_date:
        payload["actualEndDate"] = actual_end_date
    return await _make_request("POST", "/rest/atm/1.0/testresult", json=payload)

@mcp.tool()
async def create_test_execution_in_cycle(
    cycle_key: str,
    test_case_key: str,
    status: str = "Pass",
    comment: str = None,
    environment: str = None,
    executed_by: str = None,
    execution_time: int = None,
    custom_fields: dict = None,
    issue_links: list[str] = None,
    script_results: list[dict] = None,
    actual_start_date: str = None,
    actual_end_date: str = None,
) -> str:
    """Create a test execution result directly within a test cycle/run.
    
    This uses POST /testrun/{cycleKey}/testcase/{testCaseKey}/testresult which creates a result
    within the context of the specified test run. Preferred over create_test_execution when
    you have a specific cycle to record against.
    Status values: Pass, Fail, Not Executed, In Progress, Blocked.
    
    Note: 
    - `executed_by` must be a valid Zephyr username; arbitrary labels will cause 400.
    - `environment` must match an existing environment; otherwise it may cause 500s depending on server version.
    """
    status_str = status.strip() if isinstance(status, str) else "Pass"
    status_map = {
        "PASS": "Pass", "PASSED": "Pass",
        "FAIL": "Fail", "FAILED": "Fail",
        "WIP": "In Progress", "IN PROGRESS": "In Progress",
        "BLOCKED": "Blocked",
        "NOT EXECUTED": "Not Executed", "UNEXECUTED": "Not Executed",
    }
    normalized_status = status_map.get(status_str.upper(), status_str)
    payload = {"status": normalized_status}
    if comment:
        payload["comment"] = comment
    if executed_by:
        payload["executedBy"] = executed_by
    if execution_time is not None:
        payload["executionTime"] = execution_time
    if custom_fields:
        payload["customFields"] = custom_fields
    if issue_links:
        payload["issueLinks"] = issue_links
    if script_results:
        payload["scriptResults"] = script_results
    if actual_start_date:
        payload["actualStartDate"] = actual_start_date
    if actual_end_date:
        payload["actualEndDate"] = actual_end_date
    params = {}
    if environment:
        params["environment"] = environment
    return await _make_request(
        "POST",
        f"/rest/atm/1.0/testrun/{cycle_key}/testcase/{test_case_key}/testresult",
        json=payload,
        params=params or None,
    )

@mcp.tool()
async def get_test_execution(execution_id: str | int) -> str:
    """Retrieve details for a specific test execution result by numeric ID or alphanumeric key.
    
    Accepts either:
    - A numeric ID (e.g. 82812) as returned by create_test_execution
    - An alphanumeric execution key (e.g. 'PROJ-E44546') as returned by list_test_executions
    
    Note: The official Zephyr Scale Server API does not document a direct GET endpoint
    for test results by ID. Use get_latest_test_result(test_case_key) or
    list_test_executions(test_case_key) as more reliable alternatives.
    """
    execution_id_str = str(execution_id).strip()
    
    # Try the execution key path first if it looks like an alphanumeric key (e.g. PROJ-E12345)
    if not execution_id_str.isdigit():
        res = await _make_request("GET", f"/rest/atm/1.0/testresult/{execution_id_str}")
        if "404" not in res and "Not Found" not in res:
            return res
        # Fallback to search query using the key
        return await _make_request("GET", "/rest/atm/1.0/testresult/search", params={"query": f"key = \"{execution_id_str}\""})

    # Numeric ID path
    res = await _make_request("GET", f"/rest/atm/1.0/testresult/{execution_id_str}")
    if "404" in res and "Not Found" in res:
        # ID-based search using the testresult/search endpoint
        res = await _make_request("GET", "/rest/atm/1.0/testresult/search", params={"query": f"id = {execution_id_str}"})

    if "API Error 404" in res or '"status-code":404' in res:
        return json_lib.dumps({
            "note": (
                "Execution not found via /testresult/{id} or testresult/search. "
                "On some Zephyr Scale instances, direct lookup by ID is unreliable even for existing executions. "
                "Prefer get_latest_test_result(test_case_key) or list_test_executions(test_case_key) when possible."
            ),
            "statusCode": 404,
            "executionId": execution_id_str,
            "raw": res,
        })
    return res

@mcp.tool()
async def get_latest_test_result(test_case_key: str) -> str:
    """Get the most recent test execution result for a specific test case.
    
    Uses GET /testcase/{key}/testresult/latest – the officially documented endpoint
    for retrieving the last recorded result for a test case.
    """
    return await _make_request("GET", f"/rest/atm/1.0/testcase/{test_case_key}/testresult/latest")

@mcp.tool()
async def list_test_executions(test_case_key: str, cycle_key: str = None) -> str:
    """List execution history for a specific test case (optionally scoped to a cycle/test run).
    
    If cycle_key is provided, returns all results for that test run via GET /testrun/{key}/testresults.
    Otherwise returns the latest result for the test case via GET /testcase/{key}/testresult/latest.
    """
    if cycle_key:
        # Official API: GET /testrun/{testRunKey}/testresults
        return await _make_request("GET", f"/rest/atm/1.0/testrun/{cycle_key}/testresults")
    
    # Official API: GET /testcase/{testCaseKey}/testresult/latest
    return await _make_request("GET", f"/rest/atm/1.0/testcase/{test_case_key}/testresult/latest")

@mcp.tool()
async def list_test_executions_page(
    cycle_key: str,
    start_at: int = 0,
    max_results: int = 50,
    only_last_executions: bool = False,
) -> str:
    """Retrieve a paginated page of test results linked to a test run/cycle.
    
    Uses GET /testrun/{key}/testresults/page which is the preferred paginated endpoint.
    Returns a response with 'total' (total count) and 'values' (page of results).
    """
    params = {
        "startAt": start_at,
        "maxResults": max_results,
        "onlyLastExecutions": only_last_executions,
    }
    return await _make_request("GET", f"/rest/atm/1.0/testrun/{cycle_key}/testresults/page", params=params)


# --- Test Plans, Folders, Environments & Statuses ---

@mcp.tool()
async def get_test_plan(plan_key: str) -> str:
    """Fetch details for a specific test plan (e.g. 'PROJ-P123')."""
    return await _make_request("GET", f"/rest/atm/1.0/testplan/{plan_key}")

@mcp.tool()
async def search_test_plans(project_key: str = None, query: str = None, max_results: int = 20) -> str:
    """Search test plans for a project."""
    if not query and project_key:
        query = f'projectKey = "{project_key}"'
    params = {"query": query or "", "maxResults": max_results}
    return await _make_request("GET", "/rest/atm/1.0/testplan/search", params=params)


@mcp.tool()
async def create_test_plan(
    project_key: str,
    name: str,
    folder_id: int = None,
    folder: str = None,
    status: str = None,
    owner: str = None,
    labels: list[str] = None,
    issue_links: list[str] = None,
    custom_fields: dict = None,
    objective: str = None,
    description: str | None = None,
) -> str:
    """Create a new test plan."""
    payload = {"projectKey": project_key, "name": name}
    if folder_id is not None:
        payload["folderId"] = folder_id
    if folder:
        payload["folder"] = folder
    if status:
        payload["status"] = status
    if owner:
        payload["owner"] = owner
    if labels:
        payload["labels"] = labels
    if issue_links:
        payload["issueLinks"] = issue_links
    if custom_fields:
        payload["customFields"] = custom_fields
    if objective:
        payload["objective"] = objective
    return await _make_request("POST", "/rest/atm/1.0/testplan", json=payload)

@mcp.tool()
async def update_test_plan(
    plan_key: str,
    name: str = None,
    folder_id: int = None,
    folder: str = None,
    status: str = None,
    owner: str = None,
    labels: list[str] = None,
    issue_links: list[str] = None,
    custom_fields: dict = None,
    objective: str = None,
    description: str | None = None,
) -> str:
    """Update an existing test plan by key."""
    payload = {}
    if name:
        payload["name"] = name
    if folder_id is not None:
        payload["folderId"] = folder_id
    if folder:
        payload["folder"] = folder
    if status:
        payload["status"] = status
    if owner:
        payload["owner"] = owner
    if labels:
        payload["labels"] = labels
    if issue_links:
        payload["issueLinks"] = issue_links
    if custom_fields:
        payload["customFields"] = custom_fields
    if objective:
        payload["objective"] = objective
    return await _make_request("PUT", f"/rest/atm/1.0/testplan/{plan_key}", json=payload)

@mcp.tool()
async def delete_test_plan(plan_key: str) -> str:
    """Delete a test plan by key. This is irreversible."""
    return await _make_request("DELETE", f"/rest/atm/1.0/testplan/{plan_key}")

@mcp.tool()
async def list_folders(project_key: str, folder_type: str = "TEST_CASE") -> str:
    """List folders for a project (folder_type: TEST_CASE, TEST_CYCLE, TEST_PLAN).
    
    Uses the unofficial /rest/tests/1.0/project/{projectId}/customfields/folder endpoint
    which requires the numeric Jira project ID. The project key is automatically resolved
    to its numeric ID via the Jira REST API before calling the folder endpoint.
    """
    ft = _map_folder_type(folder_type)

    # Step 1: resolve project key → numeric Jira project ID
    project_id = None
    proj_res = await _make_request("GET", f"/rest/api/2/project/{project_key}")
    if "API Error" not in proj_res and "Request Error" not in proj_res:
        try:
            proj_data = json_lib.loads(proj_res)
            project_id = proj_data.get("id")
        except Exception:
            pass

    # Step 2: call the unofficial folder endpoint with the numeric ID
    if project_id:
        res = await _make_request("GET", f"/rest/tests/1.0/project/{project_id}/foldertree/{ft}")
        if "API Error" not in res and "Request Error" not in res:
            return res

    # Step 3: fallback — try the official atm/1.0/folder endpoint (works on some versions)
    params = {"projectKey": project_key, "type": ft}
    res = await _make_request("GET", "/rest/atm/1.0/folder", params=params)
    if "500" in res or ("404" in res and "Not Found" in res):
        res = await _make_request("GET", "/rest/atm/1.0/folder/search", params=params)

    if "500" in res or ("404" in res and "Not Found" in res):
        return json_lib.dumps({
            "note": "Folder listing endpoint unavailable. The unofficial /rest/tests/1.0/project/{id}/customfields/folder endpoint requires a valid numeric project ID. Verify ZEPHYR_BASE_URL and permissions.",
            "projectKey": project_key,
            "folderType": folder_type,
        })
    return res


@mcp.tool()
async def create_folder(
    project_key: str,
    name: str,
    folder_type: str = "TEST_CASE",
    parent_id: int = None,
) -> str:
    """Create a folder for organizing test cases, cycles, or plans. Name will automatically start with '/' if omitted."""
    if not name.startswith("/"):
        name = f"/{name}"
    # For create, use the Zephyr symbolic constants directly (TEST_CASE, TEST_RUN, TEST_PLAN).
    ft_raw = (folder_type or "TEST_CASE").upper().replace(" ", "_")
    if ft_raw not in ("TEST_CASE", "TEST_RUN", "TEST_PLAN"):
        if "CYCLE" in ft_raw or "RUN" in ft_raw:
            ft_raw = "TEST_RUN"
        elif "PLAN" in ft_raw:
            ft_raw = "TEST_PLAN"
        else:
            ft_raw = "TEST_CASE"
            
    payload = {"projectKey": project_key, "name": name, "type": ft_raw}
    if parent_id is not None:
        payload["parentId"] = parent_id
    return await _make_request("POST", "/rest/atm/1.0/folder", json=payload)

@mcp.tool()
async def update_folder(folder_id: int, name: str) -> str:
    """Update the name of an existing folder by its numeric ID.
    
    Uses PUT /folder/{folderId}. Only the folder name can be updated (forward and backslashes not allowed).
    """
    payload = {"name": name}
    res = await _make_request("PUT", f"/rest/atm/1.0/folder/{folder_id}", json=payload)

    if "API Error 404" in res and "Folder not found" in res:
        return json_lib.dumps({
            "note": (
                "Folder not found for the given id. "
                "This usually indicates that the folder was deleted or never existed on this instance."
            ),
            "statusCode": 404,
            "folderId": folder_id,
            "raw": res,
        })

    return res

@mcp.tool()
async def list_environments(project_key: str) -> str:
    """List available environments for a project in Zephyr Scale Data Center."""
    params = {"projectKey": project_key}
    return await _make_request("GET", "/rest/atm/1.0/environments", params=params)

@mcp.tool()
async def create_environment(project_key: str, name: str, description: str = None) -> str:
    """Create a new test environment for a project in Zephyr Scale Data Center.
    
    Environment names must be unique per project.
    """
    payload = {"projectKey": project_key, "name": name}
    if description:
        payload["description"] = description
    return await _make_request("POST", "/rest/atm/1.0/environments", json=payload)

@mcp.tool()
async def list_statuses(project_key: str = None) -> str:
    """List configured test case statuses for a project in Zephyr Scale Data Center.
    
    Uses the unofficial /rest/tests/1.0/project/{projectId}/testcasestatus endpoint which
    returns the real project-configured statuses (e.g. Draft, Approved, Deprecated) with
    their colors and IDs. The project key is automatically resolved to its numeric ID.
    Falls back to legacy endpoints, then to hardcoded defaults if all else fails.
    """
    # Step 1: resolve project key → numeric Jira project ID and call unofficial endpoint
    if project_key:
        proj_res = await _make_request("GET", f"/rest/api/2/project/{project_key}")
        if "API Error" not in proj_res and "Request Error" not in proj_res:
            try:
                proj_data = json_lib.loads(proj_res)
                project_id = proj_data.get("id")
                if project_id:
                    res = await _make_request("GET", f"/rest/tests/1.0/project/{project_id}/testcasestatus")
                    if "API Error" not in res and "Request Error" not in res:
                        return res
            except Exception:
                pass

    # Step 2: fallback — try the official atm/1.0 status endpoints
    params = {}
    if project_key:
        params["projectKey"] = project_key
    res = await _make_request("GET", "/rest/atm/1.0/status/testexecution", params=params)
    if "404" in res and "Not Found" in res:
        res = await _make_request("GET", "/rest/atm/1.0/status", params=params)

    if "404" in res and "Not Found" in res:
        # Step 3: hardcoded defaults — these are the standard Zephyr Scale statuses.
        # Custom statuses configured in your instance may differ.
        return json_lib.dumps([
            {"id": 1, "name": "Pass", "description": "Test Passed"},
            {"id": 2, "name": "Fail", "description": "Test Failed"},
            {"id": 3, "name": "In Progress", "description": "Test is currently executing"},
            {"id": 4, "name": "Blocked", "description": "Test execution is blocked"},
            {"id": 5, "name": "Not Executed", "description": "Test has not been executed yet"},
            {"note": "These are the default Zephyr Scale Server statuses. Custom statuses configured in your instance may differ. Check Zephyr Scale Administration > Statuses for project-specific values."}
        ])
    return res



if __name__ == "__main__":
    mcp.run()
