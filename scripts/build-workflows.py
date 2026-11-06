"""Regenerate the packaged Qwen Image Edit 2511 workflows (API and UI forms) from one spec."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import workflow_graph as g
from workflow_dimensions import apply_dimensions, fit_frame_to_image, sync_api

ROOT = Path(__file__).resolve().parents[1]
UNET = 'qwen_image_edit_2511_fp8mixed.safetensors'
CLIP = 'qwen_2.5_vl_7b_fp8_scaled.safetensors'
VAE = 'qwen_image_vae.safetensors'
LORA = 'Qwen-Image-Edit-2511-Lightning-8steps-V1.0-bf16.safetensors'
# Optional looks, always present and off at strength 0, where ComfyUI skips them entirely.
ANGLES = 'qwen-image-edit-2511-multiple-angles-lora.safetensors'
REAL = 'anything2real_2601.safetensors'

# Qwen's published negative (the Qwen-Image model card, in the encoder's native Chinese), followed by the
# failures an edit is prone to: bodies losing limbs, subjects pasted over a scene, and washed-out colour.
NEGATIVE = (
    '低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。'
    ' low resolution, low quality, blurry, out of focus, jpeg artifacts, noise, grid pattern, banding, watermark, text overlay,'
    ' washed out, faded, pastel colours, milky haze, colour cast, oversaturated, flat lighting, painting, watercolour,'
    ' illustration, cartoon, 3d render, airbrushed, plastic skin, waxy skin, deformed body, distorted proportions,'
    ' missing limbs, missing body parts, cut off body, cropped body, partial body, extra limbs, malformed hands,'
    ' extra fingers, disfigured face, changed face, different person, pasted on subject, cutout edges, halo around subject,'
    ' floating subject, mismatched lighting, inconsistent shadows, wrong time of day, unchanged background')

# Each variant follows its publisher. Lightning is the 8-step distilled LoRA at 8 steps with guidance off,
# LightX2V's own configuration: it was not trained for cfg, and raising it brings on the colour cast
# recorded in docs/VALIDATION.md. At cfg 1 ComfyUI skips the negative, so it only applies if cfg is raised.
# Standard is the base model at the card's 40 steps, with guidance at 3.5 and the negative in full.
VARIANTS = {
    'LIGHTNING': dict(lora=True, steps=8, cfg=1.0, prefix='QwenEdit/lightning'),
    'STANDARD': dict(lora=False, steps=40, cfg=3.5, prefix='QwenEdit/standard'),
}
PROMPT = ('Change the location to a golf course at 9pm, under a dark night sky with floodlights over the fairway. '
          'Relight the person to match the night scene. Keep their face, pose, clothing and full body exactly as they are.')


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
    s += [('30', 'LoraLoaderModelOnly', {'model': model, 'lora_name': ANGLES, 'strength_model': 0.0}, [ANGLES, 0.0], (380, 180)),
          ('31', 'LoraLoaderModelOnly', {'model': ['30', 0], 'lora_name': REAL, 'strength_model': 0.0}, [REAL, 0.0], (380, 320))]
    s += [('5', 'ModelSamplingAuraFlow', {'model': ['31', 0], 'shift': 3.1}, [3.1], (720, 40)),
          ('6', 'CFGNorm', {'model': ['5', 0], 'strength': 1.0}, [1.0, False], (1060, 40))]
    loads = []
    for n in range(images):
        load = str(10 + n * 2)
        s += [(load, 'LoadImage', {'image': 'upload_your_image_%d.png' % (n + 1)},
               ['upload_your_image_%d.png' % (n + 1), 'image'], (40, 480 + n * 330))]
        loads.append(load)
    # The encoder resizes every reference itself, keeping its proportions; only the frame needs sizing.
    s += [('11', 'ImageScaleToTotalPixels',
           {'image': [loads[0], 0], 'upscale_method': 'lanczos', 'megapixels': 1.0, 'resolution_steps': 1},
           ['lanczos', 1.0], (380, 480))]

    def encode(nid, text, pos):
        ins = {'clip': ['2', 0], 'prompt': text, 'vae': ['3', 0]}
        for n, load in enumerate(loads):
            ins['image%d' % (n + 1)] = [load, 0]
        return (nid, 'TextEncodeQwenImageEditPlus', ins, [text], pos)

    s += [encode('7', PROMPT, (720, 200)), encode('8', NEGATIVE, (720, 480)),
          ('9', 'VAEEncode', {'pixels': ['11', 0], 'vae': ['3', 0]}, [], (1060, 340)),
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
        # A frame of about 1024 x 1024 in area is the size the encoder gives its references.
        apply_dimensions(ui, (1024, 1024))
        sync_api(api,ui)
        fit_frame_to_image(api, ui, 32)
        g.check(api, ui)
        titles = {30: 'Camera angles LoRA: strength 1 and a <sks> prompt', 31: 'Realism LoRA: try strength 0.75 to 1'}
        for node in ui['nodes']:
            if node['id'] in titles:
                node['title'] = titles[node['id']]
        if variant == 'STANDARD':
            g.add_draft_cache(ui, 6, 20)
        name = '%s_%s_%s.json' % (num, variant, label)
        g.dump(ROOT / 'versions/2511/api' / name, api)
        g.dump(ROOT / 'versions/2511/workflows' / name, ui)
        print('built', name, '(%d nodes, %d links)' % (len(api), len(ui['links'])))


if __name__ == '__main__':
    main()
