from import_pytough_modules import *
#
from re import A
from mulgrids import *
from t2data import *
import os 
import _readConfig
from define import *
import makeGridAmeshVoro 
import shutil

def makeGrid(ini:_readConfig.InputIni, overWrites=False, showsProfiles=False):
    if ini.mesh.type == REGULAR:
        # 軽いので常に作り直す(overWrites=True)
        makeGridRegular(ini, overWrites=True, showsProfiles=showsProfiles)
    elif ini.mesh.type == AMESH_VORONOI:
        if os.path.exists(ini.mulgridFileFp) and not overWrites:
            return
        makeGridAmeshVoro.makePermVariableVoronoiGrid(ini, 
            force_overwrite_all=overWrites, open_viewer=showsProfiles)

def makeGridRegular(ini:_readConfig.InputIni, overWrites=False, showsProfiles=False):

    if ini.mesh.type == AMESH_VORONOI:
        sys.exit()

    #######

    ## read inputIni ##
    II = ini.toughInput
    ## define filepath
    mulgridFileFp = ini.mulgridFileFp
    t2FileDirFp = ini.t2FileDirFp
    t2FileFp = ini.t2FileFp
    t2GridFp = f"{t2FileFp}.grid"
    # create save dir. 
    os.makedirs(t2FileDirFp, exist_ok=True) 

    ######

    if os.path.isfile(t2GridFp) and not overWrites:
        sys.exit(f"t2Grid file : {t2GridFp} exists")

    ## create grid ##
    # new t2data object
    dat = t2data()
    dat.filename = t2GridFp
    dat.title = II['problemName']

    def printBlockInfo(list, comment):
        print(comment)
        for i in list:
            print(f"{i:>9.2f}")

    geo = None
    if ini.atmosphere.includesAtmos: 
        print("SINGLE ATMOS")
        atmos_type = 0
    else: 
        print("NO ATMOS")
        atmos_type = 2

    if ini.mesh.isRadial:
        # radial
        print(f"gridtype: radial")
        rblocks = ini.mesh.rblocks
        zblocks = ini.mesh.zblocks
        printBlockInfo(rblocks,"[rBLOCKS]")
        printBlockInfo(zblocks,"[zBLOCKS]")
        # [radial origin(starting radius), 
        #  vertical origin (position of the top layer)]
        origin = [0, 0]
        dat.grid = t2grid().radial(rblocks, zblocks, 
                    convention=ini.mesh.convention, 
                    atmos_type=0, origin=origin) 
        # create mulgrid object separately.
        # this 'pseudo' mulgrid is used only for visualization.
        geo = mulgrid().rectangular(rblocks, [1], zblocks, 
                                    convention = ini.mesh.convention, 
                                    atmos_type = atmos_type)
    else:
        # rectangular
        print(f"gridtype: rectangular")
        xblocks = ini.mesh.xblocks
        yblocks = ini.mesh.yblocks
        zblocks = ini.mesh.zblocks
        # printBlockInfo(xblocks,"[xBLOCKS]")
        # printBlockInfo(yblocks,"[yBLOCKS]")
        # printBlockInfo(zblocks,"[zBLOCKS]")
        geo = mulgrid().rectangular(xblocks, yblocks, zblocks, 
                                    convention = ini.mesh.convention, 
                                    atmos_type = atmos_type)
        dat.grid = t2grid().fromgeo(geo)
        

    ## ROCKS ##
    for secRock in ini.rockSecList:
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
    if ini.atmosphere.includesAtmos:
        dat.grid.add_rocktype(ini.atmosphere.atmos)
        # set to grid
        for blk in dat.grid.blocklist:
            if blk.atmosphere:
                blk.rocktype = ini.atmosphere.atmos


    # TOPは時間不変に設定するならnegativeにする
    # set air layer
    geo.atmosphere_volume = 1e50
    geo.atmosphere_connection = 1e-9

    if showsProfiles:
        # open viewer
        plt = None
    else:
        # save image insted of opening viewer
        import matplotlib.pyplot as plt

    geo.slice_plot(line=90, block_names=False, rocktypes=dat.grid, plt=plt)
    if not showsProfiles:
        plt.savefig(os.path.join(ini.t2FileDirFp, f"rocktypes_deg90.pdf"))
    geo.slice_plot(line=0, block_names=True, rocktypes=dat.grid, plt=plt)
    if not showsProfiles:
        plt.savefig(os.path.join(ini.t2FileDirFp, f"rocktypes_deg0.pdf"))
    # geo.layer_plot(None, column_names=True, plt=plt)
    # if not showsProfiles:
    #     plt.savefig(os.path.join(ini.t2FileDirFp, f"rocktypes_layer.pdf"))

    # save mulgrid object
    geo.write(mulgridFileFp)
    # write tough input file
    dat.write(t2GridFp)

    try: 
        shutil.copy2(ini.inputIniFp, t2FileDirFp)
    except shutil.SameFileError:
        pass

