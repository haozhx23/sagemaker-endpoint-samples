# Qwen3.5 SageMaker Endpoint 部署

在 SageMaker 上用 vLLM OpenAI-compatible 容器部署 Qwen3.5。

## 配置摘要

- **推理后端**:`vllm/vllm-openai:qwen3_5`
- **实例**:`ml.p5en.48xlarge`(8×H200)
- **并行**:`tensor-parallel-size = 8`
- **上下文**:`max-model-len = 262144`
- **Reasoning parser**:`qwen3`

## 1. 构建镜像

```bash
cd docker && ./build.sh
```

`build.sh` 默认用 `AWS_DEFAULT_REGION` 和 `aws sts get-caller-identity` 推断 region/account,可通过 `REGION` / `ACCOUNT_ID` / `TAG` 环境变量覆盖。

`serve` 脚本把 `SM_VLLM_*` 环境变量转成 vLLM 启动参数。例如 `SM_VLLM_TENSOR_PARALLEL_SIZE=8` → `--tensor-parallel-size 8`。这是 SageMaker 传参给 vLLM 的通用方式。

## 2. 部署 Endpoint

编辑 `deploy.py`,按需修改:

- `REGION / IAM_ROLE / INFERENCE_IMAGE`
- `INSTANCE_TYPE`(默认 `ml.p5en.48xlarge`)
- `ENV` 里的推理参数(用 `OPTION_*` 前缀,容器会映射给 vLLM)
- `TRAINING_PLAN_ARN` —— 如果走 Capacity Reservation;否则删除 `CapacityReservationConfig`

然后:

```bash
python deploy.py
```

## 3. 调用

用仓库根的通用脚本:

```bash
python ../common/invoke_endpoint.py  # 先改 ENDPOINT_NAME
```

请求体示例(支持 thinking 模式):

```json
{
  "messages": [{"role": "user", "content": "Hello, who are you?"}],
  "chat_template_kwargs": {"enable_thinking": true}
}
```
