import numpy as np, sys
sys.path.insert(0,'.')
from digitize_common import *

def runs_at(img,x,ytop,ybot,hmask,thr=150):
    rs=column_runs(img,x,ytop,ybot,thr)
    return [r[0] for r in rs if r[1]<=6 and int(round(r[0])) not in hmask]

def track(img,X,Y,xstart,starts,xlo,xhi,ytop,ybot,vgrid,hgrid,gate=3.5):
    """Multi-curve nearest-neighbour tracking with linear prediction. starts: list of start pixel y."""
    hmask=set(expand(hgrid,1)); vmask=set(expand(vgrid,1))
    out=[]
    for y0 in starts:
        pts={}
        for direction in (1,-1):
            hist=[(xstart,y0)]
            x=xstart
            while xlo<=x+direction<=xhi:
                x+=direction
                if x in vmask: continue
                if len(hist)>=2:
                    (xa,ya),(xb,yb)=hist[-2],hist[-1]
                    pred=yb+(yb-ya)/(xb-xa)*(x-xb) if xb!=xa else yb
                else:
                    pred=hist[-1][1]
                rs=runs_at(img,x,ytop,ybot,hmask)
                if rs:
                    c=min(rs,key=lambda r:abs(r-pred))
                    if abs(c-pred)<=gate:
                        hist.append((x,c)); pts[x]=c; continue
                # coast
                hist.append((x,pred))
            pts[xstart]=y0
        xs=np.array(sorted(pts)); ys=np.array([pts[k] for k in xs])
        out.append((X.val(xs),Y.val(ys)))
    return out

def runs_listing(img,X,Y,x,ytop,ybot,hgrid):
    return [round(Y.val(r),3) for r in runs_at(img,x,ytop,ybot,set(expand(hgrid,1)))]
