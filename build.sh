#!/bin/bash
# Exit on any error
set -e

echo "Building standalone executable with PyInstaller..."
# Use uv if available, otherwise fallback to pyinstaller
if command -v uv &> /dev/null; then
    uv run pyinstaller --onefile --copy-metadata fastmcp --copy-metadata truststore --name zephyr-scale-mcp zephyr_dc_mcp.py
else
    pyinstaller --onefile --copy-metadata fastmcp --copy-metadata truststore --name zephyr-scale-mcp zephyr_dc_mcp.py
fi

echo "Build complete. Executable is located in the dist/ folder."



