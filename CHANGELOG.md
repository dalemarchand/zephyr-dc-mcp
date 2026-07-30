# Changelog

All notable changes to the Zephyr Scale Data Center MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-07-30

### Added
- Expanded parameter support across all entity creation and modification tools in `zephyr_dc_mcp.py`:
  - **Test Cases (`create_test_case`, `update_test_case`)**: Added `precondition`, `folder`, `component`, `custom_fields`, `issue_links`, `objective`, `estimated_time`, and `parameters`.
  - **Test Cycles (`create_test_cycle`)**: Added `folder`, `status`, `owner`, `version`, `iteration`, `custom_fields`, and `issue_links`.
  - **Test Plans (`create_test_plan`, `update_test_plan`)**: Added `folder`, `status`, `owner`, `labels`, `issue_links`, `custom_fields`, and `objective`.
  - **Test Executions (`create_test_execution`, `create_test_execution_in_cycle`)**: Added `execution_time`, `custom_fields`, `issue_links`, `script_results`, `actual_start_date`, and `actual_end_date`.
- Added `OPENCODE.md` containing complete setup, PAT generation, and OpenCode configuration instructions.
- Added `zephyr_get_diagnostics.sh` helper script to query and aggregate GET responses into a single JSON model.
- Added `CHANGELOG.md` to track project release history.

## [0.1.0] - 2026-07-30

### Added
- Added support for UI-backed `/foldertree` endpoint in `list_folders` (Z09).
- Fixed DTO shape for `bulk_link_test_cases_to_issues` (Z24) using `testCaseIssueLinkList`.

### Changed
- Explicitly return structured limitation notes for unsupported cycle updates (Z13) and flaky ID-based execution lookups (Z19).

## [0.0.6] - 2026-07-30

### Fixed
- Fixed numeric project ID lookup fallbacks for metadata endpoints.

## [0.0.1] - 2026-07-29

### Added
- Initial release of Zephyr Scale Data Center MCP Server with core Test Case, Cycle, Execution, Plan, Folder, Environment, and Status tools.
