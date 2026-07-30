# OpenCode Integration Guide

This guide provides step-by-step instructions on how to download, set up, and configure the **Zephyr Scale Data Center MCP Server** for use in [OpenCode](https://opencode.ai).

## 1. Download the Standalone Binary

The easiest way to use this MCP server is via the standalone executable, which requires zero dependencies (not even Python).

1. Navigate to the [Releases](https://github.com/dalemarchand/zephyr-dc-mcp/releases) page of the repository.
2. Download the latest `zephyr-scale-mcp` binary attached to the release.
3. Move the downloaded binary to a permanent location on your system (e.g., `~/bin/` or `~/.local/bin/`).
4. Make the binary executable by running the following command in your terminal:
   ```bash
   chmod +x /path/to/zephyr-scale-mcp
   ```

*(Alternatively, if you prefer to run from source, you can clone the repository and run it via Python 3.10+ using `uv` or `pip` as detailed in `BUILD.md`.)*

## 2. Obtain a Jira Personal Access Token (PAT)

The server authenticates with your Jira Data Center instance using a Personal Access Token.

1. Log in to your Jira Data Center instance.
2. Click on your profile picture in the top right corner and select **Profile**.
3. In the left sidebar, click on **Personal Access Tokens**.
4. Click **Create token**.
5. Give the token a memorable name (e.g., `OpenCode MCP`) and set an expiration date if desired.
6. Click **Create** and **securely copy the token**. You will not be able to view it again.

## 3. Configure OpenCode

OpenCode uses a configuration file (`opencode.json`) to register local MCP servers. You can configure this globally (for all OpenCode projects) or locally (for a specific project).

- **Global Config**: `~/.config/opencode/opencode.json`
- **Project Config**: `.opencode/opencode.json` (at the root of your workspace)

Add the `zephyr-datacenter` server definition under the top-level `"mcp"` key.

### Example Configuration

```json
{
  "mcp": {
    "zephyr-datacenter": {
      "type": "local",
      "command": ["/absolute/path/to/zephyr-scale-mcp"],
      "environment": {
        "ZEPHYR_BASE_URL": "https://jira.yourcompany.com",
        "ZEPHYR_PAT": "{env:ZEPHYR_PAT}"
      },
      "enabled": true
    }
  }
}
```

### Configuration Breakdown

- **`command`**: The absolute path to the `zephyr-scale-mcp` binary you downloaded and made executable in Step 1.
- **`ZEPHYR_BASE_URL`**: The base URL of your Jira Data Center instance (e.g., `https://jira.mycompany.com`). Do not include a trailing slash.
- **`ZEPHYR_PAT`**: Your Jira Personal Access Token. 
  - Using `{env:ZEPHYR_PAT}` instructs OpenCode to read the token securely from your terminal environment variables rather than hardcoding it into the JSON file. 
  - You must `export ZEPHYR_PAT="your-token-here"` in your shell before launching OpenCode.
  - *(Alternatively, you can hardcode the token directly in the JSON file if security is not a concern for your local environment.)*
- **`ZEPHYR_SSL_VERIFY`** (Optional): Set to `"false"` only if you are using self-signed certificates and need to bypass SSL verification. By default, the server uses your OS native certificate store.

## 4. Verify the Integration

1. Open a terminal and ensure your token is exported if using `{env:ZEPHYR_PAT}`:
   ```bash
   export ZEPHYR_PAT="your_actual_token"
   ```
2. Launch OpenCode from that same terminal session.
3. Open a chat with OpenCode and verify the connection by asking it to execute a simple read command:
   > *"Use the zephyr-datacenter MCP to list the test cases for project key PROJ."*

If configured correctly, OpenCode will execute the tool and return the list of test cases directly from your Jira instance!
