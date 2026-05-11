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