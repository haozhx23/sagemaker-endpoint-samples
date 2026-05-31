# SageMaker Endpoint Samples

在 SageMaker 上部署大模型推理 endpoint 的示例。

## 支持的模型

| 模型 | 目录 | 实例 |
|------|------|------|
| Qwen3.5 | [`qwen35/`](./qwen35/) | `ml.p5en.48xlarge` |
| Qwen3-Omni(双向流式) | [`qwen3-omni/`](./qwen3-omni/) | `ml.g7e.12xlarge` |
| DeepSeek-V4-Pro | [`deepseek-v4/`](./deepseek-v4/) | `ml.p5en.48xlarge` / `ml.p6-b200.48xlarge` |

## Entries

```
<model>/
├── deploy*.py       # SageMaker 部署脚本(一个或多个)
└── docker/          # 镜像构建 (Dockerfile + build.sh + serve | app.py)
```

通用部署流程:

```bash
cd <model>/docker && ./build.sh    # 1. 构建推送镜像
cd .. && python deploy*.py         # 2. 部署 endpoint
python ../common/invoke_endpoint.py   # 3. 调用(HTTP 模型)
```

## DeepSeek-V4-Pro

基于 vLLM 官方 recipe 部署 `deepseek-ai/DeepSeek-V4-Pro`。参考:[B200](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4-Pro?hardware=b200) / [H200](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4-Pro?hardware=h200)。

提供 B200 / H200 两套部署脚本，共用同一镜像:

```bash
cd deepseek-v4/docker && ./build.sh && cd ..

# 配置脚本顶部的 REGION / ACCOUNT_ID / IAM_ROLE / TRAINING_PLAN_ARN 后执行:
python deploy_h200.py    # 8× H200, ml.p5en.48xlarge
python deploy_b200.py    # 8× B200, ml.p6-b200.48xlarge
```

部署参数通过 `VLLM_SERVE_ARGS` 环境变量注入,内容即 vLLM recipe 命令原文,修改无需重建镜像。

## OpenAI-Compatible 调用(新特性)

[`openai-api/`](./openai-api/) 演示 SageMaker AI endpoint 的 [OpenAI 兼容调用路径](https://aws.amazon.com/blogs/machine-learning/announcing-openai-compatible-api-support-for-amazon-sagemaker-ai-endpoints/)(`/openai/v1/*` + bearer token,2026-05 新特性)。**容器层无需任何调整** —— 任何已部署、能 serve OpenAI Chat Completions 的 endpoint(包括本仓库的 `qwen35/` / `deepseek-v4/` 等)都可直接调用。

```bash
cd openai-api
pip install -r requirements.txt

# 编辑 invoke_*.py 顶部的 ENDPOINT_NAME / REGION / MODEL 占位符
python invoke_basic.py        # OpenAI SDK 非流式
python invoke_streaming.py    # OpenAI SDK 流式
```

调用方 IAM 至少需要:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow",
     "Action": "sagemaker:InvokeEndpoint",
     "Resource": "arn:aws:sagemaker:<REGION>:<ACCOUNT_ID>:endpoint/<ENDPOINT_NAME>"},
    {"Effect": "Allow",
     "Action": "sagemaker:CallWithBearerToken",
     "Resource": "*"}
  ]
}
```

`CallWithBearerToken` 不支持 resource-level 限制 —— 生成 token 的角色一定要严格收敛权限(只授予它实际需要调用的 endpoint 上的 `InvokeEndpoint`),避免 token 泄漏被滥用到其他 endpoint。

> **Streaming caveat**:SageMaker 在 `text/event-stream` 响应里多包了一层 AWS EventStream binary frame,直接用标准 OpenAI SDK `stream=True` 会抛 `UnicodeDecodeError`。`sm_token.SageMakerOpenAITransport` 在 httpx 层透明拆封装,装上后业务代码就是标准 OpenAI 写法。
