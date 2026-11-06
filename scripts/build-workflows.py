"""Regenerate the packaged Qwen Image Edit 2511 workflows (API and UI forms) from one spec."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import workflow_graph as g
from workflow_dimensions import apply_dimensions, sync_api

ROOT = Path(__file__).resolve().parents[1]
UNET = 'qwen_image_edit_2511_fp8mixed.safetensors'
CLIP = 'qwen_2.5_vl_7b_fp8_scaled.safetensors'
VAE = 'qwen_image_vae.safetensors'
LORA = 'Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors'

# Reference settings: Lightning is the 4-step distilled LoRA at cfg 1; standard is the base model
# at the 40 steps and true-CFG 4.0 published on the model card, with its single-space negative.
# Lightning is the distilled LoRA run at 8 steps and cfg 4, which hands-on testing found follows an edit
# instruction (removing a phone from a photo, for instance) where the LoRA's nominal 4 steps at cfg 1 did
# not; the larger changes (a new person, a new location, a new camera angle) still land less reliably.
# Standard is the base model at the 40 steps and true-CFG 4.0 published on the model card, with its
# single-space negative.
VARIANTS = {
    'LIGHTNING': dict(lora=True, steps=8, cfg=4.0, negative='', prefix='QwenEdit/lightning'),
    'STANDARD': dict(lora=False, steps=40, cfg=4.0, negative=' ', prefix='QwenEdit/standard'),
}
PROMPT = 'Change the background to a sunny beach and keep the person exactly as they are.'


def spec(variant, images):
    v = VARIANTS[variant]
    s = [('1', 'UNETLoader', {'unet_name': UNET, 'weight_dtype': 'default'}, [UNET, 'default'], (40, 40)),
         ('2', 'CLIPLoader', {'clip_name': CLIP, 'type': 'qwen_image', 'device': 'default'},
          [CLIP, 'qwen_image', 'default'], (40, 200)),
         ('3', 'VAELoader', {'vae_name': VAE}, [VAE], (40, 340))]
    model = ['1', 0]
    if v['lora']:
        s.append(('4', 'LoraLoaderModelOnly', {'model': model, 'lora_name': LORA, 'strength_model': 1.0},
                  [LORA, 1.0], (380, 40)))
        model = ['4', 0]
    s += [('5', 'ModelSamplingAuraFlow', {'model': model, 'shift': 3.1}, [3.1], (720, 40)),
          ('6', 'CFGNorm', {'model': ['5', 0], 'strength': 1.0}, [1.0, False], (1060, 40))]
    scaled = []
    for n in range(images):
        load, scale = str(10 + n * 2), str(11 + n * 2)
        s += [(load, 'LoadImage', {'image': 'upload_your_image_%d.png' % (n + 1)},
               ['upload_your_image_%d.png' % (n + 1), 'image'], (40, 480 + n * 330)),
              (scale, 'ImageScaleToTotalPixels',
               {'image': [load, 0], 'upscale_method': 'lanczos', 'megapixels': 1.0, 'resolution_steps': 1},
               ['lanczos', 1.0], (380, 480 + n * 330))]
        scaled.append(scale)

    def encode(nid, text, pos):
        ins = {'clip': ['2', 0], 'prompt': text, 'vae': ['3', 0]}
        for n, sc in enumerate(scaled):
            ins['image%d' % (n + 1)] = [sc, 0]
        return (nid, 'TextEncodeQwenImageEditPlus', ins, [text], pos)

    s += [encode('7', PROMPT, (720, 200)), encode('8', v['negative'], (720, 480)),
          ('9', 'VAEEncode', {'pixels': [scaled[0], 0], 'vae': ['3', 0]}, [], (1060, 340)),
          ('20', 'KSampler', {'model': ['6', 0], 'positive': ['7', 0], 'negative': ['8', 0],
                              'latent_image': ['9', 0], 'seed': 0, 'steps': v['steps'], 'cfg': v['cfg'],
                              'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 1.0},
           [0, 'randomize', v['steps'], v['cfg'], 'euler', 'simple', 1.0], (1400, 200)),
          ('21', 'VAEDecode', {'samples': ['20', 0], 'vae': ['3', 0]}, [], (1740, 200)),
          ('22', 'SaveImage', {'images': ['21', 0], 'filename_prefix': v['prefix']}, [v['prefix']], (1900, 200))]
    return s


def main():
    plan = [('01', 'LIGHTNING', 1, 'Edit'), ('02', 'LIGHTNING', 3, 'Edit_Multi_Image'),
            ('03', 'STANDARD', 1, 'Edit'), ('04', 'STANDARD', 3, 'Edit_Multi_Image')]
    for num, variant, images, label in plan:
        api, ui = g.build(spec(variant, images))
        apply_dimensions(ui)
        sync_api(api,ui)
        g.check(api, ui)
        name = '%s_%s_%s.json' % (num, variant, label)
        g.dump(ROOT / 'versions/2511/api' / name, api)
        g.dump(ROOT / 'versions/2511/workflows' / name, ui)
        print('built', name, '(%d nodes, %d links)' % (len(api), len(ui['links'])))


if __name__ == '__main__':
    main()
