import sqlite3
# import pandas as pd
# import shlex, subprocess
import sys
# from time import sleep
import _readConfig
import os 
import re
import logDbUtil
# get directory name where this script is located
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
os.chdir(baseDir)

## get argument
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-ini", "--inputIni",
            help="for restoring single result,"\
                +" give fullpath of toughInput setting, input.ini", type=str)
parser.add_argument("-all","--updateAll", 
            help="""read multiple setting.ini defined in log_update_config.ini,
 and search all result of TOUGH_INPUT_DIR/*/*.ini and store result to DB.
 do not use with option -ini """, 
            action='store_true')
args = parser.parse_args()


if args.updateAll and args.inputIni is not None: 
    sys.exit("-h, --help:  show help message")
elif not args.updateAll and args.inputIni is None: 
    sys.exit("-h, --help:  show help message")
elif not args.updateAll and args.inputIni is not None: 
    """ restore single result """
    print(f"*** ini: {re.sub(str(baseDir.absolute()),'',args.inputIni)}")
    try:
        # resister to DB
        logDbUtil.addResultToLog(args.inputIni)
    except Exception as e:
        print(e)
        print("    ERROR in registering result to DB")
        raise

elif args.updateAll and args.inputIni is None: 
    """ restore multiple results """
    for ini in _readConfig.\
                logUpdateConfigIni("log_update_config.ini").settingIniList:
        try:
            si = _readConfig.SettingIni(ini)
        except FileNotFoundError:
            print(f"NOT FOUND: {ini}")
            continue
        ## define filepath
        # GRID_DIR_FP = os.path.join(baseDir, si.toughConfig.GRID_DIR)
        TOUGH_INPUT_DIR_FP = os.path.join(si.toughConfig.TOUGH_INPUT_DIR)
        """search TOUGH result from TOUGH_INPUT_DIR_FP and save result to log.db"""

        def dirIncludesIni(filepath:str):
            for f in os.scandir(filepath):
                if re.match(r".*\.ini$", f.name):
                    return True
        
        # list of fullpath of the directory includes t2data.dat, output.linsting etc.
        t2dataDirList = [os.path.join(TOUGH_INPUT_DIR_FP,f.name) 
            for f in os.scandir(TOUGH_INPUT_DIR_FP) 
            if f.is_dir() and 
            dirIncludesIni(os.path.join(TOUGH_INPUT_DIR_FP, f.name))]
        
        for dir in t2dataDirList:
            # search　and get the name of input file .ini
            ini = ""
            for f in os.scandir(dir):
                if re.match(r".*\.ini$", f.name): 
                    ini = os.path.join(dir, f.name)
            
            print(f"\n*** dir: {re.sub(str(baseDir.absolute()),'',dir)}")
            print(f"*** ini: {re.sub(dir+'/','',ini)}")
            
            try:
                # resister to DB
                logDbUtil.addResultToLog(ini,toughResultDir=dir)
            except Exception as e:
                print(e)
                print("    ERROR in registering result to DB")
                continue
