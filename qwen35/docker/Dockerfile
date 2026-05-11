FROM vllm/vllm-openai:qwen3_5

COPY serve /usr/bin/serve
RUN chmod 777 /usr/bin/serve

ENTRYPOINT [ "/usr/bin/serve" ]
