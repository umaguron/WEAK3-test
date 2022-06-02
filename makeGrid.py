from import_pytough_modules import *
from mulgrids import *
from t2data import *
import os 
import math
import _readConfig
import shutil

#######
## get argument
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("inputIni", 
        help="fullpath of toughInput setting input.ini", type=str)
parser.add_argument("-f","--force_overwrite", 
        help="overwrite existing mulgrid and t2data file", action='store_true')
parser.add_argument("-p","--showsProfile", 
        help="if given, show grid profile", action='store_true')
args = parser.parse_args()
## get directory name where this script is located
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
## read inputIni ##
_rii = _readConfig.InputIni().read_from_inifile(args.inputIni)
II = _rii._readInputIniToughInput()
# create save dir. 
try:
    os.makedirs(_rii.t2FileDirFp, exist_ok=True) if args.force_overwrite \
    else os.makedirs(_rii.t2FileDirFp)
except FileExistsError:
    print(f"directory: {_rii.t2FileDirFp} exists")
    print(f"    add option -f to force overwrite")
    sys.exit()
######

if os.path.isfile(_rii.mulgridFileFp) and not args.force_overwrite:
    sys.exit(f"mulgrid file : {_rii.mulgridFileFp} exists")

## create grid ##
# new t2data object
dat = t2data()
dat.filename = _rii.t2GridFp
dat.title = II['problemName']

def printBlockInfo(list, comment):
    print(comment)
    for i in list:
        print(f"{i:>9.2f}")

geo = None
if _rii.atmosphere.includesAtmos: 
    print("SINGLE ATMOS")
    atmos_type = 0
else: 
    print("NO ATMOS")
    atmos_type = 2

if _rii.mesh.isRadial:
    # radial
    print(f"gridtype: radial")
    rblocks = _rii.mesh.rblocks
    zblocks = _rii.mesh.zblocks
    printBlockInfo(rblocks,"[rBLOCKS]")
    printBlockInfo(zblocks,"[zBLOCKS]")
    # [radial origin(starting radius), 
    #  vertical origin (position of the top layer)]
    origin = [0, 0]
    dat.grid = t2grid().radial(rblocks, zblocks, 
                convention=_rii.mesh.convention, 
                atmos_type=0, origin=origin) 
    # create mulgrid object separately.
    # this 'pseudo' mulgrid is used only for visualization.
    geo = mulgrid().rectangular(rblocks, [1], zblocks, 
                                convention=_rii.mesh.convention, atmos_type = atmos_type)
else:
    # rectangular
    print(f"gridtype: rectangular")
    xblocks = _rii.mesh.xblocks
    yblocks = _rii.mesh.yblocks
    zblocks = _rii.mesh.zblocks
    printBlockInfo(xblocks,"[xBLOCKS]")
    printBlockInfo(yblocks,"[yBLOCKS]")
    printBlockInfo(zblocks,"[zBLOCKS]")
    geo = mulgrid().rectangular(xblocks, yblocks, zblocks, 
                                convention=_rii.mesh.convention, atmos_type = atmos_type)
    dat.grid = t2grid().fromgeo(geo)
    

## ROCKS ##
for secRock in _rii.rockSecList:
    permeability = [secRock.permeability_x,
                    secRock.permeability_y,
                    secRock.permeability_z]
    rock = rocktype(name = secRock.name, nad = secRock.nad, 
            density = secRock.density, 
            porosity = secRock.porosity, permeability = permeability, 
            conductivity = secRock.conductivity, 
            specific_heat = secRock.specific_heat)
    if secRock.nad >= 2:
        rock.relative_permeability = {'parameters':secRock.RP, 'type':secRock.IRP}
        rock.capillarity = {'parameters':secRock.CP, 'type':secRock.ICP}
    # set rocktype to grid
    dat.grid.add_rocktype(rock)

    for secReg in secRock.regionSecList:
        # apply rock type to the region
        count = 0
        for blk in dat.grid.blocklist:
            if not blk.atmosphere:
                if secReg.xmin <= blk.centre[0] < secReg.xmax \
                    and secReg.ymin <= blk.centre[1] < secReg.ymax \
                    and secReg.zmin <= blk.centre[2] < secReg.zmax :
                    blk.rocktype = rock
                    count += 1
        print(f"ROCK: {secRock.secName}\tREGION: {secReg.secName}\tnCELLS: {count}")

# set atomosphere
if _rii.atmosphere.includesAtmos:
    dat.grid.add_rocktype(_rii.atmosphere.atmos)
    # set to grid
    for blk in dat.grid.blocklist:
        if blk.atmosphere:
            blk.rocktype = _rii.atmosphere.atmos


# TOPは時間不変に設定するならnegativeにする
# set air layer
geo.atmosphere_volume = 1e50
geo.atmosphere_connection = 1e-9

if args.showsProfile:
    geo.slice_plot(line=90, block_names=False, rocktypes=dat.grid)
    geo.slice_plot(line=0, block_names=True, rocktypes=dat.grid)
    geo.layer_plot(None, column_names=True)

# save mulgrid object
geo.write(_rii.mulgridFileFp)
# write tough input file
dat.write(_rii.t2GridFp)

try: 
    shutil.copy2(args.inputIni, _rii.t2FileDirFp)
except shutil.SameFileError:
    pass

