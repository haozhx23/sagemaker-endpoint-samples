#!/usr/bin/env python3
"""Deploy Qwen3-Omni bidirection streaming endpoint on SageMaker."""
import time
import boto3

REGION = "us-east-1"
ACCOUNT_ID = "633205212955"
IAM_ROLE = f"arn:aws:iam::{ACCOUNT_ID}:role/service-role/AmazonSageMaker-ExecutionRole-20220923T160810"

# IMAGE_URI = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/sagemaker-bidi-stream:echo-v1"
# IMAGE_URI = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/sagemaker-bidi-stream:qwen3omni-v2"  # text only
# IMAGE_URI = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/sagemaker-bidi-stream:qwen3omni-v3"  # text + audio (vllm-openai, thinker only)
IMAGE_URI = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/sagemaker-bidi-stream:qwen3omni-omni-v2"  # vllm-omni full pipeline, dual GPU

INSTANCE_TYPE = "ml.g7e.12xlarge"
TIMEOUT = 1800

sm = boto3.client("sagemaker", region_name=REGION)
ts = time.strftime("%y%m%d-%H%M%S")
name = f"bidirection-qwen3omni-{ts}"

print(f"Image:    {IMAGE_URI}")
print(f"Instance: {INSTANCE_TYPE}")
print(f"Name:     {name}")

sm.create_model(ModelName=name, ExecutionRoleArn=IAM_ROLE, PrimaryContainer={"Image": IMAGE_URI})
sm.create_endpoint_config(EndpointConfigName=name, ProductionVariants=[{
    "VariantName": name, "ModelName": name, "InitialInstanceCount": 1,
    "InstanceType": INSTANCE_TYPE,
    "ContainerStartupHealthCheckTimeoutInSeconds": TIMEOUT,
    "ModelDataDownloadTimeoutInSeconds": TIMEOUT,
}])
sm.create_endpoint(EndpointName=name, EndpointConfigName=name)
print(f"\nEndpoint creating: {name}")
print(f"Check: aws sagemaker describe-endpoint --endpoint-name {name} --region {REGION} --query EndpointStatus")
