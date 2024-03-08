from import_pytough_modules import *
from t2data import *
import math
import _readConfig
import shutil
import numpy as np
import copy
import time
from pytough_override import mulgridSubVoronoiAmesh
from scipy.interpolate import LinearNDInterpolator
import pandas as pd
import functionUtil as fu
# import pickle
import dill as pickle
import define_logging
import seed_to_voronoi

vtk = os.path.join(baseDir, "mesh_with_topography.vtk")

def main():

    ## get argument
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("inputIni", 
            help="fullpath of toughInput setting input.ini", type=str)
    parser.add_argument("-f","--force_overwrite_t2data", 
            help="if given, use existing mulgrid file and overwrite existing t2data file", action='store_true')
    parser.add_argument("-fa","--force_overwrite_all", 
            help="if given, recreate all existing grid and input file", action='store_true')
    parser.add_argument("-view","--open_viewer", 
            help="if given, open window viewing figures, insted of saving image", action='store_true')
    parser.add_argument("-all","--plot_all_layers", 
            help="if given, saving figures for all layers", action='store_true')
    parser.add_argument("-layer","--layer", 
            help="if the layer index 'LAYER' is given, saving a figure of the specified layer", type=str)
    # parser.add_argument("-p","--showsProfile", 
    #         help="if given, show grid profile", action='store_true')
    args = parser.parse_args()

    ## read inputIni ##
    ini = _readConfig.InputIni().read_from_inifile(args.inputIni)
    ini.rocktypeDuplicateCheck()
    # create save dir. 
    try:
        os.makedirs(ini.t2FileDirFp, exist_ok=True) \
            if args.force_overwrite_all or args.force_overwrite_t2data \
            else os.makedirs(ini.t2FileDirFp)
    except FileExistsError:
        print(f"directory: {ini.t2FileDirFp} exists")
        print(f"    add option -f to force overwrite")
        sys.exit()
    
    makePermVariableVoronoiGrid(ini, 
        force_overwrite_all=args.force_overwrite_all,
        open_viewer=args.open_viewer,
        plot_all_layers=args.plot_all_layers,
        layer_no_to_plot=args.layer)
    
    try: 
        shutil.copy2(ini.inputIniFp, ini.t2FileDirFp)
    except shutil.SameFileError:
        pass

        
"""
type: A_VORO
function util
"""
def col_name(col_id, convention):
    ## MULgraph geometry file Naming conventions (optional)
    # 0: 3 characters for column followed by 2 digits for layer (default)
    # 1: 3 characters for layer followed by 2 digits for column 
    # 2: 2 characters for layer followed by 3 digits for column
    if convention==0:
        if col_id > 27*26*26+26: raise Exception(f"Too many columns. (must be <= {27*26*26+26} for convention: {convention})")
        ret = int_to_chars(col_id)
        return f"{ret:3}"    
    elif convention==1:
        if col_id > 99: raise Exception(f"Too many columns. (must be <= 99 for convention: {convention})")
        ret = col_id
        return f"{ret:2}"    
    elif convention==2:
        if col_id > 999: raise Exception(f"Too many columns. (must be <= 999 for convention: {convention})")
        ret = col_id
        return f"{ret:3}"    
    else: raise Exception

def layer_name(layer_id, convention):
    ## MULgraph geometry file Naming conventions (optional)
    # 0: 3 characters for column followed by 2 digits for layer (default)
    # 1: 3 characters for layer followed by 2 digits for column 
    # 2: 2 characters for layer followed by 3 digits for column
    if convention==0:
        if layer_id > 99: raise Exception(f"Too many layers. (must be <= 99 for convention: {convention})")
        ret = layer_id
        return f"{ret:2}"    
    elif convention==1:
        if layer_id > 27*26*26+26: raise Exception(f"Too many layers. (must be <= {27*26*26+26} for convention: {convention})")
        ret = int_to_chars(layer_id)
        return f"{ret:3}"    
    elif convention==2:
        if layer_id > 27*26: raise Exception(f"Too many layers. (must be <= {27*26} for convention: {convention})")
        ret = int_to_chars(layer_id)
        return f"{ret:2}"    
    else: raise Exception

def elem_name(layer_id, col_id, convention):
    if convention==0:
        return col_name(col_id,convention)+layer_name(layer_id,convention)
    if convention==1 or convention==2:
        return layer_name(layer_id,convention)+col_name(col_id,convention)

def resistivity2porosity(formula, rho, x, y, z, phi, k_x, k_y, k_z):
    return eval(formula)

def porosity2permeability(formula, phi, x, y, z, k_x, k_y, k_z):
    return eval(formula)


