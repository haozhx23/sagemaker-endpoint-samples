# Qwen3-Omni SageMaker Endpoint 部署(双向流式)

基于 `vllm/vllm-omni` 容器部署 Qwen3-Omni-30B-A3B-Instruct 全流程多模态 endpoint,支持**文本 + 音频**输入与**流式文本 + 音频**输出,通过 WebSocket 进行双向交互。

## 架构

```
Client (WebSocket)
   │
   ▼
FastAPI /invocations-bidirectional-stream (port 8080)
   │
   ▼
vllm-omni (port 8000, 3-stage pipeline)
   ├── Stage 0: Thinker  → GPU 0 (latent output)
   ├── Stage 1: Talker   → GPU 1 (latent output)
   └── Stage 2: Code2Wav → GPU 1 (audio output)
```

- **Thinker** 理解输入 + 生成文本(`final_output_type: text`)
- **Talker** 把文本 latent 转成语音 token
- **Code2Wav** 把语音 token 转成 WAV 音频块

三阶段 pipeline 配置见 [`docker/qwen3_omni_moe_dual_gpu.yaml`](./docker/qwen3_omni_moe_dual_gpu.yaml)。

## 配置摘要

- **推理后端**:`vllm/vllm-omni:v0.18.0` + `vllm-omni` 多 stage 调度
- **实例**:`ml.g7e.12xlarge`(2× RTX PRO 6000 96GB)
- **模型**:`Qwen/Qwen3-Omni-30B-A3B-Instruct`(需 `trust_remote_code=true`)
- **SageMaker 能力**:`com.amazonaws.sagemaker.capabilities.bidirectional-streaming=true`

## 1. 构建镜像

```bash
cd docker && ./build.sh
```

`build.sh` 默认用 `AWS_DEFAULT_REGION` 和 `aws sts get-caller-identity` 推断 region/account。镜像 tag 默认 `qwen3omni-omni-v2`。

## 2. 部署 Endpoint

编辑 `deploy.py`,按需修改:

- `REGION / ACCOUNT_ID / IAM_ROLE`
- `IMAGE_URI`(对应 `docker/build.sh` 推送的 tag)
- `INSTANCE_TYPE`

然后:

```bash
python deploy.py
```

## 3. 调用(WebSocket)

不能用通用 `invoke_endpoint.py`(那是 HTTP JSON)。需要 WebSocket 客户端:

```python
# 示例:通过 SageMaker Runtime v2 API 发起 WebSocket
# TODO: 补充完整 client 示例(sagemaker-runtime invoke-endpoint-with-response-stream 或直接 WS 连接)
```

**协议**:
- Client → Server:JSON `{"messages": [...], "modalities": ["text", "audio"]}`
- Server → Client:
  - 文本 token:WebSocket Text frame
  - 音频 WAV chunk:WebSocket Binary frame
  - 控制事件:`{"event": "audio_start"}`、`{"event": "audio_end"}`、`{"event": "turn_end"}`

## GPU 分配细节

见 `docker/qwen3_omni_moe_dual_gpu.yaml`:

| Stage | GPU | 作用 | gpu_memory_utilization |
|-------|-----|------|------------------------|
| 0 Thinker | 0 | 理解 + 生文本 latent | 0.9 |
| 1 Talker | 1 | 文本 → 语音 token | 0.6 |
| 2 Code2Wav | 1 | 语音 token → WAV | 0.1 |

基于官方 `qwen3_omni_moe.yaml`(2×H100-80G)改为 2×96GB 配置,放宽了显存预算。
