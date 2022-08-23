import os
import sys
import numpy as np
import itertools
import re

"""
このスクリプトと同じ階層に位置するini-formatファイル(ファイル名:"baseIniFileName")が読み込まれる。
作成されたiniファイルは、このスクリプトと同じ階層に作成したフォルダ"inputDirName"内に書き出される。
作成されたiniファイルのTOUGH_INPUT_DIRは、このスクリプトと同じ階層に作成したフォルダ"resultDirName"になる
このスクリプトは実行場所に依存しない。
"""

######## SETTING #########
prjRoot = '/.../WEAK3-test/' # プロジェクトルートのフルパスを書く
resultDirName = 'result/'
inputDirName = 'input/'
baseIniFileName = 'base.ini'
##########################

sys.path.append(prjRoot)
getpath = lambda str : re.sub(prjRoot, '', str)

# get directory name where this script is located
baseDir = os.path.dirname(__file__)
baseDirFpAbs = os.path.abspath(baseDir)
resultDirFpAbs = os.path.join(baseDirFpAbs,resultDirName)
inputDirFpAbs = os.path.join(baseDirFpAbs,inputDirName)
settingIniFpAbs = os.path.join(baseDirFpAbs, "setting.ini")

## reading setting.ini ##
import _readConfig
ini = _readConfig.InputIni().read_from_inifile(os.path.join(baseDirFpAbs, "base.ini"))

# save directory
try:
    os.makedirs(inputDirFpAbs)
except FileExistsError:
    sys.exit(f"directory: {inputDirFpAbs} exists")
try:
    os.makedirs(resultDirFpAbs)
except FileExistsError:
    pass

### Here, please prepare ingredients 
gener1_flux = 10**np.linspace(-2,1.2,6)
gener2_flux = 10**np.linspace(-2,1.5,6)
### 

### Here, design the setting values to the configparser.ConfigParser object. 
# please change the followings
for tupl in itertools.product(gener1_flux, gener2_flux):
    
    # define a unique name for each problem, and set
    ini.config.set('toughInput', 'problemName', f"g1flux-{tupl[0]:.2f}_g2flux-{tupl[1]:.2f}")
    # other parameters
    ini.config.set('gener1', 'flux', str(tupl[0]))
    ini.config.set('gener2', 'flux', str(tupl[1]))
###

    # set save  directory (No changes required)
    ini.config.set('configuration', 'TOUGH_INPUT_DIR', getpath(resultDirFpAbs))
    # write as new .ini-format file (No changes required)
    savefp = os.path.join(inputDirFpAbs, ini.config['toughInput']['problemName'] + ".ini")
    with open(savefp, 'w') as configfile:
        ini.config.write(configfile)