def create_mulgrid_with_topo(ini:_readConfig.InputIni):
    """
    read voronoi seed points list from the file of ini.amesh_voronoi.voronoi_seeds_list_fp
    and output mulgrid setting file ini.mulgridFileFp.
    [required files or program]
        ini.amesh_voronoi.voronoi_seeds_list_fp
        ini.amesh_voronoi.topodata_fp
        define.AMESH_PROG

    """
    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")
    import os

    mulgraph_no_topo_fn = os.path.join(baseDir, FILENAME_TMP_MULGRAPH_NO_TOPO)
    
    # functionalized 2023/11/27
    """
    create voronoi grid and convert it to mulgraph file (no topography included)
    """
    if ini.amesh_voronoi.uses_amesh:
        # use AMESH (Haukwa, 1998)
        executesAmesh(ini, output_fp=mulgraph_no_topo_fn)
    else:
        # use scipy.spatial.Voronoi
        seed_to_voronoi.seed_to_mulgraph_no_topo(
            ini, output_fp=mulgraph_no_topo_fn, showVoronoi=False)
    
    # "ini.amesh_voronoi.elevation_top_layer" is layer center elevation of the top layer
    bottom_of_bottom_layer_elev = ini.amesh_voronoi.elevation_top_layer \
                                + ini.amesh_voronoi.layer_thicknesses[0] \
                                - sum(ini.amesh_voronoi.layer_thicknesses)
    geo = mulgrid(mulgraph_no_topo_fn)

    """
    assign topography
    """
    print("*** reading topodata and generating interpolating function")
    start = time.perf_counter()
    interp = load_topo_file(topofile_fp=ini.amesh_voronoi.topodata_fp)
    end = time.perf_counter()
    print(f"    finished {end - start:10.2f}[s]")

    # append SURFA section to mulgraph file
    print("*** create mulgraph setting file of grid with topography")
    with open(mulgraph_no_topo_fn, "r") as f1,\
        open(ini.mulgridFileFp, "w") as f2:
        line_bf = f1.readline()
        f2.write(line_bf)
        for line in f1:
            # detect end of file (空行が2回続くとそこがend of file)
            if len(line_bf.strip())==0 and len(line.strip())==0:
                # if end of file, add SURFA section
                f2.write("SURFA\n")
                for col in geo.columnlist:
                    col:column
                    elev = interp(col.centre)[0]
                    logger.debug(f"col:{col} elevation: {elev:.1f}")
                    if elev <= bottom_of_bottom_layer_elev + ini.amesh_voronoi.top_layer_min_thickness:
                        logger.error(f"Surface elevation ({elev:.1f}) at column '{col}' is lower"
                                     f" than the elevation at the bottom of domain"
                                     f" ({bottom_of_bottom_layer_elev+ini.amesh_voronoi.top_layer_min_thickness}).")
                        logger.error(f"Please add more elements in 'layer_thicknesses'.")
                        
                        """ visualize position of bad column with topography """
                        import matplotlib.pyplot as plt
                        geo.layer_plot(plt=plt, column_names=[col.name])
                        plt.plot(col.centre[0], col.centre[1], 'ro', ms=10)
                        x = np.linspace(-10000, 10000, 1000)
                        y = np.linspace(-10000, 10000, 1000)
                        X, Y = np.meshgrid(x,y)
                        Z = interp(X,Y)
                        plt.contour(X,Y,Z,np.arange(-5000,2500,100),colors='blue', linewidths=1)
                        plt.contour(X,Y,Z,np.arange(-5000,2500,10),colors='blue', linewidths=0.2)
                        # invert y axis
                        lim = plt.ylim()    
                        plt.ylim((lim[1],lim[0]))
                        plt.savefig(ini.mulgridFileFp+f"_error_at_col{col}.pdf")
                        """"""

                        raise SurfaceElevationLowerThanBottomLayerException(
                                    f"Surface elevation ({elev:.1f}) at column '{col}' is lower"
                                    f" than the elevation at the bottom of domain"
                                    f" ({bottom_of_bottom_layer_elev+ini.amesh_voronoi.top_layer_min_thickness}).")
                    f2.write(f"{str(col):3}{elev:>10.1f}\n")
                break
            else:
                # if not end of file,
                f2.write(line)
            line_bf = line

    print("    finished")

    # to avoid generating too thin top layer 
    print("*** snap_columns_to_layers")
    geo_topo = mulgrid(ini.mulgridFileFp)
    print(ini.amesh_voronoi.top_layer_min_thickness)
    geo_topo.snap_columns_to_layers(min_thickness=ini.amesh_voronoi.top_layer_min_thickness)
    # you have to write mulgrid-file after doing snap_columns_to_layers()
    geo_topo.write(ini.mulgridFileFp)


def executesAmesh(ini:_readConfig.InputIni, output_fp:str):
    
    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")
    import os
    
    # clean
    try:
        os.remove(output_fp) 
        os.remove(os.path.join(AMESH_DIR, AMESH_INPUT_FILENAME))
        os.remove(os.path.join(AMESH_DIR, AMESH_SEGMT_FILENAME))
    except FileNotFoundError:
        pass
    
    # TODO check files existence 
    # - ini.amesh_voronoi.voronoi_seeds_list_fp
    # - ini.amesh_voronoi.topodata_fp

    """
    read 2D Voronoi seed points
    """
    seeds = np.array(
        pd.read_csv(ini.amesh_voronoi.voronoi_seeds_list_fp, delim_whitespace=True))
    if ini.mesh.convention==0 and len(seeds)>945:
        # AMESHのせいか、PyTOUGHのせいかわからないが、
        # convention==0かつseedsが945個以上だとmulgrid().from_ameshでエラーになる。
        # raise Convention_ga_0_de_seeds_ga_945_yori_ooi_kara_amesh_de_error_ni_naruyo
        
        # 2022/06/17追記
        # from_ameshでエラーになるのはseedの数が原因ではなさそう。
        # 945個以上でエラーになってもtolarを小さくするとエラーはなくなった
        pass

    """
    create AMESH input file
    """
    elevation = ini.amesh_voronoi.elevation_top_layer
    layer_id = 1
    with open(os.path.join(AMESH_DIR, AMESH_INPUT_FILENAME), "w") as f:
        f.write("locat\n")
        for i, l in enumerate(ini.amesh_voronoi.layer_thicknesses):
            col_id = 1
            for seed in seeds:
                # print(elem_name(layer_id, col_id, convention))
                f.write(f"{elem_name(layer_id, col_id, ini.mesh.convention):<5}{layer_id:>5} ")
                f.write(f"{seed[0]:15f} {seed[1]:15f} {elevation:>10} {l:>10}\n")
                col_id += 1
            layer_id += 1
            if i+1<len(ini.amesh_voronoi.layer_thicknesses) :
                # next layer elevation = 
                # current layer elevation - (current layer thickness + next layer thickness) / 2
                elevation = elevation - (l+ini.amesh_voronoi.layer_thicknesses[i+1])/2
                logger.debug(f"layer{i+1} elevation {elevation}m")
        f.write(f"\ntoler\n{ini.amesh_voronoi.tolar}\n")
    bottom_of_bottom_layer_elev = elevation \
                                  - ini.amesh_voronoi.layer_thicknesses[-1]/2 
    logger.debug(f"{bottom_of_bottom_layer_elev}")

    """
    execute prog AMESH
    """
    os.chdir(AMESH_DIR)
    print("*** executing program AMESH")
    start = time.perf_counter()
    os.system(os.path.join(".", AMESH_PROG))
    end = time.perf_counter()
    print(f"    finished {end - start:10.2f}[s]")
    os.chdir(baseDir)

    # TODO check files existence 
    # os.path.join(AMESH_DIR, AMESH_INPUT_FILENAME)
    # os.path.join(AMESH_DIR, AMESH_SEGMT_FILENAME)
    # なければameshが動いていない

    """
    read AMESH output and convert to mulgraph 
    """
    # nodeの数の桁がcolumnの桁数(convention=2なら3)を超えるとエラーになる。
    # MULgraphファイルのnodeの桁は3つが最大。
    print("*** converting AMESH segmt file to mulgrid object")
    start = time.perf_counter()
    geo,blockmap=mulgrid().from_amesh(
                            os.path.join(AMESH_DIR, AMESH_INPUT_FILENAME), 
                            os.path.join(AMESH_DIR, AMESH_SEGMT_FILENAME),
                            convention=ini.mesh.convention)
    end = time.perf_counter()
    print(f"    finished {end - start:10.2f}[s]")
    # geo.layer_plot(None, column_names=True)
    """
    geo.slice_plot(line="x", block_names=True)
    geo.slice_plot(line="y", block_names=True)
    """
    geo.set_atmosphere_type(0 if ini.atmosphere.includesAtmos else 2)

    geo.write(output_fp)



