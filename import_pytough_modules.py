# get directory name where this script is located
import sys
import os 
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
sys.path.append(baseDir)
sys.path.append(os.path.join(baseDir,".."))
from define import *
from define_path import *
try:
    sys.path.insert(0, os.path.join(baseDir, PYTOUGH_ROOT_PATH))
    sys.path.insert(0, os.path.join(baseDir, IAPWS_ROOT_PATH))
except:
    pass