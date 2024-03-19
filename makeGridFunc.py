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
import scipy
import copy
import define_logging

def makeGrid(ini:_readConfig.InputIni, force_overwrite_all=False, 
             open_viewer=False, force_overwrite_t2data=True, plot_all_layers=False, layer:str=None ):
    
    if ini.mesh.type == REGULAR:
        # if ini.t2GridFp does not exist --> create grid
        # if ini.t2GridFp exists,
        #     force_overwrite_all is True --> create grid
        #     force_overwrite_all is False --> skip creation and exit

        if os.path.isfile(ini.t2GridFp) and not force_overwrite_all:
            print(f"t2Grid file : {ini.t2GridFp} exists")
            print(f"    add option -fa (specify force_overwrite_all True) to force overwrite")
            return
        
        
        if ini.mesh.incorporatesCone:
            # 2-D radial grid with edifice
            makeGrid2dRadialEdifice(ini, showsProfiles=open_viewer)
        else:
            # 3-D rectilinear OR 2-D radial grid (with no edifice)
            makeGridRegular(ini, showsProfiles=open_viewer)
        
    elif ini.mesh.type == AMESH_VORONOI:
        # ini.t2FileDirFp exists | force_overwrite_all | force_overwrite_t2data||
        # -----------------------------------------------------------------------
        #                  True  |                True |                  True || create mulgrid and t2grid
        #                  True  |                True |                  False|| create mulgrid and t2grid
        #                  True  |                False|                  True || create only t2grid
        #                  True  |                False|                  False|| skip creation and raise
        #                  False |                True |                  True || create mulgrid and t2grid
        #                  False |                True |                  False|| create mulgrid and t2grid
        #                  False |                False|                  True || create only t2grid
        #                  False |                False|                  False|| create only t2grid

        ini.rocktypeDuplicateCheck()
        # create save dir. 
        if os.path.isdir(ini.t2FileDirFp) and not force_overwrite_all and not force_overwrite_t2data:
            print(f"Problem directory: {ini.t2FileDirFp} already exists")
            print(f"    add option -f (specify force_overwrite_t2data True) to force overwrite")
            return
        
        makeGridAmeshVoro.makePermVariableVoronoiGrid(ini, 
                                    force_overwrite_all=force_overwrite_all,
                                    open_viewer=open_viewer,
                                    plot_all_layers=plot_all_layers,
                                    layer_no_to_plot=layer)


# def makeGrid(ini:_readConfig.InputIni, overWrites=False, showsProfiles=False):
#     if ini.mesh.type == REGULAR:
#         # 軽いので常に作り直す(overWrites=True)
#         # makeGridRegular(ini, overWrites=True, showsProfiles=showsProfiles)
#         if ini.mesh.incorporatesCone:
#             # 2-D radial grid with edifice
#             makeGrid2dRadialEdifice(ini, overWrites=overWrites, showsProfiles=showsProfiles)
#         else:
#             # 3-D rectilinear OR 2-D radial grid (with no edifice)
#             makeGridRegular(ini, overWrites=overWrites, showsProfiles=showsProfiles)

#     elif ini.mesh.type == AMESH_VORONOI:
#         if os.path.exists(ini.mulgridFileFp) and not overWrites:
#             return
#         makeGridAmeshVoro.makePermVariableVoronoiGrid(ini, 
#             force_overwrite_all=overWrites, open_viewer=showsProfiles)

def makeGridRegular(ini:_readConfig.InputIni, showsProfiles=False):

    if ini.mesh.type == AMESH_VORONOI:
        sys.exit()

    #######

    ## read inputIni ##
    II = ini.toughInput
    ## define filepath
    mulgridFileFp = ini.mulgridFileFp
    t2FileDirFp = ini.t2FileDirFp
    t2FileFp = ini.t2FileFp
    t2GridFp = ini.t2GridFp
    # create save dir. 
    os.makedirs(t2FileDirFp, exist_ok=True) 

    ######

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
        plt.close()
    geo.slice_plot(line=0, block_names=True, rocktypes=dat.grid, plt=plt)
    if not showsProfiles:
        plt.savefig(os.path.join(ini.t2FileDirFp, f"rocktypes_deg0.pdf"))
        plt.close()
    # geo.layer_plot(None, column_names=True, plt=plt)
    # if not showsProfiles:
    #     plt.savefig(os.path.join(ini.t2FileDirFp, f"rocktypes_layer.pdf"))

    # save mulgrid object
    geo.write(mulgridFileFp)
    # write tough input file
    dat.write(t2GridFp)