def makePermVariableVoronoiGrid(ini:_readConfig.InputIni,
                                force_overwrite_all=False,
                                open_viewer=False,
                                plot_all_layers=False,
                                layer_no_to_plot=None,
                                fex="pdf"):
    """[summary]
        main function (mesh.type: A_VORO)
        make Permeability Variable Voronoi Grid.
    Args:
        ini (_readConfig.InputIni): [description]
        force_overwrite_all (bool, optional): 
            If True, recreate all existing grid and input file. Defaults to False.
        open_viewer (bool, optional): 
            If True, open window viewing figures, insted of saving image. Defaults to True.
        layer_no_to_plot (int, optional):
            If not none, a horizontal slice of specified layer number is created.
        fex (str, optional):
            file extension of image files.
            
    Raises:
        Exception: [description]
    """

    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")
    
    if ini.mesh.type != AMESH_VORONOI:
        sys.exit()

    """create dir"""
    if not os.path.isdir(ini.t2FileDirFp):
        os.makedirs(ini.t2FileDirFp, exist_ok=True)

    """
    if mulgraph_with_topo_fn does not exist, 
    create it from seed points list using AMESH prog
    """
    if not os.path.isfile(ini.mulgridFileFp)\
            or force_overwrite_all:
        create_mulgrid_with_topo(ini)
    if not os.path.isfile(ini.mulgridFileFp):
        print(f"mulgridFileFp not created: {ini.mulgridFileFp}")
        raise Exception(f"mulgridFileFp not created: {ini.mulgridFileFp}")

    """
    read mulgraph file that includes topo
    """
    print(f"*** reading existing mulgrid file: {ini.mulgridFileFp}")
    geo_topo = mulgrid(ini.mulgridFileFp, 
                       atmos_type=0 if ini.atmosphere.includesAtmos else 2)

    # geo_topo.layer_plot(None, column_names=True)
    # geo_topo.write_vtk(vtk)

    """
    Calculate resistivity value at each grid block by interpolation.
    Permeabilities of each block are calculated using the resistivity values.
    """
    # read resistivity structure
    print(f"*** reading resistivity data and generating interpolating function")
    start = time.perf_counter()
    # create or load resistivity interpolating function 
    pickledres = ini.mesh.resistivity_structure_fp+"_pickled"
    if os.path.isfile(pickledres):
        logger.debug(f"load pickled interpolating function: {pickledres}")
        # load selialized interpolating function
        with open(pickledres, 'rb') as f:
            interpRes = pickle.load(f)   
    else:
        logger.debug(f"create interpolating function and pickle: {pickledres}")
        # read data file
        df = pd.read_csv(ini.mesh.resistivity_structure_fp, delim_whitespace=True)
        x = np.array(df['x'])
        y = np.array(df['y'])
        z = np.array(df['z'])*(-1) # convert bsl to asl
        res = np.array(df['res'])    
        # interpolating function
        interpRes = LinearNDInterpolator(list(zip(x,y,z)), res)
        # serialize and save
        with open(pickledres, 'wb') as f:
            pickle.dump(interpRes, f)         
    end = time.perf_counter()
    print(f"    finished {end - start:10.2f}[s]")

    # create new t2data object
    dat = t2data()
    # convert mulgrid geometry object to t2grid, and set to created t2data
    print(f"*** converting mulgrid object to t2data object")
    start = time.perf_counter()

    pickledgeo = ini.mulgridFileFp+"_t2grid_pickled"
    # check existence of geo file, and then, updated time difference bet. geo file and pickled file
    if os.path.isfile(pickledgeo) and os.stat(ini.mulgridFileFp).st_mtime < os.stat(pickledgeo).st_mtime:
        print(f"load pickled object: {pickledgeo}")
        # load selialized object
        with open(pickledgeo, 'rb') as f:
            dat.grid = pickle.load(f)   
    else:
        print(f"create new and pickle: {pickledgeo}")
        # create t2grid newly 
        dat.grid.fromgeo(geo_topo)
        # serialize and save
        with open(pickledgeo, 'wb') as f:
            pickle.dump(dat.grid, f)      
    
    end = time.perf_counter()
    print(f"    finished {end - start:10.2f}[s]")
    
    ## define permeability modifier (PM)  
    print(f"*** assign rocktype and permeability modifier")
    start = time.perf_counter()
    """
    if seedflg is True, block-by-block permeability modifier become valid.
    In this case, pmx must be supplied in ELEME block in INFILE.
    """
    if ini.toughInput['seedFlg']:
        seed = rocktype(name = "SEED ", 
                        density = 0, # no internal generation of "linear" PM. 
                        porosity = 0, # no internal generation of "logarithmic" PM. 
                        permeability = [0, 0, 0] # no scale factor and no shift
                        )
        dat.grid.add_rocktype(seed)

    ## ROCKS ##
    for secRock in ini.rockSecList:
        count = 0
        # set rocktype to grid
        dat.grid.add_rocktype(secRock.rocktype)
        for blk in dat.grid.blocklist:
            """
            skip atmosphere block
            """
            if blk.atmosphere:
                continue
            """
            if current blk included in secRock.blockList, assign current rocktype  
            """
            if secRock.isBlkInBlockList(blk): #TODO create judge method in _RocktypeSec
                blk.rocktype = secRock.rocktype
                count += 1
            """
            if the position of current blk does not included in the assignable range 
                skip to next blk.
            """
            if not secRock.isBlkInAssignableRange(blk): #TODO create judge method in _RocktypeSec
                continue
            """
            prepare variables, which are evaluated in judging assign_condition
                or in the calculation of resistivity dependent permeability
            """
            # blk position
            x = blk.centre[0]
            y = blk.centre[1]
            z = blk.centre[2]
            surface = geo_topo.column[geo_topo.column_name(blk.name)].surface
            depth = surface - z
            # properties of current rocktype
            phi = blk.rocktype.porosity
            k_x = secRock.rocktype.permeability[0]
            k_y = secRock.rocktype.permeability[1]
            k_z = secRock.rocktype.permeability[2]
            # For each block, calc resistivity value at the center of the block 
            # by interpolation, 
            rho = interpRes(blk.centre)[0]
            # calculate block-by-block porosity by evaluating formula given by ini file
            porosity = eval(secRock.formula_porosity) 
            # calculate block-by-block permeability by evaluating formula given by ini file
            perm = eval(secRock.formula_permeability)
            # judge current blk satisfies the rocktype assignment condition by evaluating given formula 
            applies = eval(secRock.rock_assign_condition) 
            """
            If the property of the current block satisfies the rocktype assignment condition, 
                assign current rocktype to current blk
            """
            if applies:
                blk.rocktype = secRock.rocktype
            else:
                continue                
            """
            if seedflg is True, block-by-block permeability modifier (PM) become valid.
            PM is adjusted to permeablity value (perm) caluculated above.
            """
            if ini.toughInput['seedFlg']:
                """
                In TOUGH3, permeability of the block is modified as following relation,
                    perm = perm_ref * PM
                [variables]
                    perm: permeability value of the block used in the simulation
                    perm_ref: original permeability of the block before modified
                            (= permeability of rock(type) of the block)
                    PM: block-by-block permeability modifier 
                """
                perm_ref = blk.rocktype.permeability[0]
                # calc PM coefficient of the block
                pm = perm/perm_ref
                # set PM coefficient to ELEME.PMX
                blk.pmx = pm
            count += 1

        print(f"ROCK: {secRock.secName}\tnCELLS: {count}")

    # atmosphere
    if ini.atmosphere.includesAtmos:
        # set atomosphere
        dat.grid.add_rocktype(ini.atmosphere.atmos)
        # set to grid
        for blk in dat.grid.blocklist:
            if blk.atmosphere:
                blk.rocktype = ini.atmosphere.atmos

    end = time.perf_counter()
    print(f"    finished {end - start:10.2f}[s]")
    
    # set boundary condition on the side of computational domain
    if ini.boundary.boundary_side_permeable:
        print(f"*** set boundary condition")

        # By assigning huge volumes, it does not cause temperature changes, 
        # forcing it to behave like a black hole.
        boundblks, boundblk_edge_areas =\
             get_outer_boundary_blocks(geo_topo, dat.grid, geo_topo.convention)
        for blk in boundblks:
            blk.volume = HUGE_VOLUME
            # blk.rocktype = bound
        end = time.perf_counter()

        # delete connection between boundary blocks
        kill_connections_betw_boundary_blks(geo_topo, dat.grid, geo_topo.convention)
    
    # ## side ##
    # # set boundary condition on the side of computational domain
    # if ini.boundary.boundary_side_permeable:
    #     print(f"*** set boundary condition")
    #     boundblks, boundblk_edge_areas =\
    #          get_outer_boundary_blocks(geo_topo, dat.grid, geo_topo.convention)
    #     for i, blk in enumerate(boundblks):
    #         blknm = f"BD{num_convert_to_blkname_3digit(i)}"
    #         blockBound = t2block(name=blknm, volume=HUGE_VOLUME, blockrocktype=blk.rocktype)
    #         dat.grid.add_block(blockBound)
    #         conn = t2connection(blocks=[blk, blockBound], 
    #                             distance=BOUND_BLK_CONN_DISTANCE, area=boundblk_edge_areas)
    #         dat.grid.add_connection(conn)
    #         binc = t2blockincon(variable=inc[blk.name].variable, block=blknm)
    #         inc.add_incon(binc)

    # TODO 海水対応。上面に海水を割り当てるからむがある場合、この段階で空気層との接続をカットしておく必要がある。
    

    # write tough input file
    dat.write(ini.t2GridFp)

    # test plot (interpolated resistivity structure)
    temp_res = [] 
    temp_perm = []
    for blk in dat.grid.blocklist:
        if not blk.atmosphere:
            # calc resistivity value at the center of the block by interpolation
            rho = interpRes(blk.centre)[0]
            temp_res.append(rho)   
            if ini.toughInput['seedFlg']:
                k = blk.pmx *  blk.rocktype.permeability[0] 
            else:
                k = blk.rocktype.permeability[0]          
            temp_perm.append(k)   
        else:
            # atmosphere blocks
            temp_res.append(1e8)
            temp_perm.append(1e-20)   

    variable_res = np.array(temp_res)
    variable_perm = np.array(temp_perm)
    
    """pickle created array for next visualization"""
    if not os.path.isdir(ini.savefigFp):
        os.makedirs(ini.savefigFp)
    np.save(os.path.join(ini.savefigFp, PICKLED_MULGRID_PERM), variable_perm)
    np.save(os.path.join(ini.savefigFp, PICKLED_MULGRID_RES), variable_res)
    
    """visualize"""
    visualize_vslice(ini, 
                     geo_topo, 
                     variable_res,
                     variable_perm,
                     fex=fex, 
                     open_viewer=open_viewer)
    visualize_layer(ini, 
                    geo_topo, 
                    variable_res,
                    variable_perm,
                    fex=fex, 
                    open_viewer=open_viewer, 
                    plot_all_layers=plot_all_layers,
                    layer_no_to_plot=layer_no_to_plot)
 
    
