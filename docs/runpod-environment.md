# Runpod template environment

Synced to account template **Qwen Image Edit 2511 ComfyUI One-Click** (`r1fg429s5w`) on 2026-10-30.

[Open template](https://console.runpod.io/deploy?template=r1fg429s5w)

Image: `ghcr.io/acdevmedia/qwenedit-comfyui:2511`. Container disk: **200 GB**. Workspace: `/workspace`. Template service: `8188/http` (ComfyUI). The gateway port 8000 is used by the Hub/Serverless listing only and is not exposed by the Pod template. No persistent volume is requested; `volumeInGb` is 0 and storage is temporary.

`config/runpod-template.json` holds the Pod defaults. `.runpod/template-source.json` records the account source. `.runpod/hub.json` exposes the same values through Hub inputs or fixed values. `.runpod/tests.json` uses the same defaults for readiness tests. `.runpod/test_template_sync.py` fails if any of those files, this document or the README drift apart.

## Credentials

**None required.** The weights are published ungated under Apache 2.0, so first boot downloads them anonymously. Supplying `HF_TOKEN` is optional and only helps with Hugging Face rate limits.

## Template variables

### `HF_HOME`

Default: `/workspace/.cache/huggingface`.

Hugging Face cache and metadata directory on container storage.

### `MODEL_MODE`

Default: `lightning`.

Which variant to download: `lightning` (the 4-step distilled LoRA on the base model), `standard` (the base model alone, 40 steps) or `both`. The variants share every weight except the 0.85 GB LoRA, so each is about 31 GB.

### `STUDIO_VERSION`

Default: `2511`.

Which model generation this image serves, matching `versions/2511/`. It is baked at build time and selects the weights downloaded on first boot and the workflows installed.

### `PORT`

Default: `8000`.

Gateway HTTP and WebSocket port served by `.runpod/handler.py`. ComfyUI itself stays on 8188.

### `PORT_HEALTH`

Default: `8001`.

Readiness port. `/ping` returns 503 until ComfyUI reports device information, then 200.

## Hub additions and differences

The Pod template and the Hub listing build from the same Dockerfile and defaults. The Hub listing runs the readiness test in `.runpod/tests.json`; that establishes the service starts and answers, not that output quality is acceptable.

## Account template metadata

Visibility: public. No custom entrypoint or start command is set. SSH starts inside the container only when `PUBLIC_KEY` is supplied, and the template does not expose port 2222.
