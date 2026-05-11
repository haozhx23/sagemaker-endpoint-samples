# DeepSeek-V4-Pro SageMaker inference image.
# Base image requires vLLM >= 0.20.0 for V4 model architecture support.
FROM vllm/vllm-openai:latest

COPY serve /usr/bin/serve
RUN chmod 755 /usr/bin/serve

ENTRYPOINT [ "/usr/bin/serve" ]