def visualize_vslice(ini:_readConfig.InputIni,
                     geo_topo: mulgrid,
                     variable_resistivity: np.array,
                     variable_permeability: np.array,
                     fex='pdf',
                     open_viewer=False):
    """_summary_

    Args:
        ini (_readConfig.InputIni): _description_
        geo_topo (mulgrid): _description_
        variable_resistivity (np.array): loaded array of (ini.savefigFp)/(PICKLED_MULGRID_PERM)
        variable_permeability (np.array): loaded array of (ini.savefigFp)/(PICKLED_MULGRID_RES)
        fex (str, optional): extention of created figures. Defaults to 'pdf'.
        open_viewer (bool, optional): 
            If True, open window viewing figures, insted of saving image. Defaults to True.
    """
    
    if open_viewer:
        # open viewer
        plt = None
    else:
        # save image insted of opening viewer
        import matplotlib.pyplot as plt
        plt.rcParams["font.size"] = FONT_SIZE
    
    # retrieve topo data
    elevations, X, Y = [], [], []
    for col in geo_topo.columnlist:
        X.append(col.centre[0])
        Y.append(col.centre[1])
        elevations.append(col.surface)
    # plot surface layer with colname
    # geo_topo.layer_plot(layer=geo_topo.layerlist[-1], variable=elevations, column_names=False, 
    #                     plt=plt, xlabel = 'Northing (m)', ylabel = 'Easting (m)',)
    geo_topo.layer_plot(layer=geo_topo.layerlist[-1], variable=None, column_names=False,
                        plt=plt, xlabel = 'Northing (m)', ylabel = 'Easting (m)', title="plan view")
    
    # overlay lines and topo
    if not open_viewer:
        # invert y axis
        lim = plt.ylim()    
        plt.ylim((lim[1],lim[0]))
        # topo
        plt.tricontour(X, Y, elevations, np.arange(-5000,5000,100), 
                            colors='blue', linewidths=1, alpha=0.3)
        plt.tricontour(X, Y, elevations, np.arange(-5000,5000,500), 
                            colors='blue', linewidths=2, alpha=0.3)
        # plot location of profiles
        for i, line in enumerate(ini.plot.profile_lines_list):
            if isinstance(line, (float, int)):
                x = plt.xlim()
                y = [plt.xlim()[0]*math.tan((90-line)/180*math.pi), 
                     plt.xlim()[1]*math.tan((90-line)/180*math.pi)]
                if abs(plt.xlim()[1]) > abs(plt.ylim()[1]*math.tan(line/180*math.pi)):
                    text_pos = [plt.ylim()[1]*math.tan(line/180*math.pi), 
                                plt.ylim()[1]]
                else:
                    text_pos = [plt.xlim()[1], 
                                plt.xlim()[1]*math.tan((90-line)/180*math.pi)]
            elif str(line).strip().lower() == 'x':
                x, y = plt.xlim(), [0, 0]
                text_pos = [0.9*plt.xlim()[1], 0]
            elif str(line).strip().lower() == 'y':
                x, y = [0, 0], plt.ylim()
                text_pos = [0, 0.9*plt.ylim()[1]]
            elif isinstance(line, (list, np.ndarray)):
                x = [line[0][0], line[1][0]]
                y = [line[0][1], line[1][1]]
                text_pos = [line[1][0], line[1][1]]
            else:
                continue
            plt.plot(x, y, linewidth=2.0, label=f'line #{i}')
            plt.text(text_pos[0], text_pos[1], f'line #{i}', fontsize=20)
            
        plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_LAYER_SURFACE}.{fex}"))
    
    # position of slice
    xslices = []
    yslices = []
    zslices = []
    # xslices = [1000]
    # yslices = [-500]
    # zslices = [0]
    # xslices = np.arange(0, 3001, 200)
    # yslices = np.arange(-3000, 600, 200)
    # zslices = np.arange(-4000, 1001, 500)
    # angle = -20

    for x in xslices:
        linex = np.array([[x,geo_topo.bounds[0][1]],[x,geo_topo.bounds[1][1]]])
        geo_topo.slice_plot(line=linex, 
                            variable=np.log10(variable_permeability), 
                            variable_name='log10 permeability',
                            colourmap=CMAP_PERMEABILITY, 
                            plt=plt,
                            colourbar_limits=CBAR_LIM_LOG10PERM,
                            )
        if not open_viewer:
            plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_PERM_SLICE_X}{x}.{fex}"))
            plt.close()
        geo_topo.slice_plot(line=linex, 
                            variable=np.log10(variable_resistivity), 
                            variable_name='log10 resistivity',
                            colourmap=CMAP_RESISTIVITY, 
                            plt=plt,
                            colourbar_limits=CBAR_LIM_LOG10RES)
        if not open_viewer:
            plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_RESIS_SLICE_X}{x}.{fex}"))
            plt.close()
    
    for y in yslices:
        liney = np.array([[geo_topo.bounds[0][0],y],[geo_topo.bounds[1][0],y]])
        geo_topo.slice_plot(line=liney, 
                            variable=np.log10(variable_permeability), 
                            variable_name='log10 permeability',
                            colourmap=CMAP_PERMEABILITY, 
                            plt=plt,
                            colourbar_limits=CBAR_LIM_LOG10PERM)
        if not open_viewer:
            plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_PERM_SLICE_Y}{y}.{fex}"))
            plt.close()
        geo_topo.slice_plot(line=liney, 
                            variable=np.log10(variable_resistivity), 
                            variable_name='log10 resistivity',
                            colourmap=CMAP_RESISTIVITY, 
                            plt=plt,
                            colourbar_limits=CBAR_LIM_LOG10RES)
        if not open_viewer:
            plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_RESIS_SLICE_Y}{y}.{fex}"))
            plt.close()
    
    for z in zslices:
        geo_topo.layer_plot(layer=int(z), 
                            variable=np.log10(variable_permeability),
                            variable_name='log10 permeability',
                            colourmap=CMAP_PERMEABILITY, plt=plt,
                            colourbar_limits=CBAR_LIM_LOG10PERM)
        if not open_viewer:
            # invert y axis
            lim = plt.ylim()    
            plt.ylim((lim[1],lim[0]))
            plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_PERM_SLICE_Z}{z}.{fex}"))
            plt.close()
        geo_topo.layer_plot(layer=int(z), 
                            variable=np.log10(variable_resistivity),
                            variable_name='log10 resistivity',
                            colourmap=CMAP_RESISTIVITY, plt=plt,
                            colourbar_limits=CBAR_LIM_LOG10RES)
        if not open_viewer:
            # invert y axis
            lim = plt.ylim()    
            plt.ylim((lim[1],lim[0]))
            plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_RESIS_SLICE_Z}{z}.{fex}"))
            plt.close()

    for l, line in enumerate(ini.plot.profile_lines_list):
        geo_topo.slice_plot(line=line, 
                            variable=np.log10(variable_permeability), 
                            variable_name='log10 permeability',
                            colourmap=CMAP_PERMEABILITY,
                            plt=plt,
                            plot_limits=ini.plot.slice_plot_limits,
                            colourbar_limits=CBAR_LIM_LOG10PERM)
        if not open_viewer:
            plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_PERM_SLICE_LINE}{l}.{fex}"))
            plt.close()
        geo_topo.slice_plot(line=line, 
                            variable=np.log10(variable_resistivity), 
                            variable_name='log10 resistivity',
                            colourmap=CMAP_RESISTIVITY,
                            plt=plt,
                            plot_limits=ini.plot.slice_plot_limits,
                            colourbar_limits=CBAR_LIM_LOG10RES)
        if not open_viewer:
            plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_RESIS_SLICE_LINE}{l}.{fex}"))
            plt.close()

    # topo
    geo_topo.layer_plot(layer=geo_topo.layerlist[-1], variable=elevations, plt=plt, title="elevation", xlabel="Northing (m)", ylabel="Easting (m)")
    if not open_viewer:
        plt.tricontour(X, Y, elevations, np.arange(-5000,5000,100), 
                        colors='white', linewidths=0.5)
        plt.tricontour(X, Y, elevations, np.arange(-5000,5000,500), 
                        colors='white', linewidths=1)
        # symbol
        for key, tup in TOPO_MAP_SYMBOL.items():
            plt.plot(tup[0], tup[1], marker='o', markersize=1, color='black')
            # plt.annotate(key, xy=tup, xytext=(tup[0], tup[1]+500), 
            #     arrowprops=dict(facecolor='black', width=0.5, headwidth=2, headlength=2, shrink=0.05))
        
        # invert y axis
        lim = plt.ylim()    
        plt.ylim((lim[1],lim[0]))
        plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_TOPO}.{fex}"))
        plt.close()
    
    # geo_topo.slice_plot(line=angle, variable=np.log10(variable_permeability), 
    #                     colourmap=CMAP_PERMEABILITY, plt=plt)
    # if not open_viewer:
    #     plt.savefig(os.path.join(ini.t2FileDirFp, f"permeability_slice-{angle}."+fex))
    #     plt.close()
    
    # geo_topo.slice_plot(line=angle, variable=np.log10(variable_resistivity), 
    #                     colourmap=CMAP_RESISTIVITY, plt=plt,
    #                     colourbar_limits=CBAR_LIM_LOG10RES)
    # if not open_viewer:
    #     plt.savefig(os.path.join(ini.t2FileDirFp, f"resistivity_slice-{angle}."+fex))
    #     plt.close()

