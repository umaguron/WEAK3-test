import configparser
import argparse
import pathlib, sys, os
baseDir = pathlib.Path(__file__).parent.resolve()
sys.path.append(os.path.join(baseDir,".."))
from define import *
import _readConfig
parser = argparse.ArgumentParser()
parser.add_argument("inputIni", 
            help="fullpath of toughInput setting input.ini", type=str)
args = parser.parse_args()
config = configparser.ConfigParser()
config.read(args.inputIni)
try:
    type = config['mesh']['type']
except:
    type = REGULAR
print(type)

