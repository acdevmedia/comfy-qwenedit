# Runpod deployment

Use the repository [README](../README.md) for setup. Publish `ghcr.io/acdevmedia/qwenedit-comfyui:2511` through GitHub Actions, then run `python3 scripts/create-runpod-template.py` to create or update the Qwen Image Edit template. Use `--dry-run` to review its payload. The script matches the single account template by recorded id, then by name; the other packages' templates are not touched.
