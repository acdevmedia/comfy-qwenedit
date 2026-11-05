# Qwen Image Edit 2511 ComfyUI One-Click

See the [repository README](https://github.com/acdevmedia/comfy-qwenedit#readme) for the variants, workflows and environment settings. This is an editing model and needs an input image. The weights are Apache 2.0 and ungated, so **no Hugging Face token or access agreement is needed**. Hub uses the same Dockerfile and defaults as the Pod template. Use one active worker for stateful browser sessions.

The default configuration maps Runpod Secret `HUGGINGFACE_TOKEN` to `HF_TOKEN` for higher download rate limits. Create that secret with a read token, or remove the mapping for anonymous downloads.
