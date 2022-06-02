from import_pytough_modules import *
from t2data import *
import os 
import math
import numpy as np
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
import pandas as pd

# CENTER = (1000,0)
# INTBL = 150 # [m]
# ELL1 = (0, 0, 1500, 1500) # (x0, y0, a, b) a: xaxis, b:yaxis
# fact1 = 1.3
# fact2 = 1.7
CENTER = (1000,1)
INTBL = 150 # [m]
ELL1 = (0, 0, 2000, 2000) # (x0, y0, a, b) a: xaxis, b:yaxis
fact1 = 1.1
nroop1 = 14
fact2 = 1.1
nroop2 = 0

# partitioning_type = "hexa"
partitioning_type = "rect"
SAVE_DIR = "voronoigrid/"

"""
function util
"""
def isPointInInEllipse(point, ellipse):
    """
    point: list
        point[0]: x coordinate
        point[1]: y coordinate
    ellipse: list
        ellipse[0]: x0 (ellipse center)
        ellipse[1]: y0 (ellipse center)
        ellipse[2]: a (xaxis length of ellipse)
        ellipse[3]: b (yaxis length of ellipse)
    """
    ywidth = ellipse[3] * (1-(point[0]-ellipse[0])**2/ellipse[2]**2)**0.5
    ymin = ellipse[1]-ywidth
    ymax = ellipse[1]+ywidth
    if abs(point[0]-ellipse[0]) > ellipse[0]:
        return False
    elif ymin <= point[1]<= ymax:
        return True

ellipseHalfWidthY = lambda x, ellipse: \
                        ellipse[3] * (1-(x-ellipse[0])**2/ellipse[2]**2)**0.5
ellipseHalfWidthX = lambda y, ellipse: \
                        ellipse[2] * (1-(y-ellipse[1])**2/ellipse[3]**2)**0.5

def col_name(col_id, convention):
    if convention==0:
        if col_id > 27*26*26+26: raise Exception
        ret = int_to_chars(col_id)
        return f"{ret:3}"    
    elif convention==1:
        if col_id > 99: raise Exception
        ret = col_id
        return f"{ret:2}"    
    elif convention==2:
        if col_id > 999: raise Exception
        ret = col_id
        return f"{ret:3}"    
    else: raise Exception

def layer_name(layer_id, convention):
    if convention==0:
        if layer_id > 99: raise Exception
        ret = layer_id
        return f"{ret:2}"    
    elif convention==1:
        if layer_id > 27*26*26+26: raise Exception
        ret = int_to_chars(layer_id)
        return f"{ret:3}"    
    elif convention==2:
        if layer_id > 27*26: raise Exception
        ret = int_to_chars(layer_id)
        return f"{ret:2}"    
    else: raise Exception

def elem_name(layer_id, col_id, convention):
    if convention==0:
        return col_name(col_id,convention)+layer_name(layer_id,convention)
    if convention==1 or convention==2:
        return layer_name(layer_id,convention)+col_name(col_id,convention)

def resistivity2porosity(rho):
    return 0.1

def porosity2permeability(phi):
    return 1e-15

