import time
import boto3


IAM_ROLE = "<YOUR_SAGEMAKER_EXECUTION_ROLE_ARN>"
TRAINING_PLAN_ARN = "<YOUR_TRAINING_PLAN_ARN>"
REGION = "<YOUR_REGION>"
ACCOUNT_ID = "<YOUR_ACCOUNT_ID>"


# vLLM container
INFERENCE_IMAGE = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/vllm:qwen35"
INSTANCE_TYPE = "ml.p5en.48xlarge"
TIMEOUT = 3600

# Names
timestamp = time.strftime('%y%m%d-%H%M%S')
MODEL_NAME = f"qwen35-{timestamp}"
ENDPOINT_CONFIG_NAME = MODEL_NAME
ENDPOINT_NAME = MODEL_NAME

# Environment from serving.properties
ENV = {
    "OPTION_MODEL_ID": "Qwen/Qwen3.5-397B-A17B",
    "OPTION_TENSOR_PARALLEL_DEGREE": "8",
    "OPTION_MAX_MODEL_LEN": "262144",
    "OPTION_REASONING_PARSER": "qwen3",
    "OPTION_TRUST_REMOTE_CODE": "true",
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

# 4. Wait for endpoint
print("Waiting for endpoint to be InService...")
waiter = sm.get_waiter("endpoint_in_service")
waiter.wait(EndpointName=ENDPOINT_NAME, WaiterConfig={"Delay": 10, "MaxAttempts": 300})
print(f"Endpoint deployed: {ENDPOINT_NAME}")