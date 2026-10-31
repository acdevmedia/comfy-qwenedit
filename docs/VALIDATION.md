# Validation status — Qwen Image Edit 2511

## GPU generation — NVIDIA A40 48 GB

All four packaged graphs executed on a disposable A40 Pod (`$0.59/hr`) from image digest
`sha256:eab9e55f7ceafff30da41f3d55759ed296c0b519c46d996c6ceb8a0b768d0368`, built from commit `3a1a872`. The
Pod downloaded both variants (about 31 GB), rendered at 512 × 512 with seed 42, and was deleted automatically.
The run cost about $0.15.

| Workflow | Elapsed | Entropy |
| --- | --- | --- |
| 01 Lightning Edit | 22.36 s | 8.21 |
| 02 Lightning Edit, multi image | 22.08 s | 8.20 |
| 03 Standard Edit | 126.57 s | 8.39 |
| 04 Standard Edit, multi image | 325.24 s | 8.22 |

Elapsed times include model loading when a variant first runs. The A40 is Ampere and has no native FP8 compute,
yet the `fp8mixed` transformer loaded and ran, which was the main open risk going in.

Edit-only graphs have nothing to generate a source from, so the harness uploads a synthetic 512 × 512 picture: a
colour gradient with a tan circle and a red bar. The multi-image graphs received that same picture in all three
slots. The prompt was "Change the background to a sunny beach and keep the person exactly as they are."

## What the images show

The PNGs were inspected rather than trusted to the numeric checks.

- **Lightning (both graphs):** the background is replaced by a convincing sunny beach, with turquoise sea, palms,
  sand and blue sky, and the circle and the bar are preserved essentially pixel-for-pixel. This is the edit that was
  asked for.
- **Standard (both graphs):** the same beach, but the model read the circle as a person's head. The single-image
  run added a neck and shoulders, and the multi-image run drew legs and shoes beneath it. That follows from the
  prompt's word "person" and a cartoon source, so it says little about real photographs, but it does show standard
  elaborating where Lightning held back.

## Not validated

- **Real photographs and faces.** The only source used was a synthetic shape picture. Identity preservation, which is
  the headline feature of 2511, has not been exercised, and neither has editing text in an image.
- **Genuinely different inputs.** The three multi-image slots held the same picture, so combining distinct people or
  objects across inputs is untested.
- **Resolution.** Everything ran at 512 × 512 for cost. The packaged default scales inputs to about one megapixel,
  which is roughly four times the pixels and noticeably slower, especially for standard.
- **Other GPUs.** Only an A40 has been run.
- **Content filtering.** A single benign prompt was run, which says nothing about borderline prompts.

## How a first attempt would have failed

The pinned SHA256 values were initially wrong: they had been read from the `ETag` of a redirected request and held
the CDN's value rather than the file's hash, so the container would have crash-looped on a checksum mismatch, as
Z-Image's first attempt did. `scripts/verify-pins.py` now asks Hugging Face for the authoritative hash and size and
runs in CI before each build, so this run used verified pins.

## What the automated checks do and do not cover

The harness asserts dimensions, pixel variance, entropy and flatness, and that an edit genuinely differs from its
source. It does not judge whether the requested edit was actually made, prompt adherence or artefacts: a corrupted
render with heavy texture raises entropy and passes. Inspect the uploaded PNGs.