def visualize_layer(ini:_readConfig.InputIni,
                    geo_topo: mulgrid,
                    variable_resistivity: np.array,
                    variable_permeability: np.array,
                    fex='pdf',
                    open_viewer=False,
                    plot_all_layers=False,
                    layer_no_to_plot=None ):
    """_summary_

    Args:
        ini (_readConfig.InputIni): _description_
        geo_topo (mulgrid): _description_
        variable_resistivity (np.array): loaded array of (ini.savefigFp)/(PICKLED_MULGRID_PERM)
        variable_permeability (np.array): loaded array of (ini.savefigFp)/(PICKLED_MULGRID_RES)
        fex (str, optional): extention of created figures. Defaults to 'pdf'.
        open_viewer (bool, optional): 
            If True, open window viewing figures, insted of saving image. Defaults to True.
        plot_all_layers(bool, optional):
            If True, create horizontal slice for all layers.
        layer_no_to_plot (str, optional):
            If not none, a horizontal slice of specified index is created.
    """
    if open_viewer:
        # open viewer
        plt = None
    else:
        # save image insted of opening viewer
        import matplotlib.pyplot as plt
        plt.rcParams["font.size"] = FONT_SIZE
    
    # plot for all layer
    if plot_all_layers:
        for layer in geo_topo.layer:
            geo_topo.layer_plot(layer=layer, 
                                variable=np.log10(variable_permeability),
                                variable_name='log10 permeability',
                                colourmap=CMAP_PERMEABILITY, 
                                plt=plt, 
                                column_names=True,
                                colourbar_limits=CBAR_LIM_LOG10PERM,
                                xlabel = 'Northing (m)', 
                                ylabel = 'Easting (m)',)
            if not open_viewer:
                # invert y axis
                lim = plt.ylim()    
                plt.ylim((lim[1],lim[0]))
                plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_PERM_LAYER}{layer.replace(' ', '_')}.{fex}"))
                plt.close()
            geo_topo.layer_plot(layer=layer, 
                                variable=np.log10(variable_resistivity),
                                variable_name='log10 resistivity',
                                colourmap=CMAP_RESISTIVITY, 
                                plt=plt,
                                colourbar_limits=CBAR_LIM_LOG10RES,
                                column_names=True,
                                xlabel = 'Northing (m)', 
                                ylabel = 'Easting (m)',)
            if not open_viewer:
                # invert y axis
                lim = plt.ylim()    
                plt.ylim((lim[1],lim[0]))
                plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_RESIS_LAYER}{layer.replace(' ', '_')}.{fex}"))
                plt.close()
    
    if layer_no_to_plot is not None:
        for layer in geo_topo.layer:
            # if layer_no_to_plot != int(layer): continue
            if layer_no_to_plot != layer: continue
            geo_topo.layer_plot(layer=layer, 
                                variable=np.log10(variable_permeability),
                                variable_name='log10 permeability',
                                colourmap=CMAP_PERMEABILITY, 
                                plt=plt, 
                                column_names=True,
                                colourbar_limits=CBAR_LIM_LOG10PERM,
                                xlabel = 'Northing (m)', 
                                ylabel = 'Easting (m)',)
            if not open_viewer:
                # invert y axis
                lim = plt.ylim()    
                plt.ylim((lim[1],lim[0]))
                plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_PERM_LAYER}{layer.replace(' ', '_')}.{fex}"))
                plt.close()
            geo_topo.layer_plot(layer=layer, 
                                variable=np.log10(variable_resistivity),
                                variable_name='log10 resistivity',
                                colourmap=CMAP_RESISTIVITY, 
                                plt=plt,
                                colourbar_limits=CBAR_LIM_LOG10RES,
                                column_names=True,
                                xlabel = 'Northing (m)', 
                                ylabel = 'Easting (m)',)
            if not open_viewer:
                # invert y axis
                lim = plt.ylim()    
                plt.ylim((lim[1],lim[0]))
                plt.savefig(os.path.join(ini.t2FileDirFp, f"{IMG_RESIS_LAYER}{layer.replace(' ', '_')}.{fex}"))
                plt.close()



