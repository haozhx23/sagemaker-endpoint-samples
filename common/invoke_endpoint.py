"""Invoke a deployed SageMaker endpoint (OpenAI-compatible HTTP).

Replace ENDPOINT_NAME and REGION with the values printed by deploy.py.
"""
import boto3
import json


ENDPOINT_NAME = "<YOUR_ENDPOINT_NAME>"   # e.g. qwen35-260225-092242
REGION = "<YOUR_REGION>"                 # e.g. us-east-2


runtime = boto3.client("sagemaker-runtime", region_name=REGION)

payload = {
    "messages": [{"role": "user", "content": "Hello, who are you?"}],
    "chat_template_kwargs": {"enable_thinking": True},
}

response = runtime.invoke_endpoint(
    EndpointName=ENDPOINT_NAME,
    ContentType="application/json",
    Body=json.dumps(payload),
)

res = json.loads(response["Body"].read())
print("Response:", res["choices"][0]["message"]["content"])
print("Usage:", res["usage"])
