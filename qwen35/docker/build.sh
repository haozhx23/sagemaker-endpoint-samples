#!/bin/bash
set -e

export REGION=${REGION:-${AWS_DEFAULT_REGION:-us-east-2}}
export ACCOUNT_ID=${ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
export REPOSITORY_NAME=${REPOSITORY_NAME:-vllm}
export TAG=${TAG:-qwen35}

full_name="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPOSITORY_NAME}:${TAG}"

echo "Building: ${full_name}"
DOCKER_BUILDKIT=1 docker build . --tag $REPOSITORY_NAME:$TAG --file Dockerfile

aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

aws ecr describe-repositories --region ${REGION} --repository-names "${REPOSITORY_NAME}" > /dev/null 2>&1 || \
    aws ecr create-repository --region ${REGION} --repository-name "${REPOSITORY_NAME}" > /dev/null

docker tag $REPOSITORY_NAME:$TAG ${full_name}
docker push ${full_name}

echo "Pushed: ${full_name}"