def get_outer_boundary_blocks(geo:mulgrid, grid:t2grid, convention:int):
    """
    At first, get the columns of the outer boundary.
    Then, get the list of blocks that consist of the outer boundary
    Args:
        geo (mulgrid): [description]
        grid (t2grid): [description]
        convention (int): [description]

    Returns:
        [list], [list]: 
            list of t2block belonging to outer side edge of computational domain, 
            list of area of surface belonging to outer side edge of computational domain for each block
    """
    # list of mulgrids.node belong to outer side edge of computational domain
    boundnodes = geo.column_boundary_nodes(geo.columnlist)
    print("boundary nodes:")
    print(boundnodes)
    # list of mulgrids.column belong to outer side edge of computational domain
    boundcols = []
    for node in boundnodes:
        for col in node.column:
            if col not in boundcols: boundcols.append(col)
    print("boundary columns:")
    print(boundcols)
    # list of col edge length shared by the boundary of computational domain
    boundcol_edge_lengthes = get_col_outer_edge_length(boundcols, boundnodes)
    
    # outer boundaryのブロックのリストを取得
    blocklist = []
    # 計算領域の外側に接する面積も各blkごとに取得
    blk_surf_area_on_bound = []
    for col, len in zip(boundcols, boundcol_edge_lengthes):
        # columnごとに地表面標高を取得
        layer_top_elev = geo.column_surface_layer(col).centre
        for lay in geo.layerlist:
            if lay.centre > layer_top_elev:
                # 地表より上のブロックはスキップ
                # print(f'{col.name:>3}{lay.name:>2} skip')
                continue
            elif lay.centre == layer_top_elev:
                lay_thick = lay.thickness - (lay.top-col.surface)
            elif lay.centre < layer_top_elev:
                lay_thick = lay.thickness

            blkname = blockname(col.name, lay.name, convention)
            # print(blkname)
            blocklist.append(grid.block[blkname])
            blk_surf_area_on_bound.append(len*lay_thick)

    return blocklist, blk_surf_area_on_bound


