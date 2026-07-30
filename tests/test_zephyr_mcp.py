import pytest
import ssl
import truststore
from unittest.mock import patch
from httpx import Response, Request, ConnectTimeout
from zephyr_dc_mcp import (
    get_test_case,
    list_test_cases,
    create_test_case,
    update_test_case,
    delete_test_case,
    get_test_script,
    create_or_update_test_script,
    link_test_to_issue,
    bulk_link_test_cases_to_issues,
    get_test_cases_for_issue,
    get_test_cycle,
    search_test_cycles,
    create_test_cycle,
    update_test_cycle,
    delete_test_cycle,
    create_test_execution,
    create_test_execution_in_cycle,
    get_test_execution,
    get_latest_test_result,
    list_test_executions,
    list_test_executions_page,
    get_test_plan,
    search_test_plans,
    create_test_plan,
    update_test_plan,
    delete_test_plan,
    list_folders,
    create_folder,
    update_folder,
    list_environments,
    create_environment,
    list_statuses,
    UpdateNotSupportedError,
    get_base_url,
    get_pat,
    get_headers,
    get_ssl_verify,
)

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("ZEPHYR_BASE_URL", "https://jira.example.com")
    monkeypatch.setenv("ZEPHYR_PAT", "pat_fake_token_123")

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_get_test_case(mock_request):
    test_key = "PROJ-T123"
    mock_request.return_value = Response(200, json={"key": test_key, "name": "Login Test"}, request=Request("GET", "https://jira.example.com"))
    result = await get_test_case(test_key)
    assert "Login Test" in result

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_get_test_case_error(mock_request):
    test_key = "PROJ-T999"
    mock_request.return_value = Response(404, text="Test case not found", request=Request("GET", "https://jira.example.com"))
    result = await get_test_case(test_key)
    assert "API Error 404" in result
    assert "Test case not found" in result

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_get_test_case_request_error(mock_request):
    test_key = "PROJ-T123"
    mock_request.side_effect = ConnectTimeout("Connection timed out", request=Request("GET", "https://jira.example.com"))
    result = await get_test_case(test_key)
    assert "Request Error:" in result
    assert "Connection timed out" in result

@pytest.mark.asyncio
async def test_missing_url_error(monkeypatch):
    monkeypatch.delenv("ZEPHYR_BASE_URL", raising=False)
    result = await get_test_case("PROJ-T123")
    assert "Configuration Error:" in result
    assert "ZEPHYR_BASE_URL environment variable must be specified" in result

