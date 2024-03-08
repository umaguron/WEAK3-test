import os
import sys
import configparser
import json
import _readConfig
from define import *
from define_path import *
import argparse
import shutil
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputIni", 
                help="fullpath of toughInput setting input.ini", type=str)
    parser.add_argument("-p","--parallel", 
                help="overwrite existing t2data file", type=int)
    args = parser.parse_args()
    _rii = _readConfig.InputIni().read_from_inifile(args.inputIni)
    execute(_rii, n_process_parallel=args.parallel)

def execute(ini:_readConfig.InputIni, n_process_parallel=None):
    # get directory name where this script is located
    ## read inputIni ##
    II = ini.toughInput
    if not os.path.isfile(ini.t2FileFp):
        print(f"TOUGH inputfile {ini.t2FileFp} not found")
    if not os.path.isfile(ini.configuration.COMM_EXEC):
        print(f"TOUGH executable {ini.configuration.COMM_EXEC} not found")

    if n_process_parallel is not None:
        # if the number of processor at parallel execution is specified by argument
        execParallel = True
        nProc = n_process_parallel
        print(f"PARALLEL (n_proc = {nProc})")
    if n_process_parallel is None:
        # if the number of processor at parallel execution is not specified by argument
        if ini.solver.matslv==8:
            # if solver type (matslv) specified in input file = 8 (PETSc solver)
            execParallel = True
            nProc = ini.solver.nProc
            print(f"PARALLEL (n_proc = {nProc})")
        else:
            # solver type other than 
            # serial
            execParallel = False        
            print(f"SERIAL (solver type = {ini.solver.matslv})")

    # output .petscrc for parallel execution
    if execParallel:
        from pathlib import Path
        try: 
            # clean at first
            os.remove(os.path.join(Path.home(),".petscrc"))
        except: 
            pass    
        # only if PETSc solver setting found in inputIni, create new .petscrc file
        if ini.solver.matslv == 8 \
            and (ini.solver.ksp_type is not None \
                or ini.solver.pc_type is not None \
                or ini.solver.ksp_rtol is not None):
            rc = os.path.join(ini.t2FileDirFp,'.petscrc')
            print(f'PETSc solver')
            with open(rc, 'w') as f:
                if ini.solver.ksp_type is not None:
                    f.write(f'-ksp_type {ini.solver.ksp_type}\n')
                    print(f'   -ksp_type {ini.solver.ksp_type}')
                if ini.solver.pc_type is not None:
                    f.write(f'-pc_type {ini.solver.pc_type}\n')
                    print(f'   -pc_type {ini.solver.pc_type}')
                if ini.solver.ksp_rtol is not None:
                    f.write(f'-ksp_rtol {ini.solver.ksp_rtol}\n')
                    print(f'   -ksp_rtol {ini.solver.ksp_rtol}')
            shutil.copy2(rc, Path.home())

    """ execute """
    os.chdir(ini.t2FileDirFp)
    # load module
    # execute
    print(f"simulator: {ini.toughInput['simulator']}")
    if ini.toughInput['simulator']==SIMULATOR_NAME_T3:
        if execParallel:
            # mode parallel
            os.system(f"""
            {COMM_BF_EXEC}
            {MPIEXEC} -n {nProc} {ini.configuration.COMM_EXEC} {FILENAME_T2DATA} {FILENAME_TOUGH_OUTPUT}
            """)
        else:
            # mode serial 
            os.system(f"""
            {COMM_BF_EXEC}
            {ini.configuration.COMM_EXEC} {FILENAME_T2DATA} {FILENAME_TOUGH_OUTPUT}
            """)
    if ini.toughInput['simulator']==SIMULATOR_NAME_T2:
        print("SERIAL")
        os.system(f"""
        {ini.configuration.COMM_EXEC} < {FILENAME_T2DATA} | tee {FILENAME_TOUGH_OUTPUT}
        """)


if __name__ == "__main__":
    main()