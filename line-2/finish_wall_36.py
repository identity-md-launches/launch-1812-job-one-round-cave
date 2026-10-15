"""Preserve ancestor bytes outside a small transfer of generated earth pigment."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

base=Path('artifacts/line-2/wall.png')
output=Path('artifacts/line-2/wall-v16.png')
ancestor,draft=base.read_bytes(),output.read_bytes()
assert hashlib.sha256(ancestor).hexdigest()=='9861188938312f536643c91efabd1737759cb5574e0b7cbfb7b6a218723e0f27'
w,h,old=read_png(ancestor)
dw,dh,generated=read_png(draft)
assert (w,h)==(dw,dh)==(1254,1254)
x0,y0,width,height=760,445,120,75
cx,cy,cw,ch=850,521,145,94
final=bytearray(old)
changed=0
for y in range(y0,y0+height):
    for x in range(x0,x0+width):
        i=(y*w+x)*3
        rock=old[i:i+3]
        sx,sy=cx+(x-x0)*cw//width,cy+(y-y0)*ch//height
        j=(sy*dw+sx)*3
        r,g,b=generated[j:j+3]
        # Confine extraction to the new loop; omit the ancestor's diagonal stick.
        if ((sx-922)/71)**2+((sy-565)/43)**2>1 or max(rock)<85 or (x*19+y*31)%23==0:
            continue
        charcoal=max(r,g,b)<106
        ochre=r>1.4*g and 45<g<110 and b<86
        chalk=(sx-922)**2+(sy-559)**2<9**2 and r>165 and g>140 and b>95
        if charcoal or ochre or chalk:
            pigment=(42,30,20) if charcoal else ((197,180,139) if chalk else (143,64,30))
            alpha=.68 if charcoal else .60
            for c in range(3):
                final[i+c]=round(rock[c]*(1-alpha)+pigment[c]*alpha)
            changed+=final[i:i+3]!=old[i:i+3]
assert 300<changed<width*height
for y in range(h):
    for x in range(w):
        i=(y*w+x)*3
        if final[i:i+3]!=old[i:i+3]:
            assert x0<=x<x0+width and y0<=y<y0+height
            assert max(old[i:i+3])>=85
encoded=png(w,h,final)
base.write_bytes(encoded)
output.write_bytes(encoded)
preview=jpeg(512,512,resize(w,h,final),52)
assert len(preview)<100000
Path('dist/line-2/36.jpg').write_bytes(preview)
review={'number':36,'ancestor_sha256':hashlib.sha256(ancestor).hexdigest(),
        'sha256':hashlib.sha256(encoded).hexdigest(),
        'wall':{'paths':[str(base),str(output)],'width':w,'height':h,'format':'PNG','mode':'RGB','bytes':len(encoded)},
        'preview':{'path':'dist/line-2/36.jpg','width':512,'height':512,'format':'JPEG','bytes':len(preview)},
        'addition_region':{'x':x0,'y':y0,'width':width,'height':height},
        'changed_pixels':changed,'unchanged_pixels':w*h-changed,
        'outside_region_pixel_identical':True,'dark_cracks_preserved':True,
        'generation_tool':'mcp__image__edit_image','draft_sha256':hashlib.sha256(draft).hexdigest(),
        'generated_dimensions':[dw,dh],'draft_retained_in_workspace':False,
        'generation_prompt':'Preserve inherited cave and all marks; add two small red ochre pebbles in a crooked charcoal loop with a chalk dot between them on vacant stone, worn earth pigments, no new hands or writing.',
        'visual_review':'pending inspection','unmet_visual_requirements':[]}
Path('line-2/wall-review-36.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps(review,indent=2))
