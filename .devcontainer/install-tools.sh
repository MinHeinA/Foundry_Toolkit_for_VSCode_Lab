#!/usr/bin/env bash
set -Eeuo pipefail

readonly TERRAFORM_VERSION="${TERRAFORM_VERSION:-1.15.9}"
readonly AZURE_CLI_VERSION="${AZURE_CLI_VERSION:-2.89.1}"
readonly AZD_VERSION="${AZD_VERSION:-1.31.2}"

if [[ ! -r /etc/os-release ]]; then
    echo "ERROR: Cannot identify the Linux distribution." >&2
    exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
if [[ "${ID:-}" != "debian" || "${VERSION_CODENAME:-}" != "bookworm" ]]; then
    echo "ERROR: This script supports Debian 12 (Bookworm); found ${PRETTY_NAME:-unknown}." >&2
    exit 1
fi

if [[ "$(id -u)" -eq 0 ]]; then
    SUDO=()
elif command -v sudo >/dev/null 2>&1; then
    SUDO=(sudo)
else
    echo "ERROR: Run as root or install sudo." >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive
temp_dir="$(mktemp -d)"
trap 'rm -rf "$temp_dir"' EXIT

echo "Installing base packages..."
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    git \
    gnupg \
    jq \
    lsb-release \
    unzip \
    wget

echo "Configuring the Azure CLI repository..."
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    -o "$temp_dir/microsoft.asc"
gpg --batch --dearmor --yes \
    --output "$temp_dir/microsoft.gpg" "$temp_dir/microsoft.asc"
"${SUDO[@]}" install -D -m 0644 "$temp_dir/microsoft.gpg" \
    /etc/apt/keyrings/microsoft.gpg
printf '%s\n' \
    'Types: deb' \
    'URIs: https://packages.microsoft.com/repos/azure-cli/' \
    'Suites: bookworm' \
    'Components: main' \
    "Architectures: $(dpkg --print-architecture)" \
    'Signed-by: /etc/apt/keyrings/microsoft.gpg' \
    | "${SUDO[@]}" tee /etc/apt/sources.list.d/azure-cli.sources >/dev/null

echo "Configuring the HashiCorp repository..."
curl -fsSL https://apt.releases.hashicorp.com/gpg \
    -o "$temp_dir/hashicorp.asc"
gpg --batch --dearmor --yes \
    --output "$temp_dir/hashicorp.gpg" "$temp_dir/hashicorp.asc"
"${SUDO[@]}" install -D -m 0644 "$temp_dir/hashicorp.gpg" \
    /etc/apt/keyrings/hashicorp.gpg
printf '%s\n' \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com bookworm main" \
    | "${SUDO[@]}" tee /etc/apt/sources.list.d/hashicorp.list >/dev/null

echo "Installing Azure CLI ${AZURE_CLI_VERSION} and Terraform ${TERRAFORM_VERSION}..."
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y --no-install-recommends \
    "azure-cli=${AZURE_CLI_VERSION}-1~bookworm" \
    "terraform=${TERRAFORM_VERSION}-1"

echo "Installing Azure Developer CLI ${AZD_VERSION}..."
curl -fsSL https://aka.ms/install-azd.sh -o "$temp_dir/install-azd.sh"
chmod +x "$temp_dir/install-azd.sh"
"$temp_dir/install-azd.sh" --version "$AZD_VERSION"

"${SUDO[@]}" rm -rf /var/lib/apt/lists/*

python -c 'import sys; assert sys.version_info >= (3, 13), sys.version'
echo "Installed prerequisites:"
python --version
terraform version | head -n 1
az version --output json | jq -r '"azure-cli " + .["azure-cli"]'
azd version