@pytest.mark.asyncio
async def test_missing_pat_error(monkeypatch):
    monkeypatch.delenv("ZEPHYR_PAT", raising=False)
    monkeypatch.delenv("JIRA_PAT", raising=False)
    monkeypatch.delenv("ZEPHYR_API_KEY", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    result = await get_test_case("PROJ-T123")
    assert "Configuration Error:" in result
    assert "ZEPHYR_PAT (or JIRA_PAT) environment variable must be specified" in result

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_list_test_cases(mock_request):
    mock_request.return_value = Response(200, json=[{"key": "PROJ-T1"}], request=Request("GET", "https://jira.example.com"))
    result = await list_test_cases("PROJ")
    assert "PROJ-T1" in result
    assert mock_request.call_args[0][1] == "https://jira.example.com/rest/atm/1.0/testcase/search"
    assert mock_request.call_args[1]["params"]["query"] == 'projectKey = "PROJ"'

    # Test custom query
    res_custom = await list_test_cases(query='name ~ "Auth"')
    assert "PROJ-T1" in res_custom
    assert mock_request.call_args[1]["params"]["query"] == 'name ~ "Auth"'

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_create_and_update_test_case(mock_request):
    mock_request.return_value = Response(201, json={"key": "PROJ-T200"}, request=Request("POST", "https://jira.example.com"))
    res_create = await create_test_case(
        "PROJ",
        "New Auth Test",
        folder="/JLVC/ACS",
        status="Approved",
        priority="High",
        owner="JIRAUSER10949",
        component="ACS",
        labels=["StateManager"],
        custom_fields={"Linked Issues": "JSJ7JLVC-24436"},
        issue_links=["JSJ7JLVC-24436"],
        objective="Verify state manager deregistration",
        estimated_time=120000,
        parameters={"variables": [], "entries": []},
    )
    assert "PROJ-T200" in res_create
    payload = mock_request.call_args[1]["json"]
    assert payload["name"] == "New Auth Test"
    assert payload["folder"] == "/JLVC/ACS"
    assert payload["component"] == "ACS"
    assert payload["customFields"] == {"Linked Issues": "JSJ7JLVC-24436"}
    assert payload["issueLinks"] == ["JSJ7JLVC-24436"]
    assert payload["objective"] == "Verify state manager deregistration"
    assert payload["estimatedTime"] == 120000
    assert payload["parameters"] == {"variables": [], "entries": []}

    mock_request.return_value = Response(200, json={"key": "PROJ-T200", "name": "Updated Name"}, request=Request("PUT", "https://jira.example.com"))
    res_update = await update_test_case(
        "PROJ-T200",
        name="Updated Name",
        folder="/JLVC/ACS/Buckets",
        component="ACS-Core",
        custom_fields={"Linked Issues": "JSJ7JLVC-24436"},
        issue_links=["JSJ7JLVC-24436"],
        estimated_time=180000,
    )
    assert "Updated Name" in res_update
    update_payload = mock_request.call_args[1]["json"]
    assert update_payload["name"] == "Updated Name"
    assert update_payload["folder"] == "/JLVC/ACS/Buckets"
    assert update_payload["component"] == "ACS-Core"
    assert update_payload["customFields"] == {"Linked Issues": "JSJ7JLVC-24436"}
    assert update_payload["issueLinks"] == ["JSJ7JLVC-24436"]
    assert update_payload["estimatedTime"] == 180000

    mock_request.return_value = Response(200, json={"status": "linked"}, request=Request("POST", "https://jira.example.com"))
    res_link = await link_test_to_issue("PROJ-T200", "JIRA-123")
    assert "linked" in res_link
    assert mock_request.call_args[0][1] == "https://jira.example.com/rest/atm/1.0/testcase/PROJ-T200/issue"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_test_scripts(mock_request):
    # Test getting script when testScript exists
    mock_request.return_value = Response(200, json={"key": "PROJ-T100", "testScript": {"type": "STEP_BY_STEP", "steps": []}}, request=Request("GET", "https://jira.example.com"))
    get_res = await get_test_script("PROJ-T100")
    assert "STEP_BY_STEP" in get_res
    assert mock_request.call_args[0][1] == "https://jira.example.com/rest/atm/1.0/testcase/PROJ-T100"

    # Test getting script when testScript is absent
    mock_request.return_value = Response(200, json={"key": "PROJ-T100"}, request=Request("GET", "https://jira.example.com"))
    get_empty_res = await get_test_script("PROJ-T100")
    assert '"type": "NONE"' in get_empty_res

    # Test creating/updating script via primary PUT
    mock_request.return_value = Response(200, json={"status": "success"}, request=Request("PUT", "https://jira.example.com"))
    steps = [{"description": "Step 1", "expectedResult": "Pass"}]
    post_res = await create_or_update_test_script("PROJ-T100", steps)
    assert "success" in post_res
    assert mock_request.call_args[1]["json"]["testScript"]["steps"] == steps

    # Test creating/updating script fallback via POST /testscript
    mock_request.side_effect = [
        Response(404, text="Not Found", request=Request("PUT", "https://jira.example.com")),
        Response(200, json={"status": "fallback_success"}, request=Request("POST", "https://jira.example.com"))
    ]
    fallback_res = await create_or_update_test_script("PROJ-T100", steps)
    assert "fallback_success" in fallback_res




@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_test_cycles(mock_request):
    mock_request.return_value = Response(200, json={"key": "PROJ-R1"}, request=Request("GET", "https://jira.example.com"))
    res_get = await get_test_cycle("PROJ-R1")
    assert "PROJ-R1" in res_get

    mock_request.return_value = Response(200, json=[{"key": "PROJ-R1"}], request=Request("GET", "https://jira.example.com"))
    res_search = await search_test_cycles("PROJ")
    assert "PROJ-R1" in res_search

    mock_request.return_value = Response(201, json={"key": "PROJ-R2"}, request=Request("POST", "https://jira.example.com"))
    res_create = await create_test_cycle("PROJ", "Sprint 1 Regression")
    assert "PROJ-R2" in res_create

    # update_test_cycle is unsupported and must raise UpdateNotSupportedError
    with pytest.raises(UpdateNotSupportedError):
        await update_test_cycle("PROJ-R2", name="Updated")

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_test_executions(mock_request):
    mock_request.return_value = Response(201, json={"id": 500}, request=Request("POST", "https://jira.example.com"))
    res_create = await create_test_execution("PROJ-T1", "pass")
    assert "500" in res_create
    assert mock_request.call_args[1]["json"]["status"] == "Pass"

    assert mock_request.call_args[1]["json"]["projectKey"] == "PROJ"

    mock_request.return_value = Response(200, json={"id": 500, "status": "PASS"}, request=Request("GET", "https://jira.example.com"))
    # numeric ID
    res_get = await get_test_execution(500)
    assert "PASS" in res_get
    assert mock_request.call_args[0][1] == "https://jira.example.com/rest/atm/1.0/testresult/500"

    # alphanumeric key (e.g. JSJ7JLVC-E44546) - should try key-based path directly
    mock_request.return_value = Response(200, json={"id": 500, "key": "PROJ-E500", "status": "Pass"}, request=Request("GET", "https://jira.example.com"))
    res_get_key = await get_test_execution("PROJ-E500")
    assert "Pass" in res_get_key
    assert "/testresult/PROJ-E500" in mock_request.call_args[0][1]

    # list by test case key -> uses /testcase/{key}/testresult/latest
    mock_request.return_value = Response(200, json={"id": 500, "status": "Pass"}, request=Request("GET", "https://jira.example.com"))
    res_list = await list_test_executions("PROJ-T1")
    assert "500" in res_list
    assert "/testcase/PROJ-T1/testresult/latest" in mock_request.call_args[0][1]

    # list by cycle key -> uses /testrun/{key}/testresults
    mock_request.return_value = Response(200, json=[{"id": 500}], request=Request("GET", "https://jira.example.com"))
    res_list_cycle = await list_test_executions("PROJ-T1", cycle_key="PROJ-R1")
    assert "500" in res_list_cycle
    assert "/testrun/PROJ-R1/testresults" in mock_request.call_args[0][1]

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_test_plans(mock_request):
    mock_request.return_value = Response(200, json={"key": "PROJ-P1"}, request=Request("GET", "https://jira.example.com"))
    res_get = await get_test_plan("PROJ-P1")
    assert "PROJ-P1" in res_get

    mock_request.return_value = Response(200, json=[{"key": "PROJ-P1"}], request=Request("GET", "https://jira.example.com"))
    res_search = await search_test_plans("PROJ")
    assert "PROJ-P1" in res_search

    mock_request.return_value = Response(201, json={"key": "PROJ-P2"}, request=Request("POST", "https://jira.example.com"))
    res_create = await create_test_plan("PROJ", "Master Plan")
    assert "PROJ-P2" in res_create

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_folders_environments_statuses(mock_request):
    # list_folders: mock project key -> ID lookup, then the unofficial endpoint
    mock_request.side_effect = [
        Response(200, json={"id": "10701", "key": "PROJ"}, request=Request("GET", "https://jira.example.com")),
        Response(200, json=[{"id": 1, "name": "Regression"}], request=Request("GET", "https://jira.example.com")),
    ]
    res_folders = await list_folders("PROJ", "TEST_CASE")
    assert "Regression" in res_folders
    # Should have called the unofficial tests/1.0 endpoint
    assert "/rest/tests/1.0/project/10701/foldertree/testcase" in mock_request.call_args[0][1]
    mock_request.side_effect = None

    mock_request.return_value = Response(201, json={"id": 2, "name": "/Sanity"}, request=Request("POST", "https://jira.example.com"))
    res_create_folder = await create_folder("PROJ", "Sanity")
    assert "Sanity" in res_create_folder
    assert mock_request.call_args[1]["json"]["name"] == "/Sanity"

    mock_request.return_value = Response(200, json=[{"name": "Staging"}], request=Request("GET", "https://jira.example.com"))
    res_env = await list_environments("PROJ")
    assert "Staging" in res_env
    assert mock_request.call_args[0][1] == "https://jira.example.com/rest/atm/1.0/environments"

    # list_statuses: mock project key -> ID lookup, then unofficial endpoint
    mock_request.side_effect = [
        Response(200, json={"id": "10701", "key": "PROJ"}, request=Request("GET", "https://jira.example.com")),
        Response(200, json=[{"id": 85, "name": "Draft", "color": "#f0ad4e"}, {"id": 86, "name": "Approved", "color": "#3abb4b"}], request=Request("GET", "https://jira.example.com")),
    ]
    res_statuses = await list_statuses("PROJ")
    assert "Draft" in res_statuses
    assert "Approved" in res_statuses
    assert "/rest/tests/1.0/project/10701/testcasestatus" in mock_request.call_args[0][1]
    mock_request.side_effect = None



def test_dynamic_getters_and_pat(monkeypatch):
    monkeypatch.setenv("ZEPHYR_BASE_URL", "https://custom-jira.example.com/")
    monkeypatch.setenv("JIRA_PAT", "pat_token_abc")
    monkeypatch.delenv("ZEPHYR_PAT", raising=False)
    monkeypatch.setenv("ZEPHYR_SSL_VERIFY", "false")

    assert get_base_url() == "https://custom-jira.example.com"
    assert get_pat() == "pat_token_abc"
    assert get_headers()["Authorization"] == "Bearer pat_token_abc"
    assert get_ssl_verify() is False

def test_ssl_truststore_context(monkeypatch):
    monkeypatch.delenv("ZEPHYR_SSL_VERIFY", raising=False)
    ssl_context = get_ssl_verify()
    assert isinstance(ssl_context, truststore.SSLContext)

    monkeypatch.setenv("ZEPHYR_SSL_VERIFY", "true")
    ssl_context_true = get_ssl_verify()
    assert isinstance(ssl_context_true, truststore.SSLContext)
    
    monkeypatch.delenv("ZEPHYR_SSL_VERIFY", raising=False)
    monkeypatch.setenv("SSL_CERT_FILE", "/tmp/cert.pem")
    assert get_ssl_verify() == "/tmp/cert.pem"

def test_format_error():
    from zephyr_dc_mcp import format_error
    assert "Error:" in format_error(Exception("Generic Error"))

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_extra_coverage(mock_request):
    from zephyr_dc_mcp import _map_folder_type
    assert _map_folder_type("testplan") == "testplan"
    assert _map_folder_type("test_plan") == "testplan"
    assert _map_folder_type("unknown") == "unknown"
    
    mock_request.return_value = Response(201, json={"key": "T1"}, request=Request("POST", "https://jira.example.com"))
    await create_test_case("PROJ", "Name", folder_id=1, labels=["A"])

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_fallbacks_and_options(mock_request):
    # test list_statuses: project ID found, unofficial endpoint fails, both atm fallbacks fail → hardcoded defaults
    mock_request.side_effect = [
        Response(200, json={"id": "10701", "key": "PROJ"}, request=Request("GET", "https://jira.example.com")),  # project lookup OK
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # unofficial endpoint fails
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # atm/1.0/status/testexecution
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # atm/1.0/status
    ]
    res_status = await list_statuses("PROJ")
    assert "Test Passed" in res_status

    # test list_statuses: no project key → skips unofficial endpoint, falls to atm → hardcoded defaults
    mock_request.side_effect = [
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # atm/1.0/status/testexecution
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # atm/1.0/status
    ]
    res_status_no_key = await list_statuses()
    assert "Test Passed" in res_status_no_key
    mock_request.side_effect = None

    # test list_folders: project ID lookup fails → falls through to atm/1.0 fallbacks → returns info JSON
    mock_request.side_effect = [
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # project lookup fails
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # atm/1.0/folder
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # atm/1.0/folder/search
    ]
    res_folder = await list_folders("PROJ", "TEST_CYCLE")
    assert "Folder listing endpoint unavailable" in res_folder or "does not expose" in res_folder or "PROJ" in res_folder

    # test list_folders: project ID found but unofficial endpoint fails → falls through to info JSON
    mock_request.side_effect = [
        Response(200, json={"id": "10701", "key": "PROJ"}, request=Request("GET", "https://jira.example.com")),  # project lookup OK
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # unofficial endpoint fails
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # atm/1.0/folder
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),  # atm/1.0/folder/search
    ]
    res_folder2 = await list_folders("PROJ", "TEST_CYCLE")
    assert "PROJ" in res_folder2

    # test get_test_execution fallback (only 1 fallback now)
    mock_request.side_effect = [
        Response(404, text="Not Found", request=Request("GET", "https://jira.example.com")),
        Response(200, json={"id": 123}, request=Request("GET", "https://jira.example.com"))
    ]
    res_exec = await get_test_execution(123)
    assert "123" in res_exec

    # list_test_executions now directly calls the right endpoint (no fallbacks)
    mock_request.side_effect = None
    mock_request.return_value = Response(200, json={"id": 456}, request=Request("GET", "https://jira.example.com"))
    res_list_exec = await list_test_executions("PROJ-T1")
    assert "456" in res_list_exec
    
    # update_test_cycle is unsupported and must raise UpdateNotSupportedError
    with pytest.raises(UpdateNotSupportedError):
        await update_test_cycle("PROJ-C1", name="N", description="D", status="Done", folder_id=5, project_key="PROJ")
    
    # test create_test_plan fields
    mock_request.return_value = Response(200, json={"status": "created"}, request=Request("POST", "https://jira.example.com"))
    await create_test_plan("PROJ", "P", description="D", folder_id=1)
    
    # test create_folder fields
    mock_request.return_value = Response(200, json={"status": "folder"}, request=Request("POST", "https://jira.example.com"))
    await create_folder("PROJ", "F", parent_id=2)
    
    # test create_test_execution fields
    mock_request.return_value = Response(200, json={"status": "exec"}, request=Request("POST", "https://jira.example.com"))
    await create_test_execution("PROJ-T1", cycle_key="C1")

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_make_request_empty_success(mock_request):
    from zephyr_dc_mcp import _make_request
    mock_request.return_value = Response(204, text="", request=Request("GET", "https://jira.example.com"))
    res = await _make_request("GET", "/test")
    assert "success" in res
    assert "204" in res

