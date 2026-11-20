"""Digitize AFSAM Figure 9-3 (bearing efficiency factor K vs a/D for D/t curves)."""
import numpy as np, sys
sys.path.insert(0,'.')
from digitize_common import *
SRC='source/afsam_fig9_3_page.png'
X=Axis.grid([(448.5,0.4),(501.5,0.8),(556.5,1.2),(613,1.6),(668,2.0),(723,2.4),(778.5,2.8),(833.5,3.2),(890,3.6),(944.5,4.0)])
Y=Axis.grid([(467,0),(409,0.4),(355,0.8),(297.5,1.2),(240.5,1.6),(184,2.0),(128,2.4),(71,2.8),(16.5,3.2)])
VGRID=set(expand([448,449,501,502,556,557,613,668,723,778,779,833,834,890,944,945],1))
HGRID=set(list(range(14,19))+list(range(70,73))+list(range(126,130))+list(range(182,186))+list(range(239,243))
          +list(range(296,300))+list(range(353,357))+list(range(407,413))+list(range(465,470)))
EXCL=[(2.92,3.78,0.50,1.78),(0.45,1.85,1.88,3.3),(2.06,2.26,1.45,1.66),(2.06,2.26,1.0,1.2)]
DT=[2,3,4,5,6,7,8,9,10,15,20,25,30]
RIGHT={2:2.95,3:2.793,4:2.558,5:2.318,6:2.082,7:1.834,8:1.607,9:1.446,10:1.323,15:0.866,20:0.633,25:0.485,30:0.407}
MID={8:1.526,9:1.404,10:1.277,15:0.852,20:0.626,25:0.485,30:0.405}

def excluded(xv,yv):
    return any(a<=xv<=b and c<=yv<=d for a,b,c,d in EXCL)

def track(img,xv0,yv0,xv_end,gate=3.0,nfit=10):
    x0=int(round(float(X.pix(xv0)))); xe=int(round(float(X.pix(xv_end))))
    step=-1 if xe<x0 else 1
    hist=[(x0,float(Y.pix(yv0)))]; pts={x0:hist[0][1]}
    x=x0
    while x!=xe:
        x+=step
        if x in VGRID: continue
        xs=np.array([h[0] for h in hist[-nfit:]]); ys=np.array([h[1] for h in hist[-nfit:]])
        pred=np.polyval(np.polyfit(xs,ys,1),x) if len(xs)>=3 and np.ptp(xs)>0 else hist[-1][1]
        prev=hist[-1][1]
        gap=abs(x-hist[-1][0])
        g=gate+0.25*max(0,gap-2)
        xv=float(X.val(x))
        cands=[]
        for r in column_runs(img,x,18,466,140):
            yc=r[0]
            if r[1]>8 or int(round(yc)) in HGRID or excluded(xv,float(Y.val(yc))): continue
            if step<0 and yc<min(prev,pred)-1.0: continue
            if step>0 and yc>max(prev,pred)+1.0: continue
            cands.append(yc)
        if cands:
            c=min(cands,key=lambda r:abs(r-pred))
            if abs(c-pred)<=g:
                hist.append((x,c)); pts[x]=c
    xs=np.array(sorted(pts)); return X.val(xs), Y.val(np.array([pts[k] for k in xs]))

GRID=np.round(np.arange(0.5,4.0001,0.05),4)

