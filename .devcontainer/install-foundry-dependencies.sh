#!/usr/bin/env bash
set -Eeuo pipefail

readonly FOUNDRY_AZD_EXTENSION="microsoft.foundry"
readonly FOUNDRY_AZD_EXTENSION_VERSION="${FOUNDRY_AZD_EXTENSION_VERSION:-1.0.0-beta.2}"

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly script_dir
workspace_root="$(cd -- "$script_dir/.." && pwd)"
readonly workspace_root
readonly lab01_agent_dir="$workspace_root/workshop/lab01-single-agent/agent"
readonly lab01_requirements="$lab01_agent_dir/requirements.txt"
readonly lab01_venv="$lab01_agent_dir/.venv"

for command_name in azd jq python; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "ERROR: Required command not found: $command_name" >&2
        exit 1
    fi
done

installed_foundry_version="$(
    azd extension list --output json \
        | jq -r --arg id "$FOUNDRY_AZD_EXTENSION" \
            '.[] | select(.id == $id) | .installedVersion'
)"

if [[ "$installed_foundry_version" != "$FOUNDRY_AZD_EXTENSION_VERSION" ]]; then
    echo "Installing $FOUNDRY_AZD_EXTENSION $FOUNDRY_AZD_EXTENSION_VERSION..."
    azd extension install "$FOUNDRY_AZD_EXTENSION" \
        --version "$FOUNDRY_AZD_EXTENSION_VERSION" \
        --force \
        --no-prompt
else
    echo "$FOUNDRY_AZD_EXTENSION $FOUNDRY_AZD_EXTENSION_VERSION is already installed."
fi

if [[ ! -f "$lab01_requirements" ]]; then
    echo "ERROR: Lab 01 requirements not found: $lab01_requirements" >&2
    exit 1
fi

if [[ ! -x "$lab01_venv/bin/python" ]]; then
    echo "Creating Lab 01 virtual environment..."
    python -m venv "$lab01_venv"
fi

echo "Installing Lab 01 Python dependencies..."
"$lab01_venv/bin/python" -m pip install \
    --disable-pip-version-check \
    --requirement "$lab01_requirements"
"$lab01_venv/bin/python" -m pip check

echo "Foundry CLI and Lab 01 SDK dependencies are ready."