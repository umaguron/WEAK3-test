import os
import sys
import configparser
import json
import _readConfig
from define import *
import argparse
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("inputIni", 
            help="fullpath of toughInput setting input.ini", type=str)
parser.add_argument("-p","--parallel", 
            help="overwrite existing t2data file", type=int)
args = parser.parse_args()
# get directory name where this script is located
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
## read inputIni ##
_rii = _readConfig.InputIni().read_from_inifile(args.inputIni)
II = _rii.toughInput
if not os.path.isfile(_rii.t2FileFp):
    print(f"TOUGH inputfile {_rii.t2FileFp} not found")
if not os.path.isfile(_rii.setting.toughexec.COMM_EXEC):
    print(f"TOUGH executable {_rii.setting.toughexec.COMM_EXEC} not found")

if args.parallel is not None:
    # if the number of processor at parallel execution is specified by argument
    execParallel = True
    nProc = args.parallel
    print(f"PARALLEL (n_proc = {nProc})")
if args.parallel is None:
    # if the number of processor at parallel execution is not specified by argument
    if _rii.solver.matslv==8:
        # if solver type (matslv) specified in input file = 8 (PETSc solver)
        execParallel = True
        nProc = _rii.solver.nProc
        print(f"PARALLEL (n_proc = {nProc})")
    else:
        # solver type other than 
        # serial
        execParallel = False        
        print(f"SERIAL (solver type = {_rii.solver.matslv})")

# output .petscrc for parallel execution
if execParallel:
    from pathlib import Path
    try: 
        # clean at first
        os.remove(os.path.join(Path.home(),".petscrc"))
    except: 
        pass    
    # only if PETSc solver setting found in inputIni, create new .petscrc file
    if _rii.solver.matslv == 8 \
        and (_rii.solver.ksp_type is not None \
            or _rii.solver.pc_type is not None \
            or _rii.solver.ksp_rtol is not None):
        rc = os.path.join(_rii.t2FileDirFp,'.petscrc')
        print(f'PETSc solver')
        with open(rc, 'w') as f:
            if _rii.solver.ksp_type is not None:
                f.write(f'-ksp_type {_rii.solver.ksp_type}\n')
                print(f'   -ksp_type {_rii.solver.ksp_type}')
            if _rii.solver.pc_type is not None:
                f.write(f'-pc_type {_rii.solver.pc_type}\n')
                print(f'   -pc_type {_rii.solver.pc_type}')
            if _rii.solver.ksp_rtol is not None:
                f.write(f'-ksp_rtol {_rii.solver.ksp_rtol}\n')
                print(f'   -ksp_rtol {_rii.solver.ksp_rtol}')
        shutil.copy2(rc, Path.home())

""" execute """
os.chdir(_rii.t2FileDirFp)
# load module
# execute
print(f"simulator: {_rii.toughInput['simulator']}")
if _rii.toughInput['simulator']==SIMULATOR_NAME_T3:
    if execParallel:
        # mode parallel
        os.system(f"""
        module purge
        export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH
        mpiexec -n {nProc} {_rii.setting.toughexec.COMM_EXEC} {FILENAME_T2DATA} {FILENAME_TOUGH_OUTPUT}
        """)
    else:
        # mode serial 
        os.system(f"""
        module purge
        export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH
        {_rii.setting.toughexec.COMM_EXEC} {FILENAME_T2DATA} {FILENAME_TOUGH_OUTPUT}
        """)
if _rii.toughInput['simulator']==SIMULATOR_NAME_T2:
    print("SERIAL")
    os.system(f"""
    {_rii.setting.toughexec.COMM_EXEC} < {FILENAME_T2DATA} | tee {FILENAME_TOUGH_OUTPUT}
    """)

