"""Invoke a SageMaker OpenAI-compatible endpoint via the OpenAI SDK (streaming).

SageMakerOpenAITransport unwraps the AWS EventStream binary frame on the
text/event-stream response so the OpenAI SDK sees clean SSE.
SageMakerAuth re-signs the bearer token on every request.
"""
import sys

import httpx
from openai import OpenAI

from sm_token import SageMakerAuth, SageMakerOpenAITransport


ENDPOINT_NAME = "<YOUR_ENDPOINT_NAME>"   # e.g. qwen35-260225-092242
REGION = "<YOUR_REGION>"                 # e.g. us-east-2
MODEL = "<YOUR_SERVED_MODEL_NAME>"       # value of OPTION_SERVED_MODEL_NAME


http_client = httpx.Client(
    transport=SageMakerOpenAITransport(),
    auth=SageMakerAuth(region=REGION),
)

client = OpenAI(
    base_url=f"https://runtime.sagemaker.{REGION}.amazonaws.com/endpoints/{ENDPOINT_NAME}/openai/v1",
    api_key="placeholder-overridden-by-SageMakerAuth",
    http_client=http_client,
)

stream = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Count from 1 to 5, one number per line."},
    ],
    max_tokens=128,
    temperature=0.0,
    stream=True,
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        sys.stdout.write(chunk.choices[0].delta.content)
        sys.stdout.flush()
print()
