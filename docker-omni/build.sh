#!/bin/bash
set -e

REGION=${AWS_DEFAULT_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_NAME=sagemaker-bidi-stream
TAG=qwen3omni-omni-v2

IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${TAG}"

echo "Building: ${IMAGE_URI}"
DOCKER_BUILDKIT=1 docker build --platform linux/amd64 --provenance=false -t ${REPO_NAME}:${TAG} .

aws ecr get-login-password --region ${REGION} | \
    docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

aws ecr describe-repositories --region ${REGION} --repository-names "${REPO_NAME}" > /dev/null 2>&1 || \
    aws ecr create-repository --region ${REGION} --repository-name "${REPO_NAME}" > /dev/null

docker tag ${REPO_NAME}:${TAG} ${IMAGE_URI}
docker push ${IMAGE_URI}

echo "Pushed: ${IMAGE_URI}"