"""
create 2D Voronoi seed points
"""
seeds = []
if "hexa" in partitioning_type.lower():
    ## 六角形に分割する場合
    ## 楕円内部に含まれる正六面体のseedの座標を取得する。
    # NCELL for x+ direction
    for iy in range(-1*int(ELL1[3]//(INTBL*3**0.5/2)), 
                    int(ELL1[3]//(INTBL*3**0.5/2))+1):
        y1 = iy * INTBL*3**0.5/2
        if iy%2 == 0:
            residualx = \
                ellipseHalfWidthX(y1, ELL1)\
                - (ellipseHalfWidthX(y1, ELL1)//INTBL)*INTBL
            # 最も外側の点から楕円の円周までの距離が大きい場合は楕円の外側にも点を一つ追加する
            expanding = 1 if residualx > INTBL*3/4 else 0
            # case when center seed is on y axis of ellipse
            for ix in range(-1*int(ellipseHalfWidthX(y1, ELL1)//INTBL)-expanding, 
                            int(ellipseHalfWidthX(y1, ELL1)//INTBL)+1+expanding):
                seeds.append((ix*INTBL+ELL1[0]+CENTER[0], y1+CENTER[1]))
        else:
            residualx = \
                ellipseHalfWidthX(y1, ELL1)-INTBL/2 \
                - (((ellipseHalfWidthX(y1, ELL1)-INTBL/2)//INTBL)*INTBL)
            # 最も外側の点から楕円の円周までの距離が大きい場合は楕円の外側にも点を一つ追加する
            expanding = 1 if residualx > INTBL*2/3 else 0
            # case when no seeds are on y axis of ellipse
            # ~ 真ん中手前
            for ix in range(
                    -1*int((ellipseHalfWidthX(y1, ELL1)-INTBL/2) // INTBL)-expanding, 
                    0+1): 
                seeds.append((ix*INTBL+ELL1[0]-INTBL/2+CENTER[0], y1+CENTER[1]))
            # 真ん中 ~ 
            for ix in range(
                    0, 
                    int((ellipseHalfWidthX(y1, ELL1)-INTBL/2)//INTBL)+1+expanding): 
                seeds.append((ix*INTBL+ELL1[0]+INTBL/2+CENTER[0], y1+CENTER[1]))

elif "rect" in partitioning_type.lower():
    ## 正方形で分割する場合
    # NCELL for x+ direction
    for iy in range(-1*int(ELL1[3]//(INTBL)), int(ELL1[3]//(INTBL))+1):
        y1 = iy * INTBL
        residualx = \
            ellipseHalfWidthX(y1, ELL1) \
            - (ellipseHalfWidthX(y1, ELL1)//INTBL)*INTBL
        # 最も外側の点から楕円の円周までの距離が大きい場合は楕円の外側にも点を一つ追加する
        expanding = 1 if residualx > INTBL*3/4 else 0
        # case when center seed is on y axis of ellipse
        for ix in range(-1*int(ellipseHalfWidthX(y1, ELL1)//INTBL)-expanding, 
                        int(ellipseHalfWidthX(y1, ELL1)//INTBL)+1+expanding):
            seeds.append((ix*INTBL+ELL1[0]+CENTER[0], y1+CENTER[1]))
else:
    sys.exit()

"""
# 離心率
e = np.sqrt(max(ELL1[2],ELL1[3])**2 - min(ELL1[2],ELL1[3])**2) / ELL1[2]
from scipy.special import ellipe
# 楕円の弧長
L = 4*ELL1[2]*ellipe(e)
nSeedEll2 = L//(fact*INTBL)
"""
# 六面体領域より外側は,円周の周囲を等分割してseedを作る
# 円の外側に行くほどseedの間隔はfact倍ずつ大きくなる。
radius = max(ELL1[2],ELL1[3])
newIntbr = INTBL
NSEED = None
for i in range(1,nroop1+1):
    radius = radius+newIntbr
    enshu = 2*math.pi*radius
    if i==1:
        nSeed = int(enshu//newIntbr)
        NSEED = nSeed
    else:
        nSeed = NSEED
    intbrRad = 2*math.pi/nSeed
    print(f"""
    newintbr {newIntbr}
    radius {radius}
    nseed {nSeed}""")
    for s in range(nSeed):
        x = radius * math.sin(s*intbrRad) + CENTER[0]
        y = radius * math.cos(s*intbrRad) + CENTER[1]
        seeds.append((x,y))
    newIntbr = fact1*newIntbr
    
for i in range(nroop1+1,nroop1+nroop2+1):
    radius = radius+newIntbr
    enshu = 2*math.pi*radius
    nSeed = int(enshu//newIntbr)
    intbrRad = 2*math.pi/nSeed
    print(f"""
    newintbr {newIntbr}
    radius {radius}
    nseed {nSeed}""")
    for s in range(nSeed):
        x = radius * math.sin(s*intbrRad) + CENTER[0]
        y = radius * math.cos(s*intbrRad) + CENTER[1]
        seeds.append((x,y))
    newIntbr = fact2*newIntbr

print(f'{len(seeds)} seed points')

"""
save
"""
with open(os.path.join(SAVE_DIR, f"seedN{len(seeds)}_ib{INTBL}m_f1-{fact1}x{nroop1}_f2-{fact2}x{nroop2}"), "w") as f:
    f.write(f"         x          y\n")
    for seed in seeds:
        f.write(f"{seed[0]:10.3f} {seed[1]:10.3f}\n")


"""
test plot
"""
xxx = []
yyy = []
for seed in seeds:
    xxx.append(seed[0])
    yyy.append(seed[1])

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

fig = plt.figure()
ax = fig.add_subplot(1,1,1)
ax.scatter(xxx,yyy)
ellipse = Ellipse((ELL1[0]+CENTER[0], ELL1[1]+CENTER[1]), ELL1[2]*2, ELL1[3]*2, angle=0, alpha=0.3)
ax.add_artist(ellipse)
ax.set_title(f'{len(xxx)} seed points')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_aspect('equal')
ax.set_ylim([radius*(-1),radius])
ax.set_ylim([radius*(-1),radius])

plt.show()

