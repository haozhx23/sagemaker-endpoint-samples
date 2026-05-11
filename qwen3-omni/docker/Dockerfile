FROM vllm/vllm-omni:v0.18.0

LABEL com.amazonaws.sagemaker.capabilities.bidirectional-streaming=true

RUN pip install --no-cache-dir fastapi uvicorn[standard] websockets httpx qwen-omni-utils

COPY qwen3_omni_moe_dual_gpu.yaml /app/qwen3_omni_moe_dual_gpu.yaml
COPY app.py /app/app.py
WORKDIR /app

EXPOSE 8080
ENTRYPOINT ["python3", "app.py"]
CMD ["serve"]