def get_col_outer_edge_length(boundcols, boundnodes):
    """
    For the columns located at the periphery of the computational domain, 
    obtain the length of the part of each column that touches the periphery.
    (計算領域の外周部に位置するcolumnについて、それぞれのcolumnが外周部に接する長さを取得.)
    Args:
        boundcols ([list of mulgrids.column]): 
            columns at the periphery of the computational domain
        boundnodes ([list of mulgrids.node]): 
            nodes at the periphery of the computational domain
    
    Returns:
        [list of float]: length of column boundary shared by outer edge
    """
    lengthes_shared_by_outer_edge = []
    for col in boundcols:
        # 各columnについて計算領域境界に属するnode(積集合を求める)
        boundnodes_on_col = set(col.node) & set(boundnodes)
        if len(boundnodes_on_col)>3:
            print(f"the number of nodes on the edge of computational domain exceeds 3. why? (column:{col})")
            print(f"計算領域が長方形じゃないようなのでもう無理です")
            sys.exit()
        x = []
        y = []
        for bnc in boundnodes_on_col:
            x.append(bnc.pos[0])
            y.append(bnc.pos[1])
        lengthes_shared_by_outer_edge.append(((max(x)-min(x))**2+(max(y)-min(y))**2)**0.5)
    return lengthes_shared_by_outer_edge

