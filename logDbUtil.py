from import_pytough_modules import *
#
import sqlite3
import pandas as pd
import shlex, subprocess, sys
from time import sleep
import _readConfig
import os 
import re
from t2listing import *
import logDbAccess
import t2outUtil
from define import *
# get directory name where this script is located
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()

def addResultToLog(inputIni:str, toughResultDir:str=None):
    """[summary]

    Args:
        inputIni (str): 
            path of input.ini, which is used for create 
            TOUGH input files (t2data, mulgrid, INCON etc.)  
        toughResultDir (str, optional): 
            relative path of the directory from baseDir includes 
            t2data.dat, output.linsting etc.
            If dirResult is not given, use default t2dir 
            (read from input.ini and related setting.ini)
    """
    ## read inputIni ##
    try:
        _rii = _readConfig.InputIni().read_from_inifile(inputIni)
        II = _rii.toughInput
    except Exception as e:
        print(f"ERROR in reading inputIni: {inputIni}")
        raise e    

    # if dirResult is not given, restore t2dir path from info provided by the ini files
    if toughResultDir is None:
        toughResultDir = os.path.join(_rii.setting.toughConfig.TOUGH_INPUT_DIR, 
                                      _rii.toughInput['problemName'])
        # check existence
        if not os.path.exists(toughResultDir):
            print(f"TOUGH RESULT DIR: {toughResultDir} does not exist")
            raise FileNotFoundError
    
    try:
        conn = sqlite3.connect(os.path.join(baseDir, LOG_DB_PATH))
        """ update table toughInput"""
        lastrowid = logDbAccess.insertToughInput(
            conn, _rii, dirResult=toughResultDir, overWrites=True)

        """ update table toughresult"""
        c = conn.cursor()
        # get toughinput_id of last inserted record 
        sql = f"select toughInput_id from toughInput where rowid = {lastrowid}"
        c.execute(sql)
        toughInput_id = c.fetchone()[0]

        # read TOUGH output file
        # with open(os.path.join(toughResultDir, 
        #             II['toughOutputFileName']),'r') as f:
        #     pass
        # lst = t2listing(os.path.join(toughResultDir,II['toughOutputFileName']))
        # lst.last()

        # time_steps = lst.step
        # total_time = lst.time
        alltimesteps = t2outUtil.readAllTimestepsFromFOFT(_rii)
        time_steps = len(alltimesteps)
        total_time = alltimesteps[-1]
        dt_last = alltimesteps[-1]-alltimesteps[-2] if len(alltimesteps) >=2 else "NULL"
        if II['simulator']=='TOUGH3':
            temp = 'TEMP'
            pres = 'PRES'
            label_heat = 'heat'
            label_flow_l = 'flow_l'
            label_flow_g = 'flow_g'
            label_flow ='flow'
        if II['simulator']=='TOUGH2':
            temp = 'T'
            pres = 'P'
            label_heat = 'floh'
            label_flow_l = 'flo(aq'
            label_flow_g = 'flo(gas'
            label_flow ='flof'
        # convergence_temp = repr(lst.convergence[temp])
        # convergence_pres = repr(lst.convergence[pres])

        # get elapsed time
        with open(_rii.tOutFileFp, "r") as f:
            e_time = 0
            endflg = False
            status = 9 # calculation is running or was aborted
            for line in f:
                if re.search(CONSECUTIVE_10, line):
                    status=10
                if re.search(FOLLOWING_TWO, line):
                    status=42
                if re.search(NO_CONVERGENCE, line):
                    status=26
                if re.search(SIM_END, line):
                    endflg = True
                if line.lower().startswith('elapsed time'):
                    e_time = re.sub('[ ]*SEC\n','',re.sub('^.*=[ ]+','', line))
                    # status = 2 # calculation ended propely
            if endflg and not (status in [10, 42, 26]):
                status = 5
            if not endflg:
                status = 9 # calculation is running or was aborted
        
        # get surface budget
        # df_conn = lst.connection.DataFrame
        # read from OUTPUT_CONNE.csv (not from output.listing) 
        df_conn, time, label, unit = t2outUtil.read_output_conne_csv(_rii) 
        budget = t2outUtil.dfGetSurfaceBudget(df_conn[-1])
        s_heat = None
        s_flow = None
        s_flow_l = None
        s_flow_g = None
        for variable in list(budget.index):
            if label_heat in variable.lower(): s_heat = budget[variable]
            elif label_flow_l in variable.lower(): s_flow_l = budget[variable]
            elif label_flow_g in variable.lower(): s_flow_g = budget[variable]
            elif label_flow in variable.lower(): s_flow = budget[variable]

        print(f"[toughresult] inserting or replacing new record ...")
        sql = f"""
        INSERT OR REPLACE INTO toughresult(
            toughinput_id, time_steps, total_time, 
            status, elapsed_time,
            updated_time, surface_heat, surface_flow, surface_flow_l, 
            surface_flow_g, last_timestep_length  
        ) VALUES(
            {toughInput_id}, {time_steps}, {total_time}, 
            {status}, {e_time},
            datetime('now','localtime'), 
            {s_heat}, {s_flow}, {s_flow_l}, {s_flow_g}, {dt_last} 
        )"""
        c.execute(sql)
        
        # crose cursor
        c.close()
        conn.commit()
        print("[logDbUtil] committed")
    except Exception as e:
        conn.rollback()
        print("[logDbUtil] rollback")
        raise e
    conn.close()
