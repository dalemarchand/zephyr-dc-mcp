#!/usr/bin/env bash
# Zephyr Scale Data Center GET Operations Diagnostic Aggregator Script
# Usage: export JIRA_PERSONAL_TOKEN="your_token_here" && ./zephyr_get_diagnostics.sh

export ZEPHYR_BASE_URL="${ZEPHYR_BASE_URL:-https://jira.yourcompany.com}"
export JIRA_PERSONAL_TOKEN="${JIRA_PERSONAL_TOKEN:-your_jira_personal_token_here}"

export PROJECT_KEY="${PROJECT_KEY:-PROJ}"
export PROJECT_ID="${PROJECT_ID:-10000}"
export TEST_CASE_KEY="${TEST_CASE_KEY:-PROJ-T1}"
export TEST_CYCLE_KEY="${TEST_CYCLE_KEY:-PROJ-C1}"
export TEST_PLAN_KEY="${TEST_PLAN_KEY:-PROJ-P1}"
export EXECUTION_ID="${EXECUTION_ID:-1001}"
export ISSUE_KEY="${ISSUE_KEY:-PROJ-100}"

python3 - << 'EOF'
import os, json, urllib.request, urllib.error, ssl

base_url = os.environ.get("ZEPHYR_BASE_URL", "https://jira.yourcompany.com").rstrip("/")
token = os.environ.get("JIRA_PERSONAL_TOKEN", "")
project_key = os.environ.get("PROJECT_KEY", "PROJ")
project_id = os.environ.get("PROJECT_ID", "10000")
test_case_key = os.environ.get("TEST_CASE_KEY", "PROJ-T1")
test_cycle_key = os.environ.get("TEST_CYCLE_KEY", "PROJ-C1")
test_plan_key = os.environ.get("TEST_PLAN_KEY", "PROJ-P1")
execution_id = os.environ.get("EXECUTION_ID", "1001")
issue_key = os.environ.get("ISSUE_KEY", "PROJ-100")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

endpoints = {
    "get_test_case": f"/rest/atm/1.0/testcase/{test_case_key}",
    "search_test_cases": f"/rest/atm/1.0/testcase/search?query=projectKey%20%3D%20%22{project_key}%22&maxResults=2",
    "get_test_cycle": f"/rest/atm/1.0/testrun/{test_cycle_key}",
    "search_test_cycles": f"/rest/atm/1.0/testrun/search?query=projectKey%20%3D%20%22{project_key}%22&maxResults=2",
    "get_test_plan": f"/rest/atm/1.0/testplan/{test_plan_key}",
    "search_test_plans": f"/rest/atm/1.0/testplan/search?query=projectKey%20%3D%20%22{project_key}%22&maxResults=2",
    "get_test_execution_by_id": f"/rest/atm/1.0/testresult/{execution_id}",
    "get_latest_test_result": f"/rest/atm/1.0/testcase/{test_case_key}/testresult/latest",
    "list_cycle_executions": f"/rest/atm/1.0/testrun/{test_cycle_key}/testresults",
    "list_cycle_executions_page": f"/rest/atm/1.0/testrun/{test_cycle_key}/testresults/page?startAt=0&maxResults=2",
    "list_folders_official": f"/rest/atm/1.0/folder?projectKey={project_key}&type=TEST_CASE",
    "get_folder_tree_ui": f"/rest/tests/1.0/project/{project_id}/foldertree/testcase",
    "list_environments": f"/rest/atm/1.0/environments?projectKey={project_key}",
    "list_statuses_ui": f"/rest/tests/1.0/project/{project_id}/testcasestatus",
    "get_issue_test_cases": f"/rest/atm/1.0/issuelink/{issue_key}/testcases"
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

results = {}
for key, url_path in endpoints.items():
    full_url = f"{base_url}{url_path}"
    req = urllib.request.Request(full_url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            body = response.read().decode("utf-8")
            try:
                results[key] = json.loads(body)
            except Exception:
                results[key] = body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            results[key] = {"error": f"HTTP {e.code}", "body": json.loads(body)}
        except Exception:
            results[key] = {"error": f"HTTP {e.code}", "body": body}
    except Exception as e:
        results[key] = {"error": str(e)}

out_file = "zephyr_get_aggregated_results.json"
with open(out_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"Aggregation complete! Results written to {out_file}")
print(json.dumps(results, indent=2))
EOF
