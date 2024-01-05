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
        help="(Only valid for type: A_VORO) if the layer index 'LAYER' (type: str) is given, saving a figure of the specified layer", type=str)
args = parser.parse_args()
## get directory name where this script is located
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
## read inputIni ##
ini = _readConfig.InputIni().read_from_inifile(args.inputIni)

makeGridFunc.makeGrid(
        ini=ini,
        force_overwrite_all=args.force_overwrite_all,
        open_viewer=args.open_viewer,
        force_overwrite_t2data=args.force_overwrite_t2data,
        plot_all_layers=args.plot_all_layers, 
        layer=args.layer
)

try: 
    shutil.copy2(ini.inputIniFp, ini.t2FileDirFp)
except shutil.SameFileError:
    pass