#!/usr/bin/env python3
"""
Qwen3-Omni Bidirectional Streaming Server for SageMaker (vllm-omni edition).
- /ping: health check
- /invocations: placeholder (required by SageMaker)
- /invocations-bidirectional-stream: WebSocket — text/audio in, streaming text+audio out
"""
import base64
import json
import os
import subprocess
import sys
import time

import httpx
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

app = FastAPI()

VLLM_URL = "http://127.0.0.1:8000"
MODEL_ID = "Qwen/Qwen3-Omni-30B-A3B-Instruct"
STAGE_CONFIG = "/app/qwen3_omni_moe_dual_gpu.yaml"
vllm_process = None


def start_vllm():
    global vllm_process
    env = os.environ.copy()
    env["VLLM_USE_V1"] = "0"
    cmd = [
        "vllm", "serve", MODEL_ID,
        "--omni",
        "--stage-configs-path", STAGE_CONFIG,
        "--host", "127.0.0.1",
        "--port", "8000",
        "--allowed-local-media-path", "/",
    ]
    print(f"Starting vllm-omni: {' '.join(cmd)}", flush=True)
    vllm_process = subprocess.Popen(cmd, env=env)


def wait_for_vllm(timeout=900):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = httpx.get(f"{VLLM_URL}/health", timeout=5)
            if r.status_code == 200:
                print("vllm-omni is ready!", flush=True)
                return True
        except Exception:
            pass
        time.sleep(5)
    raise RuntimeError("vllm-omni failed to start within timeout")


@app.get("/ping")
@app.post("/ping")
async def ping():
    return JSONResponse(content={"status": "healthy"})


@app.post("/invocations")
async def invocations():
    return JSONResponse(content={"status": "use websocket endpoint"})


@app.websocket("/invocations-bidirectional-stream")
async def websocket_bidirection(websocket: WebSocket):
    """
    Bidirectional streaming: receive text/audio messages, stream back text + audio.

    Protocol:
      Client sends JSON: {"messages": [...], "modalities": ["text","audio"]}
      Server streams back:
        - text tokens as WebSocket Text frames
        - audio WAV chunks as WebSocket Binary frames
        - JSON control frames: {"event": "audio_start"}, {"event": "audio_end"},
          {"event": "turn_end"}
    """
    await websocket.accept()
    messages = []

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.receive":
                data = message.get("text") or (message.get("bytes", b"").decode("utf-8"))
                if not data:
                    continue

                payload = {}
                try:
                    payload = json.loads(data)
                    if "messages" in payload:
                        messages = payload["messages"]
                    else:
                        messages.append({"role": "user", "content": data})
                except json.JSONDecodeError:
                    messages.append({"role": "user", "content": data})

                modalities = payload.get("modalities", ["text", "audio"])

                request_body = {
                    "model": MODEL_ID,
                    "messages": messages,
                    "stream": True,
                    "modalities": modalities,
                }

                async with httpx.AsyncClient(timeout=300) as client:
                    async with client.stream(
                        "POST",
                        f"{VLLM_URL}/v1/chat/completions",
                        json=request_body,
                    ) as resp:
                        if resp.status_code != 200:
                            err = await resp.aread()
                            await websocket.send_text(
                                json.dumps({"event": "error", "detail": f"vLLM {resp.status_code}: {err.decode()}"})
                            )
                            continue

                        full_text = ""
                        audio_started = False

                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            chunk = line[6:]
                            if chunk == "[DONE]":
                                break

                            try:
                                parsed = json.loads(chunk)
                            except json.JSONDecodeError:
                                continue

                            modality = parsed.get("modality", "text")
                            choices = parsed.get("choices", [])
                            if not choices:
                                continue

                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")

                            if modality == "text" and content:
                                full_text += content
                                await websocket.send_text(content)

                            elif modality == "audio" and content:
                                if not audio_started:
                                    await websocket.send_text(json.dumps({"event": "audio_start"}))
                                    audio_started = True
                                try:
                                    wav_bytes = base64.b64decode(content)
                                    await websocket.send_bytes(wav_bytes)
                                except Exception:
                                    pass

                        if audio_started:
                            await websocket.send_text(json.dumps({"event": "audio_end"}))

                        await websocket.send_text(json.dumps({"event": "turn_end"}))
                        messages.append({"role": "assistant", "content": full_text or "[audio response]"})

            elif message["type"] in ("websocket.disconnect", "websocket.close"):
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[ws] error: {e}", flush=True)
        try:
            await websocket.send_text(json.dumps({"event": "error", "detail": str(e)}))
        except Exception:
            pass


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        start_vllm()
        wait_for_vllm()
        print("Starting WebSocket server on port 8080...", flush=True)
        uvicorn.run(app, host="0.0.0.0", port=8080)
    else:
        print("Usage: python app.py serve")
        sys.exit(1)


if __name__ == "__main__":
    main()
