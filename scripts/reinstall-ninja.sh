#!/usr/bin/env bash
#-------------------------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See https://go.microsoft.com/fwlink/?linkid=2090316 for license information.
#-------------------------------------------------------------------------------------------------------------
#
set -e

NINJA_VERSION=${1:-"none"}

if [ "${NINJA_VERSION}" = "none" ]; then
    echo "No Ninja version specified, skipping Ninja reinstallation"
    exit 0
fi

# Cleanup temporary directory and associated files when exiting the script.
cleanup() {
    EXIT_CODE=$?
    set +e
    if [[ -n "${TMP_DIR}" ]]; then
        echo "Executing cleanup of tmp files"
        rm -Rf "${TMP_DIR}"
    fi
    exit $EXIT_CODE
}
trap cleanup EXIT


echo "Installing Ninja..."
apt-get -y purge --auto-remove ninja-build
mkdir -p /opt/ninja

architecture=$(dpkg --print-architecture)
case "${architecture}" in
    arm64)
        NINJA_BINARY_NAME="ninja-linux-aarch64.zip" ;;
    amd64)
        NINJA_BINARY_NAME="ninja-linux.zip" ;;
    *)
        echo "Unsupported architecture ${architecture}."
        exit 1
        ;;
esac

# CMAKE_CHECKSUM_NAME="cmake-${NINJA_VERSION}-SHA-256.txt"
TMP_DIR=$(mktemp -d -t ninja-XXXXXXXXXX)

echo "${TMP_DIR}"
cd "${TMP_DIR}"

curl -sSL "https://github.com/ninja-build/ninja/releases/download/v${NINJA_VERSION}/${NINJA_BINARY_NAME}" -O
# curl -sSL "https://github.com/ninja-build/ninja/releases/download/v${NINJA_VERSION}/${NINJA_CHECKSUM_NAME}" -O
# sha256sum -c --ignore-missing "${NINJA_CHECKSUM_NAME}"
unzip ${NINJA_BINARY_NAME}
cp ./ninja /usr/local/bin/ninja

which ninja
/usr/local/bin/ninja --version