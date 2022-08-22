from http.client import TOO_MANY_REQUESTS
import os
import sys
import numpy as np
import itertools

# get directory name where this script is located
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
sys.path.append(baseDir)

### Here, please set file path 
# BASE FILE (.ini-format file)
base = "iniSample/input_radial_converged_eco2n.ini"
# INI OUTPUT (the directory where newly created .ini file to be saved)
saveDir = "iniSample/bf_input_radial_converged_eco2n/input"
# RESULT OUTPUT (the directory where result directory of newly created .ini file will be created)
TOUGH_INPUT_DIR = "iniSample/bf_input_radial_converged_eco2n/result"
### 

# reading setting.ini 
import _readConfig
ini = _readConfig.InputIni().read_from_inifile(base)

try:
    os.makedirs(saveDir)
except FileExistsError:
    sys.exit(f"directory: {saveDir} exists")
try:
    os.makedirs(TOUGH_INPUT_DIR)
except FileExistsError:
    sys.exit(f"directory: {TOUGH_INPUT_DIR} exists")

### Here, please prepare ingredients 
gener1_flux = 10**np.linspace(-2,1.2,6)
gener2_flux = 10**np.linspace(-2,1.5,6)
### 

### Here, design the setting values to the configparser.ConfigParser object. 
# please change the followings
for tupl in itertools.product(gener1_flux, gener2_flux):
    
    # define a unique name for each problem, and set
    ini.config.set('toughInput', 'problemName', f"{tupl[0]:.2f}_{tupl[1]:.2f}")
    # other parameters
    ini.config.set('gener1', 'flux', str(tupl[0]))
    ini.config.set('gener2', 'flux', str(tupl[1]))
###

    # set save  directory (No changes required)
    ini.config.set('configuration', 'TOUGH_INPUT_DIR', TOUGH_INPUT_DIR)
    # write as new .ini-format file (No changes required)
    savefp = os.path.join(saveDir, ini.config['toughInput']['problemName'] + ".ini")
    with open(savefp, 'w') as configfile:
        ini.config.write(configfile)


