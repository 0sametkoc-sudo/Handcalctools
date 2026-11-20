import sys
from PIL import Image, ImageDraw
sys.path.insert(0,'.')
from digitize_common import Axis
def zoomgrid(src,out,X,Y,xr,yr,dx,dy,z=4):
    im=Image.open(src).convert('RGB')
    x0,x1=sorted([int(X.pix(xr[0]))-8,int(X.pix(xr[1]))+8]); y0,y1=sorted([int(Y.pix(yr[0])),int(Y.pix(yr[1]))]); y0-=8; y1+=8
    c=im.crop((x0,y0,x1,y1)).resize(((x1-x0)*z,(y1-y0)*z),Image.LANCZOS)
    d=ImageDraw.Draw(c)
    v=xr[0]
    while v<=xr[1]+1e-9:
        px=(X.pix(v)-x0)*z; d.line([(px,0),(px,c.height)],fill=(0,200,255)); d.text((px+2,2),f"{v:.2f}",fill=(0,120,255)); v+=dx
    v=yr[0]
    while v<=yr[1]+1e-9:
        py=(Y.pix(v)-y0)*z; d.line([(0,py),(c.width,py)],fill=(255,150,0)); d.text((2,py-11),f"{v:.2f}",fill=(220,80,0)); v+=dy
    c.save(out)
