"""Retain only image editor pigment for mark 36; keep the ancestor pixel exact elsewhere."""
import hashlib
import json
from pathlib import Path

from image_bytes import jpeg, png, read_png, resize

OLD_SHA = '6dcaa1836e970d214039ab5e6fb8b3c096f1ac75b8c3e4e9defe8dcb62564032'


def main():
    folder = Path('artifacts/line-4')
    ancestor = (folder/'wall.png').read_bytes()
    draft = (folder/'wall-v16.png').read_bytes()
    assert hashlib.sha256(ancestor).hexdigest() == OLD_SHA
    w, h, old = read_png(ancestor)
    dw, dh, generated = read_png(draft)
    assert (w, h, dw, dh) == (1254, 1254, 1254, 1254)
    final = bytearray(old)
    for y in range(65, 146):
        for x in range(934, 1063):
            i = (y*w+x)*3
            original = old[i:i+3]
            r, g, b = generated[i:i+3]
            if sum(original) < 70:  # Keep deep fissures exactly.
                continue
            red_zone = (934 <= x <= 1001 and 69 <= y <= 139) or (1014 <= x <= 1062 and 65 <= y <= 127)
            red = (red_zone and 60 < r < 205 and r > 1.48*g and r-g > 36 and
                   r > original[0] + 4 and r-g > original[0]-original[1]+14)
            bridge = 984 <= x <= 1023 and 94 <= y <= 114
            white = bridge and min(r,g,b) > 90 and max(r,g,b)-min(r,g,b) < 50 and sum((r,g,b)) > sum(original)+50
            charcoal = bridge and r < 83 and sum((r,g,b)) < sum(original)-28
            if red:
                target = [round(a*.22+p*.78) for a,p in zip(original,(r,g,b))]
            elif white:
                target = [round(a*.25+p*.75) for a,p in zip(original,(r,g,b))]
            elif charcoal:
                target = [round(a*.50) for a in original]
            else:
                continue
            final[i:i+3] = bytes(target)
    changes = []
    for i in range(0, len(old), 3):
        if old[i:i+3] != final[i:i+3]:
            y, x = divmod(i//3, w)
            assert 934 <= x < 1063 and 65 <= y < 146 and sum(old[i:i+3]) >= 70
            changes.append((x,y))
    assert 1000 < len(changes) < 5000
    wall = png(w,h,final)
    sha = hashlib.sha256(wall).hexdigest()
    preview = jpeg(512,512,resize(w,h,final),52)
    assert len(preview) < 100_000
    for name in ('wall.png','wall-v16.png'):
        (folder/name).write_bytes(wall)
    Path('dist/line-4/36.jpg').write_bytes(preview)
    review = {
        'wall': {'paths': ['artifacts/line-4/wall.png','artifacts/line-4/wall-v16.png'],
                 'width':w,'height':h,'format':'PNG','mode':'RGB','bytes':len(wall),'sha256':sha},
        'preview': {'path':'dist/line-4/36.jpg','width':512,'height':512,'format':'JPEG',
                    'bytes':len(preview),'sha256':hashlib.sha256(preview).hexdigest()},
        'ancestorSha256': OLD_SHA, 'generatedDraftSha256':hashlib.sha256(draft).hexdigest(),
        'imageTool':'Built-in imagegen; generation 01a13dfd-947f-7e13-bd34-f563cbe6d6fb',
        'prompt':'Preserve the inherited cave, Pepe and all marks. Add only two small hollow red ochre pebbles joined by charcoal and a chalk fleck on vacant upper-right rock. Earth pigments, no new hands or writing.',
        'changedPixels':len(changes),'unchangedPixels':w*h-len(changes),
        'additionBoundsExclusive':[min(x for x,y in changes),min(y for x,y in changes),
                                   max(x for x,y in changes)+1,max(y for x,y in changes)+1],
        'preservation':'Only selected generated pigment transferred on vacant rock; every pixel outside addition is the exact ancestor. Deep old cracks are protected.',
        'visualReview':'Pending full PNG and JPEG inspection.', 'unmetVisualRequirements':[],
        'limitations':['Local visual review is not independent certification.',
                       'The mark is intentionally small in the 512-pixel preview.',
                       'The generated draft changed other rock; the preservation pass excludes it.']}
    Path('line-4/wall-review-36.json').write_text(json.dumps(review,indent=2)+'\n')
    record = {'name':'The Witnessed Source','image':'https://api.imd.fun/artifacts/'+sha,
              'attributes':[
                  {'trait_type':'Cave','value':'Water'},
                  {'trait_type':'Wall','value':'Line 4'},
                  {'trait_type':'Number','value':36},
                  {'trait_type':'Left behind','value':'offline EIP-712 source-witness binder'},
                  {'trait_type':'Meaning','value':'Pepe joins the source stone to its witnessed trace before trusting their shared mark.'},
                  {'trait_type':'One thing','value':'offline EIP-712 typed-data digest checking'}]}
    Path('dist/line-4/36.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
