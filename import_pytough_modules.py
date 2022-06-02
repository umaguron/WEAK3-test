# get directory name where this script is located
import sys
import os 
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
sys.path.append(baseDir)
sys.path.append(os.path.join(baseDir,".."))
from define import *
try:
    sys.path.append(PYTOUGH_ROOT_PATH)
    sys.path.append(IAPWS_ROOT_PATH)
except:
    pass