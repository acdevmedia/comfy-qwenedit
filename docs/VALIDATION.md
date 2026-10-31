# Validation status — Qwen Image Edit 2511

## Not yet validated on a GPU

This package has had no GPU run. Source checks, template parity, pinned-weight metadata and
weight-reference checks pass, and every packaged API graph is schema-checked against a CPU-only
ComfyUI during the image build, which catches unknown node types and missing required inputs.

None of that establishes that the model edits well, or at all. In particular, **the packaged
graphs were generated from the maintainer's tuned workflows and the upstream templates, not run**.
Two things in them have not been exercised: `qwen_image_edit_2511_fp8mixed` loading on an Ampere
card (A40, RTX A6000), which has no native FP8 compute, and the multi-image graphs with fewer than
three images connected.

Dispatch the build workflow with `gpu_smoke=true`, or run `scripts/test-runpod.py --keep`, and
record the result here before treating a revision as tested.

## What the automated checks do and do not cover

Edit-only graphs have nothing to generate a source picture from, so the harness uploads a
synthetic 512 × 512 image and checks that the output differs from it. Generation checks assert
dimensions, pixel variance, entropy and flatness, and reject passthrough output. They do not judge
whether the requested edit was actually made, prompt adherence or artefacts: a corrupted render
with heavy texture raises entropy and passes. Inspect the uploaded PNGs.
