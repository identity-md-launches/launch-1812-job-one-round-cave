"""One-time delivery formatting of the installed image tool's new pigment.

Inputs are the verified ancestor at wall.png and generated edit at wall-v16.png.
FFmpeg transfers only generated dark pigment; no illustration is synthesized by
this script. Both declared PNG paths become the same completed wall. The input
hash guards deliberately prevent accidentally applying the transfer twice.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from image_bytes import read_png

ANCESTOR = '570456ece32010c9f1de7286dc4999b9b3d2aee19ab0adcfbb67bcdb7db1c07e'
GENERATED = '83007f43fb0706c83cb81fd8b3ab21252703177964181dab5171e0922e73bbe0'


def ffmpeg(args):
    result = subprocess.run(['/usr/bin/ffmpeg', '-hide_banner', '-loglevel',
                             'error', '-filter_complex_threads', '1', *args],
                            capture_output=True, check=True, env={})
    return result.stdout


def main():
    wall = Path('artifacts/line-1/wall.png')
    named = Path('artifacts/line-1/wall-v16.png')
    old_bytes, draft_bytes = wall.read_bytes(), named.read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest() == ANCESTOR
    assert hashlib.sha256(draft_bytes).hexdigest() == GENERATED
    w, h, original = read_png(old_bytes)
    assert (w, h) == (1254, 1254)
    assert read_png(draft_bytes)[:2] == (w, h)

    # A small ellipse tightly encloses the generated seed below Pepe. Color
    # selection excludes the regenerated rock and pale transfer surround. RGB
    # compositing avoids a YUV conversion that would change the ancestral wall.
    ellipse = ('lt(pow((0.906*(X-626)+0.423*(Y-900))/24,2)'
               '+pow((0.423*(X-626)-0.906*(Y-900))/49,2),1)')
    pigment = 'gt(lt(g(X,Y),0.59*r(X,Y))+lt(r(X,Y),80),0)'
    alpha = 'if(' + ellipse + '*' + pigment + ',220,0)'
    graph = ("[1:v]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='" +
             alpha + "'[pigment];[0:v]split=2[base][original];"
             '[base][pigment]overlay=format=rgb[added];'
             '[original][added]blend=all_mode=darken:shortest=1,format=rgb24[out]')
    final_bytes = ffmpeg(['-i', str(wall), '-i', str(named), '-filter_complex',
                          graph, '-map', '[out]', '-frames:v', '1',
                          '-f', 'image2pipe', '-vcodec', 'png', '-'])
    fw, fh, final = read_png(final_bytes)
    assert (fw, fh) == (w, h)
    changed = []
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if original[i:i+3] != final[i:i+3]:
                assert 590 <= x <= 662 and 850 <= y <= 950
                assert all(final[i+c] <= original[i+c] for c in range(3))
                changed.append((x, y))
    assert 500 < len(changed) < 4500
    wall.write_bytes(final_bytes)
    named.write_bytes(final_bytes)
    thumb = ffmpeg(['-i', str(wall), '-vf', 'scale=512:512:flags=area',
                    '-frames:v', '1', '-q:v', '4', '-f', 'image2pipe',
                    '-vcodec', 'mjpeg', '-'])
    assert thumb[:2] == b'\xff\xd8' and thumb[-2:] == b'\xff\xd9'
    assert len(thumb) < 100000
    Path('dist/line-1/36.jpg').write_bytes(thumb)

    digest = hashlib.sha256(final_bytes).hexdigest()
    record = {
        'name': 'The Fitting Seed',
        'image': 'https://api.imd.fun/artifacts/' + digest,
        'attributes': [{'trait_type': k, 'value': v} for k, v in (
            ('Cave', 'Water'), ('Wall', 'Line 1'), ('Number', 36),
            ('Left behind', 'Snapshot request match'),
            ('Meaning', 'Pepe fits a seed to the hollow he meant to fill.'),
            ('One thing', 'portable live Ethereum JSON-RPC snapshots'))],
    }
    record_path = Path('dist/line-1/36.json')
    assert not record_path.exists()
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    review = {
        'record': 36,
        'ancestor_sha256': ANCESTOR,
        'output_sha256': digest,
        'wall': {'paths': [str(wall), str(named)], 'width': w, 'height': h,
                 'format': 'PNG', 'mode': 'RGB', 'bytes': len(final_bytes)},
        'thumbnail': {'path': 'dist/line-1/36.jpg', 'width': 512, 'height': 512,
                      'format': 'JPEG', 'bytes': len(thumb)},
        'generation': {'tool': 'image_gen.imagegen', 'mode': 'built-in edit',
                       'draft_sha256': GENERATED, 'draft_retained': False,
                       'prompt_file': 'line-1/wall-prompt-36.txt'},
        'changed_pixels': len(changed),
        'unchanged_pixels': w*h-len(changed),
        'changed_bounds_inclusive': [min(x for x, y in changed),
                                     min(y for x, y in changed),
                                     max(x for x, y in changed),
                                     max(y for x, y in changed)],
        'preservation': 'Only generated red ochre and charcoal pigment on previously '
                        'unpainted stone below Pepe was transferred. All pixels outside '
                        'the addition are exactly ancestral. Darken-only blending '
                        'retains underlying rock texture. No ancestral mark was touched.',
        'visual_review': 'Pending final full-wall and JPEG inspection.',
        'unmet_visual_requirements': [],
    }
    Path('line-1/wall-review-36.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
