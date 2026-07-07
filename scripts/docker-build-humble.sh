#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE_NAME="${CLEANY_DOCKER_IMAGE:-cleany:ros2-humble}"

docker build -t "${IMAGE_NAME}" "${REPO_ROOT}"
