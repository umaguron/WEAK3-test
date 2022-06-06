import sqlite3
import _readConfig
from define import *
import os, re, sys
import define_logging


def insertToughInput(conn: sqlite3.Connection, 
                    ini: _readConfig.InputIni,
                    dirResult:str,
                    overWrites:bool=True):
    """[summary]

    Args:
        conn (sqlite3.Connection): [description]
        ini (_readConfig.InputIni): [description]
        dirResult (str): value to be inserted to column toughinput.t2dir
        overWrites (bool, optional): [description]. Defaults to True.

    Returns:
        lastrowid: rowid of last updated record
    """
    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")

    II = ini.toughInput
    c = conn.cursor()

    t2dir = dirResult
    problemname = II['problemName']
    mesh = ini.mesh
    if mesh.type==REGULAR:
        if mesh.isRadial:
            num_element_axis1 = len(mesh.rblocks)
            num_element_axis2 = 1
            num_element_axis3 = len(mesh.zblocks)
        else:
            num_element_axis1 = len(mesh.xblocks)
            num_element_axis2 = len(mesh.yblocks)
            num_element_axis3 = len(mesh.zblocks)
    else:
        # A_VORO対応　応急処置
        num_element_axis1 = 0
        num_element_axis2 = 0
        num_element_axis3 = 0

    # 20210416 added column
    params = ['max_iterations', 'max_duration', 
            'texp', 'be', 'tstart', 'max_timestep', 
            'timestep_reduction', 'scale', 'relative_error', 
            'absolute_error', 'upstream_weight', 'newton_weight', 
            'derivative_increment', 'for', 'amres']
    
    # 20211019 added column
    solver_params = ['matslv','z_precond','o_precond','relative_max_iterations','closure',
                     'nProc','ksp_type','pc_type','ksp_rtol']
    
    # 20220603 detect parameter existence
    params2 = ['print_interval','max_timesteps','print_level','tstop',
               'const_timestep','gravity','MOPs01','MOPs02','MOPs03',
               'MOPs04','MOPs05','MOPs06','MOPs07','MOPs08','MOPs09',
               'MOPs10','MOPs11','MOPs12','MOPs13','MOPs14','MOPs15',
               'MOPs16','MOPs17']

    """ update table toughInput"""
    # search record and check exitence
    sql = f"""
    SELECT toughInput_id FROM toughInput 
    WHERE t2dir = '{t2dir}' AND problemname = '{problemname}'
    """
    c.execute(sql)
    result = c.fetchone()

    if result is None:
        print(f"[toughinput] inserting new record ...")
        # if record does not exists, insert as new record.
        col_str = f"""
                configIni,
                t2dir, 
                problemName, 
                updated_time,
                isRadial, 
                num_element_axis1,
                num_element_axis2,
                num_element_axis3,
                module ,
                num_components ,
                num_equations ,
                num_phases ,
                num_secondary_parameters ,
                PRIMARY_AIR ,
                PRIMARY_default ,
                problemNamePreviousRun ,
                rockSecList ,
                generSecList ,
                crustalHeatFlowRate ,
                rainfallAnnual_mm ,
                T_rain """
        value_str = f"""
                '{ini.configIniFp}', 
                '{t2dir}', 
                '{problemname}', 
                datetime('now','localtime'),
                '{mesh.type==REGULAR and mesh.isRadial}' ,
                {num_element_axis1} ,
                {num_element_axis2} ,
                {num_element_axis3} , 
                '{II['module']}' ,
                {II['num_components']} ,
                {II['num_equations']} ,
                {II['num_phases']} ,
                {II['num_secondary_parameters']} ,
                "{ini.atmosphere.PRIMARY_AIR}" ,
                "{II['PRIMARY_default']}" ,
                '{II['problemNamePreviousRun']}' ,
                "{II['rockSecList']}" ,
                "{II['generSecList']}" ,
                {II['crustalHeatFlowRate']} ,
                {II['rainfallAnnual_mm']}  ,
                {II['T_rain']}"""
        
        for param in params:
            if param in II and re.search(r"^[0-9eE.+-]+$",str(II[param])):
                col_str += f', {param}' 
                value_str += f", {II[param]}" 

        for sp in solver_params:
            if hasattr(ini.solver, sp):
                col_str += f', {sp}' 
                value_str += f", '{getattr(ini.solver, sp)}'" 

        for param in params2:
            if param in II and len(str(II[param]))>0 :
                col_str += f", {param}"
                value_str += f", {II[param]}"

        logger.debug('col_str  '+ repr(col_str))
        logger.debug('value_str  '+ repr(value_str))
        
        sql = f"INSERT INTO toughInput({col_str}) VALUES ({value_str})"  
    elif result is not None and overWrites:
        print(f"[toughinput] overwrite already existing "\
                +f"record (toughinput_id={result[0]})")
        # if record already exists, replace existence record
        col_str = f"""
                toughInput_id,
                configIni, 
                t2dir, 
                problemName, 
                updated_time,
                isRadial, 
                num_element_axis1,
                num_element_axis2,
                num_element_axis3,
                module ,
                num_components ,
                num_equations ,
                num_phases ,
                num_secondary_parameters ,
                PRIMARY_AIR ,
                PRIMARY_default ,
                problemNamePreviousRun ,
                rockSecList ,
                generSecList ,
                crustalHeatFlowRate ,
                rainfallAnnual_mm ,
                T_rain """

        value_str = f"""
                {result[0]}, 
                '{ini.configIniFp}', 
                '{t2dir}', 
                '{problemname}', 
                datetime('now','localtime'),
                '{mesh.type==REGULAR and mesh.isRadial}' ,
                {num_element_axis1} ,
                {num_element_axis2} ,
                {num_element_axis3} ,
                '{II['module']}' ,
                {II['num_components']} ,
                {II['num_equations']} ,
                {II['num_phases']} ,
                {II['num_secondary_parameters']} ,
                "{ini.atmosphere.PRIMARY_AIR}" ,
                "{II['PRIMARY_default']}" ,
                '{II['problemNamePreviousRun']}' ,
                "{II['rockSecList']}" ,
                "{II['generSecList']}" ,
                {II['crustalHeatFlowRate']} ,
                {II['rainfallAnnual_mm']}  ,
                {II['T_rain']}"""
        
        for param in params:
            if param in II and re.search(r"^[0-9eE.+-]+$",str(II[param])):
                col_str += f', {param}' 
                value_str += f", {II[param]}"  
                     
        for sp in solver_params:
            if hasattr(ini.solver, sp):
                col_str += f', {sp}' 
                value_str += f", '{getattr(ini.solver, sp)}'" 
        
        for param in params2:
            if param in II and len(str(II[param]))>0 :
                col_str += f", {param}"
                value_str += f", {II[param]}"

        logger.debug('col_str  '+ repr(col_str))
        logger.debug('value_str  '+ repr(value_str))

        sql = f"REPLACE INTO toughInput({col_str}) VALUES ({value_str})"  
    else:
        print(f"[toughinput] record (id: {result}) already exists, skip")
        raise Exception
    
    c.execute(sql)
    lastrowid = c.lastrowid

    if result is None:
        """ insert table ROCK (only at first time)"""
        print(f"[rock] inserting new record ...")
        # get toughinput_id of last inserted record 
        sql = f"select toughInput_id from toughInput where rowid = {lastrowid}"
        c.execute(sql)
        toughInput_id = c.fetchone()[0]
        for secRock in ini.rockSecList:
            
            if secRock.nad >= 2:
                nad2_col = ", IRP ,RP ,ICP ,CP "
                nad2_val = \
                    f""",{secRock.IRP},"{secRock.RP}",{secRock.ICP},"{secRock.CP}" """
            else:
                nad2_col = ""
                nad2_val = ""
            
            sql = f"""
            INSERT INTO rock(
                toughinput_id ,
                name ,
                nad ,
                density ,
                porosity ,
                permeability_x ,
                permeability_y ,
                permeability_z ,
                conductivity ,
                specific_heat ,
                regionSecList ,
                updated_time {nad2_col}

            ) VALUES (
                {toughInput_id},
                "{secRock.name}",
                {secRock.nad},
                {secRock.density},
                {secRock.porosity},
                {secRock.permeability_x},
                {secRock.permeability_y},
                {secRock.permeability_z},
                {secRock.conductivity},
                {secRock.specific_heat},
                "{secRock.regionSecList}",
                datetime('now','localtime') {nad2_val}
            ) """
            c.execute(sql)

            # """ update table region """
        
        """ insert table gener (only at first time)"""
        # for secGener in II['generSecList']:
        for secGener in ini.generSecList:
            print(f"[gener] inserting new record ...")
            # read property of gener from configuration file
            col_str = """
                        toughinput_id,
                        name ,
                        block ,
                        area ,
                        type ,
                        flux ,
                        vol_injblock ,
                        dist_injblock,
                        updated_time"""
            values_str = f"""
                        {toughInput_id},
                        "{secGener.name}",
                        "{secGener.block}",
                        "{secGener.area}",
                        "{secGener.type}",
                        {secGener.flux_sum},
                        "{secGener.vol_injblock}",
                        "{secGener.dist_injblock}",
                        datetime('now','localtime')"""
            if hasattr(secGener, "temperature"):
                col_str +=  ", temperature" 
                values_str += f", {secGener.temperature}"

            sql = f"INSERT INTO gener({col_str}) VALUES ({values_str})"  
            c.execute(sql)

    return lastrowid



# def insertToughResult(conn: sqlite3.Connection, 
#                       ini: _readConfig.InputIni,
#                       dirResult:str=None,
#                       overWrites:bool=True):
#     pass

