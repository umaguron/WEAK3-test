from import_pytough_modules import *
from mulgrids import *
from t2data import *
import os 
import math
import _readConfig
import shutil
import makeGridFunc
import makeGridAmeshVoro

#######
## get argument
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("inputIni", 
        help="fullpath of toughInput setting input.ini", type=str)
parser.add_argument("-fa","--force_overwrite_all", 
        help="if given, recreate all existing grid and input file", action='store_true')
parser.add_argument("-view","--open_viewer", 
        help="if given, open window viewing figures, insted of saving image", action='store_true')
parser.add_argument("-f","--force_overwrite_t2data", 
        help="(Only valid for type: A_VORO) if given, use existing mulgrid file and overwrite existing t2data file", action='store_true')
parser.add_argument("-all","--plot_all_layers", 
        help="(Only valid for type: A_VORO) if given, saving figures for all layers", action='store_true')
parser.add_argument("-layer","--layer", 
        help="(Only valid for type: A_VORO) if the layer number 'LAYER' is given, saving a figure of the specified layer", type=int)
args = parser.parse_args()
## get directory name where this script is located
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
## read inputIni ##
ini = _readConfig.InputIni().read_from_inifile(args.inputIni)

if ini.mesh.type == REGULAR:
    
    if os.path.isfile(ini.t2GridFp) and not args.force_overwrite_all:
        print(f"t2Grid file : {ini.t2GridFp} exists")
        sys.exit(f"    add option -fa to force overwrite")

    makeGridFunc.makeGridRegular(ini, 
                                overWrites=args.force_overwrite_all, 
                                showsProfiles=args.open_viewer)

elif ini.mesh.type == AMESH_VORONOI:
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
    
    makeGridAmeshVoro.makePermVariableVoronoiGrid(ini, 
                                force_overwrite_all=args.force_overwrite_all,
                                open_viewer=args.open_viewer,
                                plot_all_layers=args.plot_all_layers,
                                layer_no_to_plot=args.layer)