# def num_convert_to_blkname_3digit(num):
#     arr=["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z",1,2,3,4,5,6,7,8,9]
#     n=len(arr)
#     if num>=n**3:
#         sys.exit("overflow")
#     elif n**3 > num >= n**2:
#         return f"{arr[num//n**2-1]}{arr[(num%n**2)//n**1-1]}{arr[((num%n**2)%n**1)-1]}"
#     elif n**2 > num >= n**1:
#         return f" {arr[(num%n**2)//n**1-1]}{arr[((num%n**2)%n**1)-1]}"
#     elif n**1 > num >= n**0:
#         return f"  {arr[((num%n**2)%n**1)-1]}"

def kill_connections_betw_boundary_blks(geo:mulgrid, grid:t2grid, convention:int):
    # list of mulgrids.node belong to outer side edge of computational domain
    boundnodes = geo.column_boundary_nodes(geo.columnlist)
    # list of mulgrids.column belong to outer side edge of computational domain
    boundcols = []
    for node in boundnodes:
        for col in node.column:
            if col not in boundcols: boundcols.append(col)
    for col in boundcols:
        # delete lateral connection
        for neighcol in col.neighbour & set(boundcols):
            for lay in geo.layerlist:
                conname1 = (blockname(col.name, lay.name, convention),
                            blockname(neighcol.name, lay.name, convention))
                conname2 = (blockname(neighcol.name, lay.name, convention),
                            blockname(col.name, lay.name, convention))
                if conname1 in grid.connection:
                    grid.delete_connection(conname1)
                elif conname2 in grid.connection:
                    grid.delete_connection(conname2)

        # delete vertical connection
        for lay1 in geo.layerlist:
            for lay2 in geo.layerlist:
                conname1 = (blockname(col.name, lay1.name, convention),
                            blockname(col.name, lay2.name, convention))
                conname2 = (blockname(col.name, lay2.name, convention),
                            blockname(col.name, lay1.name, convention))
                if conname1 in grid.connection:
                    grid.delete_connection(conname1)
                elif conname2 in grid.connection:
                    grid.delete_connection(conname2)
        
        # delete connections to atmosphere block
        if geo.atmosphere_type == 0 or geo.atmosphere_type == 1:
            if len(grid.atmosphere_blocks)==0:
                print(f"""atmosphere_type={geo.atmosphere_type}. But, no atmosphere block found in dat.grid. Exit""")
            for atmblk in grid.atmosphere_blocks:
                for lay in geo.layerlist:
                    conname1 = (blockname(col.name, lay.name, convention),
                                atmblk.name)
                    conname2 = (atmblk.name,
                                blockname(col.name, lay.name, convention))
                    if conname1 in grid.connection:
                        grid.delete_connection(conname1)
                    elif conname2 in grid.connection:
                        grid.delete_connection(conname2)


def blockname(colname, layname, convention):
    if convention == 0:
        blkname = f'{colname:>3}{layname:>2}'
    elif convention == 1:
        blkname = f'{layname:>3}{colname:>2}'
    elif convention == 2:
        blkname = f'{layname:>2}{colname:>3}'
    return blkname


def load_topo_file(topofile_fp):
    # create or load resistivity interpolating function 
    pickledtopo = topofile_fp+"_pickled"
    if os.path.isfile(pickledtopo):
        print(f"load pickled interpolating function: {pickledtopo}")
        # load selialized interpolating function
        with open(pickledtopo, 'rb') as f:
            interp = pickle.load(f)   
    else:
        print(f"create interpolating function and pickle: {pickledtopo}")
        # read data file
        df = pd.read_csv(topofile_fp, delim_whitespace=True)
        x = np.array(df['x']) * M_OVER_KM # km to m
        y = np.array(df['y']) * M_OVER_KM # km to m
        z = np.array(df['z']) * M_OVER_KM # km to m
        # interpolating function
        interp = LinearNDInterpolator(list(zip(x,y)), z)
        # serialize and save
        with open(pickledtopo, 'wb') as f:
            pickle.dump(interp, f)
    return interp




if __name__ == "__main__":
    main()