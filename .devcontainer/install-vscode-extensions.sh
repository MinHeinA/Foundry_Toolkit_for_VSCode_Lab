#!/usr/bin/env bash
set -Eeuo pipefail

readonly EXTENSIONS=(
    "hashicorp.terraform"
    "ms-python.debugpy@2026.6.0"
    "ms-python.python@2026.4.0"
    "ms-python.vscode-pylance@2026.3.1"
    "ms-python.vscode-python-envs@1.36.0"
    "ms-azuretools.vscode-containers"
    "ms-azuretools.vscode-azureterraform"
    "ms-windows-ai-studio.windows-ai-studio"
)

if [[ -n "${CODE_CLI:-}" ]]; then
    code_cli="$CODE_CLI"
elif command -v code >/dev/null 2>&1; then
    code_cli="code"
elif command -v code-insiders >/dev/null 2>&1; then
    code_cli="code-insiders"
else
    echo "ERROR: VS Code CLI not found. Run this script from a VS Code terminal." >&2
    exit 1
fi

install_extension() {
    local extension="$1"
    local attempt

    for attempt in 1 2 3; do
        echo "Installing ${extension} (attempt ${attempt}/3)..."
        if "$code_cli" --install-extension "$extension" --force; then
            return 0
        fi
    done

    echo "ERROR: Failed to install ${extension} after 3 attempts." >&2
    return 1
}

for extension in "${EXTENSIONS[@]}"; do
    install_extension "$extension"
done

echo "Installed VS Code extensions:"
"$code_cli" --list-extensions --show-versions