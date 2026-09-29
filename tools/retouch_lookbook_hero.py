#!/usr/bin/env python3
"""Hero version of the Rezet lookbook cover without the cover typography.

Removes "LOOKBOOK AUTUMN WINTER 2025", "REZET STORE" and the address from
assets/images/rezet-lookbook-01.jpg (the original is never modified) and writes
assets/images/rezet-lookbook-01-hero.jpg, used only in the home page hero.
The case page keeps the original cover.

Usage (from the project root; needs numpy and opencv-python-headless):
    python3 tools/retouch_lookbook_hero.py
Then run tools/optimize_media.py and tools/build_site.py.
"""
import cv2, numpy as np
src=cv2.imread('assets/images/rezet-lookbook-01.jpg')
img=src.astype(np.float32)
H,W=src.shape[:2]
b,g,r=[src[:,:,i].astype(int) for i in range(3)]
white=(r>150)&(g>150)&(b>140)&((np.maximum(np.maximum(r,g),b)-np.minimum(np.minimum(r,g),b))<55)
# text boxes; background boxes get a generous mask (their surroundings are plain backdrop)
boxes_bg=[(50,28,215,72),(50,492,292,570),(488,492,590,570),(635,978,790,1022)]
box_fabric=(292,492,488,570)
mask=np.zeros((H,W),np.uint8)
for (x0,y0,x1,y1) in boxes_bg:
    m=np.zeros((H,W),np.uint8); m[y0:y1,x0:x1][white[y0:y1,x0:x1]]=1
    mask|=cv2.dilate(m,np.ones((9,9),np.uint8))
x0,y0,x1,y1=box_fabric
m=np.zeros((H,W),np.uint8); m[y0:y1,x0:x1][white[y0:y1,x0:x1]]=1
mask|=cv2.dilate(m,np.ones((5,5),np.uint8))
out=cv2.inpaint(src,mask*255,7,cv2.INPAINT_TELEA).astype(np.float32)
rng=np.random.default_rng(11)
def grain(sd,blur=0.7):
    n=cv2.GaussianBlur(rng.normal(0,1,(H,W)).astype(np.float32),(0,0),blur); n*=sd/float(n.std())
    return np.repeat(n[...,None],3,axis=2)
def hf_sd(patch,blur=2.2):
    return float((patch-cv2.GaussianBlur(patch,(0,0),blur)).mean(axis=2).std())
Y0,Y1,D=492,570,74
# 1) pleats: band copied from just below, feathered
X0,X1=298,428
band=img[Y0+D:Y1+D, X0:X1]
f=16
alpha=np.ones((Y1-Y0,1,1),np.float32); alpha[:f,0,0]=np.linspace(0,1,f); alpha[-f:,0,0]=np.linspace(1,0,f)
reg=cv2.GaussianBlur(cv2.dilate(mask,np.ones((17,17),np.uint8))[Y0:Y1,X0:X1].astype(np.float32),(0,0),3)[...,None]
xa=np.ones((1,X1-X0,1),np.float32); xa[0,-10:,0]=np.linspace(1,0,10)
a=np.clip(alpha*np.clip(reg*1.6,0,1)*xa,0,1)
out[Y0:Y1,X0:X1]=a*band+(1-a)*out[Y0:Y1,X0:X1]
# 2) diagonal panel: smooth fill + fabric grain, kept 4px inside the fabric edge
flap=np.zeros((H,W),np.uint8)
cv2.fillPoly(flap,[np.array([[420,Y0],[488,Y0],[537,Y1],[420,Y1]],np.int32)],1)
sel=((mask>0)&(flap>0)).astype(np.float32)
# the panel is neutral grey wool: build the fill from clean fabric colour, not from the olive backdrop
ref=img[578:606,500:528].reshape(-1,3)
ref_col=ref.mean(axis=0)
lum=cv2.GaussianBlur(out,(0,0),4).mean(axis=2)
m=(mask>0)&(flap>0)
lum_adj=(lum-lum[m].mean())*0.35                 # keep a little of the natural light falloff
cand=np.empty_like(out)
for ch in range(3):
    cand[...,ch]=ref_col[ch]+lum_adj
cand=cand+grain(hf_sd(img[578:606,500:528]))
soft=cv2.GaussianBlur(sel,(0,0),1.0)[...,None]
out=soft*cand+(1-soft)*out
# 3) backdrop: match the photo's own grain inside the filled letters
bgsel=((mask>0)&(flap==0)).astype(np.float32)
bgsel[Y0:Y1,X0:X1]=0
bsd=hf_sd(img[100:160,60:220],1.2)
soft=cv2.GaussianBlur(bgsel,(0,0),1.2)[...,None]
out=out+soft*grain(bsd,0.6)
out=np.clip(out,0,255).astype(np.uint8)
cv2.imwrite('assets/images/rezet-lookbook-01-hero.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 94])
print('wrote assets/images/rezet-lookbook-01-hero.jpg')
