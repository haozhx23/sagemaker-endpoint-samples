"""Deploy DeepSeek-V4-Pro on SageMaker — H200 profile.

Recipe: https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4-Pro?hardware=h200
"""
import time
import boto3


IAM_ROLE = "<YOUR_SAGEMAKER_EXECUTION_ROLE_ARN>"
TRAINING_PLAN_ARN = "<YOUR_TRAINING_PLAN_ARN>"
REGION = "<YOUR_REGION>"
ACCOUNT_ID = "<YOUR_ACCOUNT_ID>"


INFERENCE_IMAGE = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/vllm:deepseek-v4-pro"
INSTANCE_TYPE = "ml.p5en.48xlarge"  # 8× H200 141GB
TIMEOUT = 3600

timestamp = time.strftime("%y%m%d-%H%M%S")
MODEL_NAME = f"deepseek-v4-pro-h200-{timestamp}"
ENDPOINT_CONFIG_NAME = MODEL_NAME
ENDPOINT_NAME = MODEL_NAME


VLLM_SERVE_ARGS = """
deepseek-ai/DeepSeek-V4-Pro
--trust-remote-code
--kv-cache-dtype fp8
--block-size 256
--enable-expert-parallel
--tensor-parallel-size 8
--max-model-len 800000
--gpu-memory-utilization 0.95
--max-num-seqs 512
--max-num-batched-tokens 512
--no-enable-flashinfer-autotune
--compilation-config '{"mode": 0, "cudagraph_mode": "FULL_DECODE_ONLY"}'
--reasoning-parser deepseek_v4
--tokenizer-mode deepseek_v4
--tool-call-parser deepseek_v4
--enable-auto-tool-choice
"""

ENV = {
    "VLLM_SERVE_ARGS": VLLM_SERVE_ARGS,
    "VLLM_ENGINE_READY_TIMEOUT_S": "3600",
    "VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS": "0",
}


sm = boto3.client("sagemaker", region_name=REGION)

# 1. Create Model
print(f"Creating model: {MODEL_NAME}")
sm.create_model(
    ModelName=MODEL_NAME,
    ExecutionRoleArn=IAM_ROLE,
    PrimaryContainer={"Image": INFERENCE_IMAGE, "Environment": ENV},
)

# 2. Create Endpoint Config
print(f"Creating endpoint config: {ENDPOINT_CONFIG_NAME}")
sm.create_endpoint_config(
    EndpointConfigName=ENDPOINT_CONFIG_NAME,
    ProductionVariants=[{
        "VariantName": MODEL_NAME,
        "ModelName": MODEL_NAME,
        "InitialInstanceCount": 1,
        "InstanceType": INSTANCE_TYPE,
        "ContainerStartupHealthCheckTimeoutInSeconds": TIMEOUT,
        "ModelDataDownloadTimeoutInSeconds": TIMEOUT,
        "CapacityReservationConfig": {
            "CapacityReservationPreference": "capacity-reservations-only",
            "MlReservationArn": TRAINING_PLAN_ARN,
        },
    }],
)

# 3. Create Endpoint
print(f"Creating endpoint: {ENDPOINT_NAME}")
sm.create_endpoint(EndpointName=ENDPOINT_NAME, EndpointConfigName=ENDPOINT_CONFIG_NAME)

# 4. Wait for endpoint (960GB checkpoint: ~15-45 min cold start)
print("Waiting for endpoint to be InService...")
waiter = sm.get_waiter("endpoint_in_service")
waiter.wait(EndpointName=ENDPOINT_NAME, WaiterConfig={"Delay": 30, "MaxAttempts": 360})
print(f"Endpoint deployed: {ENDPOINT_NAME}")
