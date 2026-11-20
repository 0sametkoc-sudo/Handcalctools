import numpy as np, sys
sys.path.insert(0,'.')
from digitize_common import *
SRC='source/'

def thick_runs(img,x,ytop,ybot,minlen=3,thr=120):
    return [r for r in column_runs(img,x,ytop,ybot,thr) if r[1]>=minlen]

def fig9_2():
    img=load(SRC+'afsam_fig9_2_page.png')
    X=Axis(518,0.4,863.5,2.4); Y=Axis(372.5,2.0,717,1.0)
    vgrid=expand([518,535,551,587,621,656,690,725,760,795,829,863],2)
    px,py=[],[]
    for x in range(520,862):
        if x in vgrid: continue
        rs=thick_runs(img,x,368,700)
        rs=[r for r in rs if r[1]<40]
        if rs:
            r=max(rs,key=lambda r:r[1]); px.append(x); py.append(r[0])
    return X.val(np.array(px)), Y.val(np.array(py)), X, Y

def fig9_8():
    img=load(SRC+'afsam_fig9_8_page.png')
    X=Axis(478.5,0.0,903.5,1.6); Y=Axis(752,0.0,542,1.6)
    vgrid=expand([478,531,586,639,691,744,798,852,903],2)
    up,lo=([],[]),([],[])
    for x in range(481,880):
        if x in vgrid: continue
        rs=[r for r in thick_runs(img,x,545,750) if r[1]<30]
        if not rs: continue
        if len(rs)==1:
            for t in (up,lo): t[0].append(x); t[1].append(rs[0][0])
        else:
            rs=sorted(rs,key=lambda r:r[0])
            up[0].append(x); up[1].append(rs[0][0]); lo[0].append(x); lo[1].append(rs[-1][0])
    f=lambda t:(X.val(np.array(t[0])),Y.val(np.array(t[1])))
    return f(up),f(lo),X,Y

if __name__=='__main__':
    x,y,X,Y=fig9_2(); print('9-2', len(x), x.min(), x.max())
    for v in (0.5,1.0,1.25,1.5,2.0,2.35): print(v, round(float(np.interp(v,x,y)),3))
    overlay(SRC+'afsam_fig9_2_page.png','/tmp/ov92.png',[('K',x,y)],X,Y,crop=(470,350,900,740))
    (xu,yu),(xl,yl),X,Y=fig9_8(); print('9-8',len(xu), xu.min(),xu.max())
    for v in (0.1,0.4,0.8,1.0,1.2,1.4,1.5): print(v, round(float(np.interp(v,xu,yu)),3), round(float(np.interp(v,xl,yl)),3))
    overlay(SRC+'afsam_fig9_8_page.png','/tmp/ov98.png',[('u',xu,yu),('y',xl,yl)],X,Y,crop=(440,520,920,780))
