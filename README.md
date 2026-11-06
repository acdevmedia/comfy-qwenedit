# Qwen Image Edit 2511 ComfyUI One-Click

[![Runpod](https://api.runpod.io/badge/acdevmedia/comfy-qwenedit)](https://console.runpod.io/hub/listing/acdevmedia/comfy-qwenedit)

Qwen-Image-Edit-2511 running in ComfyUI: instruction-based image editing with strong identity consistency, multi-person fusion and up to three reference images. Weights are **Apache 2.0** and published ungated by Qwen, and packaged for ComfyUI by Comfy-Org, so there is no access agreement, no mandatory token, and no licence barrier to commercial use.

Container: **`ghcr.io/acdevmedia/qwenedit-comfyui:2511`**, with an immutable `2511-sha-<commit>` tag per build. Model revisions, checksums and workflow defaults live under `versions/2511/`. Everything runs on ComfyUI's **native** Qwen-Image-Edit support — no custom nodes.

## Start on Runpod

1. Create or update the template with `python3 scripts/create-runpod-template.py`, or `--dry-run` to review the payload first. It only calls the Runpod API; it builds nothing and downloads no weights.
2. Launch on a **48 GB** GPU with a **200 GB container disk** and no persistent volume. The resident set is about 31 GB (a 20.5 GB fp8 transformer, a 9.4 GB fp8 text encoder, the VAE and the Lightning LoRA), leaving headroom for activations. A 24 GB card is not enough.
3. Open **Connect → HTTP 8188 / ComfyUI** once the service reports Ready. First boot downloads the pinned weights into `/workspace/ComfyUI/models`.
4. Pick a workflow in the sidebar, load an image, describe the edit, press Queue.

For authenticated downloads, create Runpod Secret `HUGGINGFACE_TOKEN` with your Hugging Face read token; the template maps it to `HF_TOKEN`. The weights are ungated, so you can remove the mapping to download anonymously. Storage is temporary and no network volume is attached. First-boot downloads resume, your workflow edits persist across restarts, and no weights or credentials are baked into the image.

## This is an editing model

Qwen-Image-Edit **requires an input image**. It has no text-to-image mode, so there is no text-to-image workflow here. To generate from text alone, use the Z-Image, FLUX or Ideogram packages and bring the result here to edit.

Describe the *change*, not the whole picture: "Change the background to a rainy street and keep the person exactly as they are." Reference images by number — "the woman from image 1", "the jacket in image 2".

## Workflows

| Workflow | Images | Steps | CFG |
| --- | --- | --- | --- |
| **01 Lightning Edit** (default) | 1 | 8 | 1.0 |
| **02 Lightning Edit Multi Image** | up to 3 | 8 | 1.0 |
| **03 Standard Edit** | 1 | 40 | 3.5 |
| **04 Standard Edit Multi Image** | up to 3 | 40 | 3.5 |
| **10 Advanced user recipe** | up to 3 | 4 | 1.0 |

**Lightning** applies the **8-step** distilled LoRA at strength 1.0 and is the default. It runs at **8 steps with guidance off (cfg 1)**, which is how LightX2V publishes and configures that LoRA. It is not trained for higher cfg, and raising it brings on washed-out or colour-cast images. At cfg 1 ComfyUI skips the negative prompt altogether, so the packaged negative only takes effect if you raise cfg.

**Standard** is the base model at the model card's **40 steps** with cfg **3.5**, and its negative prompt is fully active. It takes about five times as long and is the better choice for big changes such as a new location or time of day.

**Larger edits ask more of the prompt.** Say what changes and what stays, and describe the light, not just the place: "Change the location to a golf course at 9pm, under a dark night sky with floodlights over the fairway. Relight the person to match the night scene. Keep their face, pose, clothing and full body exactly as they are." Alibaba's own examples follow the same shape: name what to preserve, then the change, then the direction and quality of the light. Try a few seeds, and use Standard if Lightning falls short.

The multi-image workflows take one to three pictures; leave the extra loaders empty or unconnected for fewer. Every input is used whole. The encoder sizes each reference itself to about **1 megapixel**, keeping its proportions, and the output takes the first image's shape at the area set by **Render Width** and **Render Height** (1024 × 1024 by default, the same area the encoder uses), in multiples of 32. A head-to-toe portrait stays head to toe.

**10 Advanced user recipe** is the hand-tuned graph this package was built from, kept verbatim as a reference: it uses the 4-step LoRA at cfg 1 and still centre-crops to Render Width and Height, so use 01 to 04 for portrait images.

## Settings that matter

- **Sampler** `euler` / `simple`, `denoise` 1.0, with `ModelSamplingAuraFlow` shift **3.1** and `CFGNorm` strength 1.0. These match the upstream templates.
- **Text encoder** loads with `CLIPLoader` type `qwen_image`.
- **Render Width and Render Height** set the working area. Raise them for more detail at a higher memory cost, though the model is built around 1 megapixel.
- **Negative prompt** opens with Qwen's published negative in Chinese, the encoder's native language, and adds the failures edits are prone to: missing limbs, pasted-on subjects, washed-out or pastel colour, mismatched light. Both variants carry it; only cfg above 1 uses it, so it is active on Standard.
- **Reference method** needs no extra node: the pinned 2511 weights carry ComfyUI's `index_timestep_zero` marker, so the method is selected automatically.

## Seeds

The seed widget carries ComfyUI's standard **control after generate**, set to `randomize` in every packaged workflow. Set `fixed` to reproduce an edit exactly.

## Image preview ribbon

A strip of recent output images sits along the bottom of the window and refreshes as each queued graph finishes. Click a thumbnail to open the viewer: arrow keys move through the batch, **space** picks, **D** downloads, **Escape** closes. **Download picked** saves only the chosen files.

## Optional LoRAs

Both sit on the canvas in every packaged workflow except 10, at strength 0.

- **Camera angles** ([Multiple Angles](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA), Apache 2.0): set strength to 1 and write the prompt as `<sks> [azimuth] [elevation] [distance]`, for example `<sks> right side view low-angle shot close-up`. It covers 96 camera positions.
- **Realism** ([Anything2Real](https://huggingface.co/lrzjason/Anything2Real_2601), Apache 2.0): turns stylised images photographic; try strength 0.75 to 1. Leave it off for ordinary edits of photographs.

Standard also has a bypassed **Draft mode** node (EasyCache): select it and press Ctrl+B for quicker, softer drafts while working out a shot.

These are pinned and downloaded at first boot, never baked into the image. At strength 0 ComfyUI skips a LoRA entirely, so it costs nothing while it is off.

## Speed

ComfyUI starts with SageAttention and `--highvram`, so models stay on the 48 GB GPU between runs. Each boot tests Sage on the assigned GPU and falls back to PyTorch attention if the check fails; set `COMFYUI_ATTENTION=pytorch` to force that. Attention that needs a mask runs on PyTorch either way. First-boot downloads use Hugging Face's high-performance Xet mode.

## Browse and download outputs

**Connect → HTTP 3923 / Copyparty** opens a gallery of everything in `/workspace/ComfyUI/output`, newest first. Sign in with the values of Runpod Secrets `COPYPARTY_USERNAME` and `COPYPARTY_SECRET`. Select files to download them, or a whole folder as a ZIP. It is read-only: nothing can be uploaded, changed or deleted, and if either secret is missing it stays off without affecting ComfyUI. The log is `/workspace/logs/copyparty.log`.

`zip`, `unzip` and `aws` are on the path in the terminal for moving outputs off the Pod yourself.

## Environment variables

- `HF_TOKEN`: `{{ RUNPOD_SECRET_HUGGINGFACE_TOKEN }}`; optional read token for authenticated Hugging Face downloads.
- `COPYPARTY_USERNAME`: `{{ RUNPOD_SECRET_COPYPARTY_USERNAME }}`; login for the file browser on port 3923.
- `COPYPARTY_PASSWORD`: `{{ RUNPOD_SECRET_COPYPARTY_SECRET }}`; its password. The browser stays off without both.
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

## CPU thread sizing

CPU thread pools are sized automatically to the container CPU quota and available CPUs before PyTorch starts, avoiding host-sized pools that can throttle image scaling and export. Set `OMP_NUM_THREADS` and optionally `MKL_NUM_THREADS` to override; startup logs show the selected values. Actual speedup depends on the workload and has not been benchmarked for this revision.

## Editable render size

Set **Render Width** and **Render Height** on the canvas, or **Width** and **Height** in the main controls panel. These fields drive generation directly; resolution presets no longer override them. The added image-resize controls use a center crop to the selected dimensions; change the resize node’s crop setting if needed. Use dimensions supported by the model (multiples of 32 for LTX video, 16 for image workflows). LTX’s two-stage workflows retain their internal half-resolution first pass and upscale to the selected output size. Existing installed workflows and user edits are preserved; open a newly packaged workflow to get these controls.