def makeGrid2dRadialEdifice(ini:_readConfig.InputIni, showsProfiles=False):
    """
    create 2-D radial grid with incorporating an edifice
    """

    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")
    
    # create save dir. 
    os.makedirs(ini.t2FileDirFp, exist_ok=True) 
    

    ## 地形データの指定 ##
    """
    R,ELEVは同じ大きさの配列で、Rにr座標, ELEVに標高値を書く。あとで補間するのでセル中心のr座標でなくてOK
    例)
    標高点(r,z)が(0,10), (50,100), (100, 150)の3つのときは以下のようにする
    R=[0, 50, 100]
    ELEV=[10,100,150]
    """
    # 地形データ
    dr = 10 # 刻み幅
    if ini.mesh.isSimpleCone:
        height = ini.mesh.cone_height_above_base
        radius = ini.mesh.cone_base_radius
        R = np.arange(0,sum(ini.mesh.rblocks),dr)
        ELEV = [ (ini.mesh.cone_top_elevation-height/radius*r if r<radius 
                else ini.mesh.cone_top_elevation-height) for r in R]
    else:
        R = ini.mesh.cone_shape_r
        ELEV = ini.mesh.cone_shape_elev
        # coneの底部が領域より小さい場合、外側へ補外
        if R[-1] < sum(ini.mesh.rblocks):
            r_extra = np.arange(R[-1],sum(ini.mesh.rblocks),dr)
            R += list(r_extra)
            ELEV += list([ELEV[-1] for _ in range(len(r_extra))])
    # 線形補間する。elev = f(r)となる関数ができる。 
    f = scipy.interpolate.interp1d(R,ELEV,kind='linear')

    # mulgrid.rectangular, t2grid.radialでの座標計算のorigin
    # add z offset to avoid too steep cone top
    ORIGIN_Z = float(f(0))
    print(f"CALCULATED ORIGIN (x,y,z): {0, 0, ORIGIN_Z}")


    ## 断面描画用mulgraphファイルの作成 ##
    # 地形なし直方体2Dメッシュのgeoファイルを作成 
    geo = mulgrid().rectangular(ini.mesh.rblocks, [1], ini.mesh.zblocks,
                                origin=[0, 0, ORIGIN_Z], 
                                convention = ini.mesh.convention, 
                                atmos_type = 0 if ini.atmosphere.includesAtmos else 2)
    # 一旦ファイルとして書き出す。
    geo.write(ini.mulgridFileFp+"tmp")

    # 書き出したファイルを手動で編集し、標高データを書き加える。
    with open(ini.mulgridFileFp+"tmp", "r") as f1, open(ini.mulgridFileFp, "w") as f2:
        # 一行目だけ手動で処理
        line_bf = f1.readline()
        f2.write(line_bf)
        # 二行目以降は以下のループで処理
        for line in f1:
            # detect end of file (空行が2回続いているかどうかで判定)
            if len(line_bf.strip())==0 and len(line.strip())==0:
                f2.write('SURFA\n')
                for col in geo.columnlist:
                    elev = f(col.centre[0])
                    f2.write(f"{str(col):3}{elev:>10.1f}\n")
                break
            else:
                # if not end of file,
                # 行の内容をそのままコピー
                f2.write(line)
            line_bf = line

    # 編集したmulgraphファイルを再度読み込む。読み込まれた時点で地形ができる。
    geo_topo = mulgrid(ini.mulgridFileFp, atmos_type=0)
    # 地表面の要素の厚さを揃える
    geo_topo.snap_columns_to_nearest_layers()
    # 揃えてから書き出し
    geo_topo.write()


    ## TOUGH3の入力データ作成 ##
    # new t2data object
    dat = t2data()
    dat.filename = ini.t2GridFp

    # 地形なしradialグリッドを作成
    # 注) 地形ありmulgraphをradialに変換することはできないので、radialグリッドに変換してから再度地形を作成する。
    # [radial origin(starting radius), vertical origin (position of the top layer)]
    dat.grid = t2grid().radial(ini.mesh.rblocks, ini.mesh.zblocks, 
                convention=ini.mesh.convention, 
                origin = [0, ORIGIN_Z],
                atmos_type=0 if ini.atmosphere.includesAtmos else 2) 
            
    #不要な要素の洗い出し。
    del_blk_names = []
    for blk in dat.grid.blocklist:
        blk: t2block
        # 空気層の場合はスキップ
        if blk.atmosphere:
            print("ATMOSPHERE BLK NAME: ",blk.name)
            continue
        # # 地表面の標高より中心が高くにあるときは要素を削除する
        # if blk.centre[2] > f(blk.centre[0]):
        #     del_blk_names.append(blk.name)
        # 地表面の標高より底面が高くにある要素を削除する 
        laybot = geo_topo.layer[geo_topo.layer_name(blk.name)].bottom
        colsuf = geo_topo.column[geo_topo.column_name(blk.name)].surface
        if laybot >= colsuf:
            del_blk_names.append(blk.name)
            


    # 不要な要素の削除前の地形なしgeoからconnection情報を取り出しておく
    dict_col_conn = {}
    for conn in dat.grid.connectionlist:
        if ATM_BLK_NAME(ini.mesh.convention) == conn.block[0].name:
            dict_col_conn[geo.column_name(conn.block[1].name)] = copy.deepcopy(conn)
        elif ATM_BLK_NAME(ini.mesh.convention) == conn.block[1].name: 
            dict_col_conn[geo.column_name(conn.block[0].name)] = copy.deepcopy(conn)

    # 不要な要素の削除
    for dblk in del_blk_names:
        dat.grid.delete_block(dblk)

    # 表層要素と空気層の間のconnectionを復活させる
    for col in geo_topo.columnlist:
        layer_top = geo_topo.column_surface_layer(col)
        blockname_top = geo_topo.block_name(layer_top.name, col.name)
        dict_col_conn[col.name].block = [dat.grid.block[blockname_top],
                                        dat.grid.block[ATM_BLK_NAME(ini.mesh.convention)]]
        dat.grid.add_connection(dict_col_conn[col.name])

    # 海水を含む場合、海水面以下では空気層との接続を遮断しておく
    # 補足)
    # tough3exec_ws.pyではブロック/接続が追加され、グリッド情報が変わってしまうことがある。
    # そこで、makeVtu.pyではflowのプロットの際にエラーが起きないようにtough3exec_ws.py
    # で作成したグリッドではなくmakeGrid.pyで作成されたもの(ini.t2GridFp)を参照するよう
    # にしている。 このとき、t2listingで読み込んだ結果に含まれる追加済みのブロック・接続の
    # 情報についてのみt2outUtilで除去することで、
    #   resultDataのブロック/接続数==makeGrid出力(ini.t2GridFp)のブロック・接続数, 
    # の関係を維持している。
    # tough3exec_ws.pyのSEAFLOORパートではt2gridに対して'追加'ではなく、空気層との接続
    # を'削除'する編集を加えるので、計算結果に含まれるブロック/接続数も少なくなりこの関係が
    # 破綻してしまう。これを防ぐためにini.t2GridFpに対しても同様の編集を加えておく必要がある。
    if hasattr(ini, 'sea') and (
            ECO2N in ini.toughInput['module'].strip().lower() or \
            EWASG in ini.toughInput['module'].strip().lower()):
        
        for col in geo_topo.columnlist:
            col:column
            if col.surface < ini.sea.sea_level: # surface elevation
                layer_top = geo_topo.column_surface_layer(col)
                blockname_top = geo_topo.block_name(layer_top.name, col.name)
                # If the block has a connection to ATM-blk, kill that connection.
                atmconn = (blockname_top, geo_topo.block_name(geo_topo.layerlist[0].name,geo_topo.atmosphere_column_name))
                if atmconn in dat.grid.connection:
                    dat.grid.delete_connection(atmconn)
                    logger.info(f"connection killed: {atmconn}")
                elif (atmconn[1], atmconn[0]) in dat.grid.connection:
                    dat.grid.delete_connection((atmconn[1], atmconn[0]))
                    logger.info(f"connection killed: {(atmconn[1], atmconn[0])}")


    # 岩石タイプ割り当て (makeGridFunc.makeGridRegularの一部をそのまま流用)
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

    # 書き出し
    dat.write(ini.t2GridFp)

    # geo_topo.slice_plot(line='x', rocktypes=dat.grid,block_names=True)
    if showsProfiles:
        # open viewer
        plt = None
        blknm = True
    else:
        # save image insted of opening viewer
        import matplotlib.pyplot as plt
        blknm = False
    geo_topo.slice_plot(line='x', rocktypes=dat.grid, block_names=blknm, plt=plt)
    lim = plt.ylim()    
    plt.ylim(lim[0] ,max(ELEV))
    plt.savefig(os.path.join(ini.t2FileDirFp, f"rocktypes.pdf"))
    plt.close()


