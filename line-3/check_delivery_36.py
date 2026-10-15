"""Check round 36 delivery bytes, record schema, goal and allowed changes."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from image_bytes import read_png


def main():
    root = Path(__file__).resolve().parent.parent
    wall = root/'artifacts/line-3/wall-v16.png'
    raw = wall.read_bytes()
    w, h, pixels = read_png(raw)
    assert (w, h) == (1254, 1254)
    assert raw == (root/'artifacts/line-3/wall.png').read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    rec = json.loads((root/'dist/line-3/36.json').read_text())
    assert set(rec) == {'name', 'image', 'attributes'}
    assert rec['image'] == 'https://api.imd.fun/artifacts/'+sha
    traits = rec['attributes']
    assert all(set(t) == {'trait_type', 'value'} for t in traits)
    assert [t['trait_type'] for t in traits] == ['Cave','Wall','Number','Left behind','Meaning','One thing']
    assert [t['value'] for t in traits[:4]] == ['Water','Line 3',36,'settlement-gap']
    assert type(traits[2]['value']) is int
    preview = (root/'dist/line-3/36.jpg').read_bytes()
    assert preview[:2] == b'\xff\xd8' and preview[-2:] == b'\xff\xd9'
    at, dimensions = 2, None
    while at < len(preview):
        assert preview[at] == 255
        marker = preview[at+1]
        size = int.from_bytes(preview[at+2:at+4], 'big')
        if marker == 192:
            bits, jh, jw, channels = struct.unpack('>BHHB', preview[at+4:at+10])
            assert bits == 8 and channels == 3
            dimensions = (jw, jh)
            break
        at += size+2
    assert dimensions == (512,512) and len(preview) <= 100000
    review = json.loads((root/'line-3/wall-review-36.json').read_text())
    assert review['wallSha256'] == sha and review['unmetVisualRequirements'] == []
    assert review['changedPixels'] == 785 and review['allPixelsOutsideAdditionUnchanged']
    assert review['reviewStatus'] == 'Final PNG and decoded JPEG visually inspected'
    goal = subprocess.check_output(['git','show','HEAD:line-3/GOAL.md'],cwd=root)
    assert (root/'line-3/GOAL.md').read_bytes() == goal
    changed = subprocess.check_output(['git','diff','--name-only'],cwd=root,text=True).splitlines()
    assert changed == ['line-3/USED.md'], changed
    new = subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=root,text=True).splitlines()
    assert all(n.startswith(('line-3/','dist/line-3/','artifacts/line-3/','test/scratch/')) for n in new)
    assert not subprocess.check_output(['git','ls-files','artifacts/line-3/wall-v16.png'],cwd=root)
    for name in changed + new:
        path = root/name
        if not name.startswith(('artifacts/','test/scratch/')):
            assert path.stat().st_size <= 100000, name
    assert len(list((root/'dist/line-3').glob('*.json'))) == 36
    result = {'passed':True,'wallDimensions':[w,h],'wallFormat':'PNG','wallSha256':sha,
              'previewDimensions':list(dimensions),'previewFormat':'JPEG','previewBytes':len(preview),
              'goalUnchanged':True,'oldRecordsUnchanged':True,'scopeCheckPassed':True,
              'requiredOutputUntracked':True,'unmetVisualRequirements':[]}
    (root/'line-3/delivery-check-36.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
