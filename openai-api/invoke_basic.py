"""Invoke a SageMaker OpenAI-compatible endpoint via the OpenAI SDK (non-streaming)."""
from openai import OpenAI

from sm_token import generate_sm_token


ENDPOINT_NAME = "<YOUR_ENDPOINT_NAME>"   # e.g. qwen35-260225-092242
REGION = "<YOUR_REGION>"                 # e.g. us-east-2
MODEL = "<YOUR_SERVED_MODEL_NAME>"       # value of OPTION_SERVED_MODEL_NAME


client = OpenAI(
    base_url=f"https://runtime.sagemaker.{REGION}.amazonaws.com/endpoints/{ENDPOINT_NAME}/openai/v1",
    api_key=generate_sm_token(region=REGION),
)

resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, who are you?"},
    ],
    max_tokens=64,
    temperature=0.2,
)

print(resp.choices[0].message.content)
print(f"Usage: prompt={resp.usage.prompt_tokens} completion={resp.usage.completion_tokens}")
