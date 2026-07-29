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
    get_test_script,
    create_or_update_test_script,
    link_test_to_issue,
    get_test_cycle,
    search_test_cycles,
    create_test_cycle,
    update_test_cycle,
    create_test_execution,
    get_test_execution,
    list_test_executions,
    get_test_plan,
    search_test_plans,
    create_test_plan,
    list_folders,
    create_folder,
    list_environments,
    list_statuses,
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
    assert "fields" in mock_request.call_args[1]["params"]

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_create_and_update_test_case(mock_request):

    mock_request.return_value = Response(201, json={"key": "PROJ-T200"}, request=Request("POST", "https://jira.example.com"))
    res_create = await create_test_case("PROJ", "New Auth Test", status="Approved", priority="High")
    assert "PROJ-T200" in res_create
    assert mock_request.call_args[1]["json"]["name"] == "New Auth Test"

    mock_request.return_value = Response(200, json={"key": "PROJ-T200", "name": "Updated Name"}, request=Request("PUT", "https://jira.example.com"))
    res_update = await update_test_case("PROJ-T200", name="Updated Name")
    assert "Updated Name" in res_update

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_test_scripts(mock_request):
    mock_request.return_value = Response(200, json={"type": "STEP_BY_STEP", "steps": []}, request=Request("GET", "https://jira.example.com"))
    get_res = await get_test_script("PROJ-T100")
    assert "STEP_BY_STEP" in get_res

    mock_request.return_value = Response(200, json={"status": "success"}, request=Request("POST", "https://jira.example.com"))
    steps = [{"description": "Step 1", "expectedResult": "Pass"}]
    post_res = await create_or_update_test_script("PROJ-T100", steps)
    assert "success" in post_res
    assert mock_request.call_args[1]["json"]["steps"] == steps

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

    mock_request.return_value = Response(200, json={"key": "PROJ-R2", "status": "Done"}, request=Request("PUT", "https://jira.example.com"))
    res_update = await update_test_cycle("PROJ-R2", status="Done")
    assert "Done" in res_update

@pytest.mark.asyncio
@patch("httpx.AsyncClient.request")
async def test_test_executions(mock_request):
    mock_request.return_value = Response(201, json={"id": 500}, request=Request("POST", "https://jira.example.com"))
    res_create = await create_test_execution("PROJ-T1", "pass")
    assert "500" in res_create
    assert mock_request.call_args[1]["json"]["status"] == "PASS"

    mock_request.return_value = Response(200, json={"id": 500, "status": "PASS"}, request=Request("GET", "https://jira.example.com"))
    res_get = await get_test_execution(500)
    assert "PASS" in res_get

    mock_request.return_value = Response(200, json=[{"id": 500}], request=Request("GET", "https://jira.example.com"))
    res_list = await list_test_executions("PROJ-T1")
    assert "500" in res_list

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
    mock_request.return_value = Response(200, json=[{"id": 1, "name": "Regression"}], request=Request("GET", "https://jira.example.com"))
    res_folders = await list_folders("PROJ", "TEST_CASE")
    assert "Regression" in res_folders

    mock_request.return_value = Response(201, json={"id": 2, "name": "Sanity"}, request=Request("POST", "https://jira.example.com"))
    res_create_folder = await create_folder("PROJ", "Sanity")
    assert "Sanity" in res_create_folder

    mock_request.return_value = Response(200, json=[{"name": "Staging"}], request=Request("GET", "https://jira.example.com"))
    res_env = await list_environments("PROJ")
    assert "Staging" in res_env

    mock_request.return_value = Response(200, json=[{"name": "PASS"}], request=Request("GET", "https://jira.example.com"))
    res_statuses = await list_statuses("PROJ")
    assert "PASS" in res_statuses

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



