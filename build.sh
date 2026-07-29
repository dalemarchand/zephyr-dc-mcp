#!/bin/bash
# Exit on any error
set -e

echo "Building standalone executable with PyInstaller..."
# PyInstaller needs metadata for fastmcp and truststore
uv run pyinstaller --onefile --copy-metadata fastmcp --copy-metadata truststore --name zephyr-scale-mcp zephyr_dc_mcp.py

echo "Build complete. Executable is located in the dist/ folder."


