# Qwen Image Edit 2511 ComfyUI One-Click

Qwen-Image-Edit-2511 running in ComfyUI: instruction-based image editing with strong identity consistency, multi-person fusion and up to three reference images. Weights are **Apache 2.0** and published ungated by Qwen, and packaged for ComfyUI by Comfy-Org, so there is no access agreement, no token to configure, and no licence barrier to commercial use.

Container: **`ghcr.io/acdevmedia/qwenedit-comfyui:2511`**, with an immutable `2511-sha-<commit>` tag per build. Model revisions, checksums and workflow defaults live under `versions/2511/`. Everything runs on ComfyUI's **native** Qwen-Image-Edit support — no custom nodes.

## Start on Runpod

1. Create or update the template with `python3 scripts/create-runpod-template.py`, or `--dry-run` to review the payload first. It only calls the Runpod API; it builds nothing and downloads no weights.
2. Launch on a **48 GB** GPU with a **200 GB container disk** and no persistent volume. The resident set is about 31 GB (a 20.5 GB fp8 transformer, a 9.4 GB fp8 text encoder, the VAE and the Lightning LoRA), leaving headroom for activations. A 24 GB card is not enough.
3. Open **Connect → HTTP 8188 / ComfyUI** once the service reports Ready. First boot downloads the pinned weights into `/workspace/ComfyUI/models`.
4. Pick a workflow in the sidebar, load an image, describe the edit, press Queue.

No Hugging Face token is needed. Storage is temporary and no network volume is attached. First-boot downloads resume, your workflow edits persist across restarts, and no weights or credentials are baked into the image.

## This is an editing model

Qwen-Image-Edit **requires an input image**. It has no text-to-image mode, so there is no text-to-image workflow here. To generate from text alone, use the Z-Image, FLUX or Ideogram packages and bring the result here to edit.

Describe the *change*, not the whole picture: "Change the background to a rainy street and keep the person exactly as they are." Reference images by number — "the woman from image 1", "the jacket in image 2".

## Workflows

| Workflow | Images | Steps | CFG |
| --- | --- | --- | --- |
| **01 Lightning Edit** (default) | 1 | 4 | 1.0 |
| **02 Lightning Edit Multi Image** | up to 3 | 4 | 1.0 |
| **03 Standard Edit** | 1 | 40 | 4.0 |
| **04 Standard Edit Multi Image** | up to 3 | 40 | 4.0 |
| **10 Advanced user recipe** | up to 3 | 4 | 1.0 |

**Lightning** applies the distilled 4-step LoRA at strength 1.0 and is the sensible default: roughly ten times fewer steps, with CFG 1.0 so no second forward pass. **Standard** is the base model on the published reference settings — 40 steps and true CFG 4.0 — for when you want the model's own full sampling. It is far slower: on an A40 at 512 × 512 it took about 127 s for one image and 325 s with three inputs, against 22 s for Lightning. Prefer Lightning, and use an L40S for standard. `MODEL_MODE` selects which to download; the two share every weight except the 0.85 GB LoRA.

The multi-image workflows take one to three pictures; leave the extra loaders empty or unconnected for fewer. Each input is scaled to a total of about **1 megapixel** before encoding, which is the resolution the model works at, and the output follows the first image's proportions.

**10 Advanced user recipe** is the hand-tuned graph this package was built from, kept verbatim as a reference.

## Settings that matter

- **Sampler** `euler` / `simple`, `denoise` 1.0, with `ModelSamplingAuraFlow` shift **3.1** and `CFGNorm` strength 1.0. These match the upstream templates.
- **Text encoder** loads with `CLIPLoader` type `qwen_image`.
- **Megapixels** on each `ImageScaleToTotalPixels` node sets working resolution. Raise it for more detail at a higher memory cost; 1.0 is the default.
- **Negative prompt** is empty for Lightning, where CFG 1.0 makes it inert, and a single space for Standard, as on the model card.

## Seeds

The seed widget carries ComfyUI's standard **control after generate**, set to `randomize` in every packaged workflow. Set `fixed` to reproduce an edit exactly.

## Image preview ribbon

A strip of recent output images sits along the bottom of the window and refreshes as each queued graph finishes. Click a thumbnail to open the viewer: arrow keys move through the batch, **space** picks, **D** downloads, **Escape** closes. **Download picked** saves only the chosen files.

## Environment variables

- `HF_HOME=/workspace/.cache/huggingface`: Hugging Face cache and metadata location.
- `MODEL_MODE=lightning`: which variant to download — `lightning`, `standard` or `both`. About 31 GB either way; the variants differ by a 0.85 GB LoRA.
- `STUDIO_VERSION=2511`: which generation this image serves, baked at build time from `versions/2511/profile.json`.
- `PORT=8000`: gateway port for the Runpod Hub/Serverless listing. The Pod template does not expose it; Pod users reach ComfyUI directly on 8188.
- `PORT_HEALTH=8001`: readiness service for the Hub listing; `/ping` returns 503 until ComfyUI reports device information.
- `PUBLIC_KEY`: optional SSH key for diagnostics. When set, the container starts SSH on 2222; the template does not expose that port.

`RUNPOD_API_KEY` and `GITHUB_PACKAGES_PAT` are local deployment credentials only and must never reach the worker container.

## Build, validate and update

All container builds and runtime tests run in **GitHub Actions**, never on a local workstation. Pushing to `develop` or `main` builds, runs source and template-parity checks, verifies every packaged graph against a CPU-only ComfyUI, and publishes the image.

Paid GPU tests are opt-in through the `gpu_smoke` dispatch input. When set, Actions launches a disposable 48 GB Pod from that exact image digest. Because every graph here is edit-only, the harness uploads a synthetic source picture, renders each workflow at 512 × 512, and checks dimensions, pixel variance, entropy, flatness and that the output genuinely differs from the input. Those checks catch blank, flat and passthrough output, not artistic quality.

`scripts/build-workflows.py` regenerates the packaged workflows, in API and UI form, from a single specification, so the two cannot drift. `scripts/test-runpod.py` also runs by hand: `--keep` leaves the Pod up, `--pod <id>` re-runs against a running Pod with randomised seeds, and `--cleanup` deletes it. `docs/VALIDATION.md` holds the current record.

## Troubleshooting

- **Connect opens ComfyUI with HTTP 403:** ComfyUI's browser-origin guard rejects cross-site page navigations, and a link clicked from the Runpod dashboard counts as cross-site. This image patches the guard at build time to permit only a safe top-level `GET /` navigation. On a Pod built from an older digest, paste `https://<pod-id>-8188.proxy.runpod.net` into a blank tab instead.
- **ComfyUI does not become ready:** first boot downloads about 31 GB before ComfyUI starts. Check the Pod logs.
- **The edit ignores part of the prompt or changes too much:** describe the change and say what to keep, and refer to inputs by number. Lightning left untouched what it was told to keep in testing, whereas standard sometimes elaborated on it, drawing a neck and shoulders onto a head-shaped circle when told to "keep the person". Say exactly what must not change.
- **Out of GPU memory:** use a 48 GB card.

## Attribution

Model: [Qwen/Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511), Apache 2.0, packaged for ComfyUI by [Comfy-Org](https://huggingface.co/Comfy-Org/Qwen-Image-Edit). Lightning LoRA: [lightx2v/Qwen-Image-Edit-2511-Lightning](https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning).
