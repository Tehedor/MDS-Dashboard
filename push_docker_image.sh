#!/usr/bin/env bash
set -euo pipefail


MODE="${MODE:-docker}" # "docker" or "buildx"
# MODE="${MODE:-buildx}" # "docker" or "buildx"
BUILDER_NAME="mi_builder"
BUILDKIT_CONTAINER="buildx_buildkit_${BUILDER_NAME}0"

DOCKERHUB_USER="stehedor"
IMAGE_NAME="mds_temporal_app"
TAG="v0"

if [[ -z "$DOCKERHUB_USER" || -z "$IMAGE_NAME" ]]; then
	echo "Usage: $0 <dockerhub_user> <image_name> [tag]"
	exit 1
fi

FULL_IMAGE_NAME="${DOCKERHUB_USER}/${IMAGE_NAME}:${TAG}"

ensure_buildx_builder() {
	if ! docker ps --format '{{.Names}}' | grep -qx "${BUILDKIT_CONTAINER}"; then
		echo "BuildKit container not running. Creating/starting buildx builder..."
		if docker buildx inspect "${BUILDER_NAME}" >/dev/null 2>&1; then
			docker buildx use "${BUILDER_NAME}" >/dev/null
		else
			docker buildx create --name "${BUILDER_NAME}" --driver docker-container --use >/dev/null
		fi
		docker buildx inspect --bootstrap >/dev/null
	fi
}

cleanup_buildx_builder() {
	if docker ps -a --format '{{.Names}}' | grep -qx "${BUILDKIT_CONTAINER}"; then
		echo "Stopping and removing BuildKit container: ${BUILDKIT_CONTAINER}"
		docker stop "${BUILDKIT_CONTAINER}" >/dev/null || true
		docker rm "${BUILDKIT_CONTAINER}" >/dev/null || true
	fi
}

if [[ "${MODE}" == "docker" ]]; then
	echo "Building image: ${FULL_IMAGE_NAME}"
	docker build -t "${FULL_IMAGE_NAME}" .

	echo "Pushing image: ${FULL_IMAGE_NAME}"
	docker push "${FULL_IMAGE_NAME}"
elif [[ "${MODE}" == "buildx" ]]; then
	ensure_buildx_builder
	echo "Building and pushing image: ${FULL_IMAGE_NAME}"
	docker buildx build --platform "linux/amd64,linux/arm64" -t "${FULL_IMAGE_NAME}" --push .
	cleanup_buildx_builder
else
	echo "Invalid MODE: ${MODE}. Use 'docker' or 'buildx'."
	exit 1
fi

echo "Done."