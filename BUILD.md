# Building Zephyr Scale Data Center MCP Server

This guide explains how to set up, develop, test, and build the Zephyr Scale Data Center MCP Server.

## Prerequisites & Requirements

- **Python Version**: **Python 3.10 or higher** (Python 3.10, 3.11, or 3.12 recommended).
- **Supported Operating Systems**: Linux, macOS, Windows.

---

## 1. Local Environment Setup

You can set up your development environment using standard Python (`python3` + `pip`) or using [`uv`](https://github.com/astral-sh/uv).

### Option A: Standard Python (`pip` & `venv`)

1. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install runtime and development dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

### Option B: Using `uv`

1. **Create a virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   uv pip install -r requirements-dev.txt
   ```

---

## 2. Running Automated Tests

The project uses `pytest` with async support (`pytest-asyncio`) and mocks for HTTP calls.

### Using standard `pytest`:
```bash
PYTHONPATH=. pytest tests/
```

### Using `uv`:
```bash
PYTHONPATH=. uv run pytest tests/
```

---

## 3. Building Standalone Executable (PyInstaller)

To package the MCP server as a standalone, zero-dependency binary (e.g. for deployment with OpenCode without needing Python installed):

### Using the build script:
```bash
./build.sh
```

### Or running PyInstaller manually:
```bash
# With standard pip/venv active:
pyinstaller --onefile --copy-metadata fastmcp --copy-metadata truststore --name zephyr-scale-mcp zephyr_dc_mcp.py

# Or with uv:
uv run pyinstaller --onefile --copy-metadata fastmcp --copy-metadata truststore --name zephyr-scale-mcp zephyr_dc_mcp.py
```

The compiled standalone executable will be generated at `dist/zephyr-scale-mcp`.

---

## 5. Continuous Integration (GitHub Actions)

A GitHub Actions workflow is configured in [.github/workflows/ci.yml](.github/workflows/ci.yml).

- **Triggers**: Executed automatically on all Pull Requests targeting `main` and on pushes to `main`.
- **Matrix Testing**: Runs tests across Python 3.10, 3.11, and 3.12.
- **Pull Request Enforcement**: To require all PRs to pass tests before merging:
  1. Go to your GitHub repository: `https://github.com/dalemarchand/zephyr-dc-mcp/settings/branches`.
  2. Click **Add branch protection rule** for `main`.
  3. Enable **Require status checks to pass before merging**.
  4. Search and select `Run Pytest Suite` status check.