@pytest.mark.asyncio
async def test_make_request_value_error(monkeypatch):
    from zephyr_dc_mcp import _make_request
    monkeypatch.delenv("ZEPHYR_BASE_URL", raising=False)
    res = await _make_request("GET", "/test")
    assert "Configuration Error" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_delete_operations(mock_request):
    """Test DELETE endpoints for test cases, cycles, and plans."""
    mock_request.return_value = Response(204, text="", request=Request("DELETE", "https://jira.example.com"))

    res = await delete_test_case("PROJ-T1")
    assert "success" in res
    assert mock_request.call_args[0][0] == "DELETE"
    assert "/testcase/PROJ-T1" in mock_request.call_args[0][1]

    res = await delete_test_cycle("PROJ-R1")
    assert "success" in res
    assert "/testrun/PROJ-R1" in mock_request.call_args[0][1]

    res = await delete_test_plan("PROJ-P1")
    assert "success" in res
    assert "/testplan/PROJ-P1" in mock_request.call_args[0][1]


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_update_test_plan(mock_request):
    """Test update_test_plan sends PUT to correct endpoint."""
    mock_request.return_value = Response(200, json={"key": "PROJ-P1"}, request=Request("PUT", "https://jira.example.com"))
    res = await update_test_plan("PROJ-P1", name="New Name", description="Desc", status="Approved")
    assert mock_request.call_args[0][0] == "PUT"
    assert "/testplan/PROJ-P1" in mock_request.call_args[0][1]
    assert mock_request.call_args[1]["json"]["name"] == "New Name"
    assert mock_request.call_args[1]["json"]["status"] == "Approved"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_get_latest_test_result(mock_request):
    """Test get_latest_test_result uses the documented /testresult/latest endpoint."""
    mock_request.return_value = Response(200, json={"id": 99, "status": "Pass"}, request=Request("GET", "https://jira.example.com"))
    res = await get_latest_test_result("PROJ-T1")
    assert "Pass" in res
    assert "/testcase/PROJ-T1/testresult/latest" in mock_request.call_args[0][1]


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_create_test_execution_in_cycle(mock_request):
    """Test create_test_execution_in_cycle uses POST /testrun/{cycle}/testcase/{tc}/testresult."""
    mock_request.return_value = Response(201, json={"id": 77}, request=Request("POST", "https://jira.example.com"))

    # basic call
    res = await create_test_execution_in_cycle("PROJ-R1", "PROJ-T1", status="Fail")
    assert "77" in res
    url = mock_request.call_args[0][1]
    assert "/testrun/PROJ-R1/testcase/PROJ-T1/testresult" in url
    assert mock_request.call_args[1]["json"]["status"] == "Fail"

    # with optional fields and status normalization
    res = await create_test_execution_in_cycle(
        "PROJ-R1", "PROJ-T1", status="PASS", comment="looks good",
        environment="Firefox", executed_by="user1"
    )
    j = mock_request.call_args[1]["json"]
    assert j["status"] == "Pass"
    assert j["comment"] == "looks good"
    assert j["executedBy"] == "user1"
    # environment goes as query param
    assert mock_request.call_args[1]["params"]["environment"] == "Firefox"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_list_test_executions_page(mock_request):
    """Test list_test_executions_page uses paginated endpoint."""
    mock_request.return_value = Response(200, json={"total": 5, "values": [{"id": 1}]}, request=Request("GET", "https://jira.example.com"))
    res = await list_test_executions_page("PROJ-R1", start_at=10, max_results=25, only_last_executions=True)
    assert "total" in res
    url = mock_request.call_args[0][1]
    assert "/testrun/PROJ-R1/testresults/page" in url
    params = mock_request.call_args[1]["params"]
    assert params["startAt"] == 10
    assert params["maxResults"] == 25
    assert params["onlyLastExecutions"] is True


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_environment_operations(mock_request):
    """Test create_environment."""
    mock_request.return_value = Response(201, json={"id": 5, "name": "Safari"}, request=Request("POST", "https://jira.example.com"))
    res = await create_environment("PROJ", "Safari", description="Safari browser env")
    assert "Safari" in res
    assert mock_request.call_args[0][0] == "POST"
    assert "/environments" in mock_request.call_args[0][1]
    j = mock_request.call_args[1]["json"]
    assert j["projectKey"] == "PROJ"
    assert j["name"] == "Safari"
    assert j["description"] == "Safari browser env"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_update_folder(mock_request):
    """Test update_folder sends PUT /folder/{id}."""
    mock_request.return_value = Response(200, json={"id": 42, "name": "New Folder Name"}, request=Request("PUT", "https://jira.example.com"))
    res = await update_folder(42, "New Folder Name")
    assert mock_request.call_args[0][0] == "PUT"
    assert "/folder/42" in mock_request.call_args[0][1]
    assert mock_request.call_args[1]["json"]["name"] == "New Folder Name"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_issue_linking_operations(mock_request):
    """Test get_test_cases_for_issue and bulk_link_test_cases_to_issues."""
    mock_request.return_value = Response(200, json=[{"key": "PROJ-T1"}], request=Request("GET", "https://jira.example.com"))
    res = await get_test_cases_for_issue("PROJ-123")
    assert "PROJ-T1" in res
    assert "/issuelink/PROJ-123/testcases" in mock_request.call_args[0][1]

    mock_request.return_value = Response(201, text="", request=Request("POST", "https://jira.example.com"))
    links = [{"testCaseKey": "PROJ-T1", "issueKey": "PROJ-123"}, {"testCaseKey": "PROJ-T2", "issueKey": "PROJ-123"}]
    res = await bulk_link_test_cases_to_issues(links)
    assert mock_request.call_args[0][0] == "POST"
    assert "/testcase/link-issues" in mock_request.call_args[0][1]
    assert mock_request.call_args[1]["json"] == {"testCaseIssueLinkList": links}