def run():
    """Return {D/t: K values on GRID (a/D = 0.50 ... 4.00, step 0.05)}."""
    img=load(SRC)
    raw={}
    for d in DT:
        if d<=7:
            x,y=track(img,3.95,RIGHT[d],0.45)
            x=np.r_[x,4.0]; y=np.r_[y,RIGHT[d]]
        else:
            xl,yl=track(img,2.2,MID[d],0.45)
            if d==30:   # flat and hidden under the 0.4 grid line to the right of a/D = 2.2
                xr,yr=np.array([2.2]),np.array([MID[d]])
            else:
                xr,yr=track(img,2.2,MID[d],2.85)
            x=np.r_[xl,xr,3.95,4.0]; y=np.r_[yl,yr,RIGHT[d],RIGHT[d]]
        o=np.argsort(x); x,y=despike(x[o],y[o],win=6,tol=0.04)
        raw[d]=(x,y)
    env_x,env_y=raw[2]
    out={}
    for d in DT:
        x,y=raw[d]
        g=np.interp(GRID,x,y)
        env=np.interp(GRID,env_x,env_y)
        # left of the first tracked point the curve lies on the common envelope
        g=np.where(GRID<x.min(),env,g)
        out[d]=np.minimum(g,env)
    # near the common origin (a/D ~ 0.475) the curves fan out as straight lines; the scan cannot separate
    # them there, so below a/D = 0.65 each curve is a straight line from the origin to its a/D = 0.65 value
    i65=int(np.argmin(np.abs(GRID-0.65)))
    for d in DT:
        k65=out[d][i65]
        for i in range(i65):
            out[d][i]=max(0.0,k65*(GRID[i]-0.475)/(0.65-0.475))
    # curves may merge but not cross: K decreases with D/t
    for i in range(len(DT)-2,-1,-1):
        out[DT[i]]=np.maximum(out[DT[i]],out[DT[i+1]])
    # K is non-decreasing in a/D
    for d in DT:
        out[d]=np.maximum.accumulate(out[d])
    return out

if __name__=='__main__':
    c=run()
    overlay(SRC,'/tmp/ov93.png',[(str(d),GRID,c[d]) for d in DT],X,Y,crop=(400,0,990,480),dot=1.6)
    for d in DT:
        print(d,[round(float(np.interp(v,GRID,c[d])),3) for v in (0.6,0.8,1.0,1.2,1.5,2.0,2.5,3.0,3.5,4.0)])


# ---------------------------------------------------------------- cut-off curves A and B (dashed)
SEEDS_A=[(1.33,1.165),(1.38,1.20),(1.43,1.228),(1.48,1.264),(1.54,1.30),(1.62,1.35),(1.71,1.39),(1.80,1.44),(1.88,1.48),(1.95,1.51),(2.05,1.54),(2.08,1.545)]
SEEDS_B=[(1.33,1.06),(1.42,1.08),(1.55,1.095),(1.75,1.10),(1.95,1.105),(2.08,1.11)]


def snap(img,seeds,gate=2.0):
    sx=np.array([s[0] for s in seeds]); sy=np.array([s[1] for s in seeds])
    px,py=[],[]
    for x in range(int(X.pix(sx[0])),int(X.pix(sx[-1]))+1):
        if x in VGRID: continue
        xv=float(X.val(x)); pred=float(Y.pix(np.interp(xv,sx,sy)))
        rs=[r[0] for r in column_runs(img,x,150,330,140) if r[1]<=6 and int(round(r[0])) not in HGRID]
        if rs:
            c=min(rs,key=lambda r:abs(r-pred))
            if abs(c-pred)<=gate:
                px.append(xv); py.append(float(Y.val(c)))
    return np.array(px),np.array(py)


def cutoffs():
    """Cut-off curves A and B on GRID; NaN where the curve does not apply (left of its start).
    Right of the last drawn point (a/D ~ 2.1) the cut-off is held at its last value."""
    img=load(SRC)
    out={}
    for name,seeds in (("A",SEEDS_A),("B",SEEDS_B)):
        x,y=snap(img,seeds)
        x,y=despike(x,y,win=5,tol=0.03)
        # where no dash could be snapped (start of the curve), use the visually read seed points
        pre=[(a,b) for a,b in seeds if a<x.min()-0.01]
        if pre:
            x=np.r_[[a for a,b in pre],x]; y=np.r_[[b for a,b in pre],y]
        g=np.interp(GRID,x,y)
        g=np.where(GRID<x.min(),np.nan,g)
        out[name]=np.maximum.accumulate(np.nan_to_num(g,nan=0.0))
        out[name]=np.where(GRID<x.min(),np.nan,out[name])
        out[name+"_pts"]=(x,y)
    return out
