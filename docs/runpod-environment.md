# Runpod template environment

Synced to account template **Qwen Image Edit 2511 ComfyUI One-Click** (`r1fg429s5w`) on 2026-10-30.

[Open template](https://console.runpod.io/deploy?template=r1fg429s5w)

Image: `ghcr.io/acdevmedia/qwenedit-comfyui:2511`. Container disk: **200 GB**. Workspace: `/workspace`. Template service: `8188/http` (ComfyUI) and `3923/http` (copyparty). The gateway port 8000 is used by the Hub/Serverless listing only and is not exposed by the Pod template. No persistent volume is requested; `volumeInGb` is 0 and storage is temporary.

`config/runpod-template.json` holds the Pod defaults. `.runpod/template-source.json` records the account source. `.runpod/hub.json` exposes the same values through Hub inputs or fixed values. `.runpod/tests.json` uses the same defaults for readiness tests. `.runpod/test_template_sync.py` fails if any of those files, this document or the README drift apart.

## Credentials

The file browser on port 3923 signs in with Runpod Secrets `COPYPARTY_USERNAME` and `COPYPARTY_SECRET`, which the template maps to `COPYPARTY_USERNAME` and `COPYPARTY_PASSWORD`.

The template maps Runpod Secret `HUGGINGFACE_TOKEN` to `HF_TOKEN` for authenticated downloads and higher rate limits. Create that secret with a Hugging Face read token. The weights remain ungated: users without a token can remove the mapping and download anonymously. No credential values are stored in the repository or image.

## Template variables

### `COPYPARTY_USERNAME`

Default: `{{ RUNPOD_SECRET_COPYPARTY_USERNAME }}`.

Username for the output file browser on port 3923, from Runpod Secret `COPYPARTY_USERNAME`.

### `COPYPARTY_PASSWORD`

Default: `{{ RUNPOD_SECRET_COPYPARTY_SECRET }}`.

Password for the output file browser, from Runpod Secret `COPYPARTY_SECRET`. Without both values the file browser does not start; ComfyUI is unaffected.

### `HF_TOKEN`

Default: `{{ RUNPOD_SECRET_HUGGINGFACE_TOKEN }}`.

Optional Hugging Face read token from Runpod Secret `HUGGINGFACE_TOKEN`. Remove the mapping to use anonymous downloads.

### `HF_HOME`

Default: `/workspace/.cache/huggingface`.

Hugging Face cache and metadata directory on container storage.

### `MODEL_MODE`

Default: `lightning`.

Which variant to download: `lightning` (the distilled LoRAs on the base model), `standard` (the base model alone, 40 steps) or `both`. The variants share every weight except the 0.85 GB LoRA, so each is about 31 GB.

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
