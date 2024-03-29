#-------------------------------------------------------------------------------
from import_pytough_modules import *
#
from mulgrids import *
from pytough_override import t2dataSub
from t2data import *
from t2incons import *
from t2listing import *
from t2thermo import *
import math
import _readConfig
import shutil
import copy
import dill as pickle
import define_logging
import re
# get directory name where this script is located
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
import makeGridAmeshVoro as mgav


def main():
    ## get argument
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("inputIni", 
                help="fullpath of toughInput setting input.ini", type=str)
    parser.add_argument("-f","--force_overwrite", 
                help="overwrite existing t2data file", action='store_true')
    args = parser.parse_args()
    ## read inputIni ##
    ini = _readConfig.InputIni().read_from_inifile(args.inputIni)
    ini.rocktypeDuplicateCheck()
    # create save dir. 
    os.makedirs(ini.t2FileDirFp, exist_ok=True)
    if os.path.isfile(ini.t2FileFp) and not args.force_overwrite:
        print(f"[tough3exec] t2File: {ini.t2FileFp} exists")
        print(f"    add option -f to force overwrite")
        sys.exit()
    
    # main
    print("---- INTO makeToughInput() ----")
    makeToughInput(ini)
    print("---- END makeToughInput() ----")

    try:
        shutil.copy2(ini.inputIniFp, ini.t2FileDirFp)
    except shutil.SameFileError as e:
        print(e)
        print("skip")
    

def makeToughInput(ini:_readConfig.InputIni):

    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")
    
    ## import sea water property
    if hasattr(ini, 'sea'):
        import seawater_property 

    II = ini.toughInput
    ## create t2data, t2grid object
    # read mulgrid file
    print(f" read mulgrid: {ini.mulgridFileFp}")
    if not os.path.isfile(ini.mulgridFileFp):
        sys.exit(f"mulgrid file not found: {ini.mulgridFileFp}")
    geo = mulgrid(ini.mulgridFileFp)
    dat = t2dataSub()
    if os.path.isfile(ini.t2GridFp):
        # read existing t2grid data file:
        datG = t2dataSub(ini.t2GridFp)
        print(f"[tough3exec] read existing t2grid file: {ini.t2GridFp}")
        if datG.grid is None:
            # if t2file have not been created yet
            sys.exit(f"t2grid have not been created in: {ini.t2GridFp}")
        # Append .atmosphere = True manually
        # because the attribute 'atmosphere' is not appended to t2block 'ATM 0' without using t2grid().fromgeo()
        datG.grid.block[
                geo.block_name(geo.layerlist[0].name,geo.atmosphere_column_name)
            ].atmosphere = ini.atmosphere.includesAtmos
        dat.grid = datG.grid
    else:
        # create t2grid newly from mulgrid file 
        dat.filename = ini.t2FileFp
        dat.title = II['problemName']
        dat.grid = t2grid().fromgeo(geo)

    ## ROCKS ##
    print("*** ROCKS")
    # define the rocktype for injection blocks
    inj = copy.deepcopy(dat.grid.rocktype['dfalt'])
    # give huge specific heat to keep constant temperature
    inj.name = "INJCT"
    inj.specific_heat = HUGE_SPECIFIC_HEAT
    # add the rocktype for injection blocks
    dat.grid.add_rocktype(inj)

    isRocktypeEmpty = len(dat.grid.rocktypelist) <= 1
    if isRocktypeEmpty: raise Exception
    """ 古い実装なので一時コメントアウト
        # add rocktype read from configuration file
        for secRock in ini.rockSecList:
            permeability = [secRock.permeability_x,
                            secRock.permeability_y,
                            secRock.permeability_z]
            rock = rocktype(name = secRock.name, nad = secRock.nad, 
                    density = secRock.density, 
                    porosity = secRock.porosity, permeability = permeability, 
                    conductivity = secRock.conductivity, 
                    specific_heat = secRock.specific_heat)
            if secRock.nad >= 2:
                rock.relative_permeability = {'parameters':secRock.RP, 'type':secRock.IRP}
                rock.capillarity = {'parameters':secRock.CP, 'type':secRock.ICP}
            # set rocktype to grid
            dat.grid.add_rocktype(rock)

            for secReg in secRock.regionSecList:
                # apply rock type to the region
                count = 0
                for blk in dat.grid.blocklist:
                    if not blk.atmosphere:
                        if secReg.xmin <= blk.centre[0] < secReg.xmax \
                            and secReg.ymin <= blk.centre[1] < secReg.ymax \
                            and secReg.zmin <= blk.centre[2] < secReg.zmax :
                            blk.rocktype = rock
                            count += 1
                print(f"ROCK: {secRock.secName}\tREGION:"\
                    +f" {secReg.secName}\tnCELLS: {count}")
        
        if ini.atmosphere.includesAtmos:
            # set atomosphere
            dat.grid.add_rocktype(ini.atmosphere.atmos)
            # set to grid
            for blk in dat.grid.blocklist:
                if blk.atmosphere:
                    blk.rocktype = ini.atmosphere.atmos
    """        

    ## MULTI ## 
    print("*** MULTI")
    dat.multi = {
        'num_components': II['num_components'],
        'num_equations': II['num_equations'],
        'num_phases': II['num_phases'],
        'num_secondary_parameters': II['num_secondary_parameters']} 

    ## START ##
    """
    A Boolean property specifying whether 
    the flexible start option is used
    """
    dat.start = True


    ## PARAM ##
    print("*** PARAM")
    params = {'max_iterations','print_level','max_timesteps','max_duration',
            'print_interval', 'texp','be','tstart','tstop','const_timestep',
            'max_timestep','print_block','gravity','timestep_reduction',
            'scale','relative_error','absolute_error','upstream_weight',
            'newton_weight','derivative_increment','for','amres',}
    for param in params:
        if param in II:
            dat.parameter[param] = II[param]

    # PARAM1.MOP
    dat.parameter['option'][1] = II['MOPs01']
    dat.parameter['option'][2] = II['MOPs02']
    dat.parameter['option'][3] = II['MOPs03']
    dat.parameter['option'][4] = II['MOPs04']
    dat.parameter['option'][5] = II['MOPs05']
    dat.parameter['option'][6] = II['MOPs06']
    dat.parameter['option'][7] = II['MOPs07']
    dat.parameter['option'][8] = II['MOPs08']
    dat.parameter['option'][9] = II['MOPs09']
    dat.parameter['option'][10] = II['MOPs10'] 
    dat.parameter['option'][11] = II['MOPs11'] 
    dat.parameter['option'][12] = II['MOPs12'] 
    dat.parameter['option'][13] = II['MOPs13'] 
    # dat.parameter['option'][14] = II['MOPs14'] 
    dat.parameter['option'][15] = II['MOPs15'] 
    dat.parameter['option'][16] = II['MOPs16'] 
    dat.parameter['option'][17] = II['MOPs17'] 

    # PARAM.4
    # DEP(I)
    dat.parameter['default_incons'] = II['PRIMARY_default']




    # set short printout 
    # dat.parameter['print_block'] = ''

    ## INCON ##
    print("*** INCON")
    inc:t2incon = None

    # prepare
    if EOS2 == II['module'].strip().lower():
        ID_P = INCON_ID_EOS2_PRES
        ID_T = INCON_ID_EOS2_TEMP
        ID_Xs = [INCON_ID_EOS2_XCO2]
    if EOS3 == II['module'].strip().lower():
        ID_P = INCON_ID_EOS3_PRES
        ID_T = INCON_ID_EOS3_TEMP
        ID_Xs = [INCON_ID_EOS3_XAIR]
    if ECO2N in II['module'].strip().lower():
        ID_P = INCON_ID_ECO2N_PRES
        ID_T = INCON_ID_ECO2N_TEMP
        ID_XSAL = INCON_ID_ECO2N_XSAL
        ID_Xs = [INCON_ID_ECO2N_XSAL, INCON_ID_ECO2N_XCO2]
    if EWASG in II['module'].strip().lower():
        ID_P = INCON_ID_EWASG_PRES
        ID_T = INCON_ID_EWASG_TEMP
        ID_XSAL = INCON_ID_EWASG_XSAL
        ID_Xs = [INCON_ID_EWASG_XSAL, INCON_ID_EWASG_XNCG]
    G = II['gravity'] if 'gravity' in II else GRAV_ACCEL
    
    if II['use_1d_result_as_incon'] and len(II['problemNamePreviousRun']) == 0:
        ini1d = _readConfig.InputIni().read_from_inifile(II['1d_hydrostatic_sim_result_ini'])
        inc = dat.grid.incons()
        create_incon_from_1d_result(ini1d, ini, inc)

    elif len(II['problemNamePreviousRun']) == 0:
        # if no incon given
        # apply hydrostatic pressure as initial condition
        inc = dat.grid.incons()
        for blk in dat.grid.blocklist:
            if blk.atmosphere:
                continue
            else:
                
                if ini.toughInput['water_table_elevation'] is None:
                    # considering sea
                    if hasattr(ini, 'sea'):
                        h_sea = ini.sea.sea_level - suf_elev_t2block(blk, geo, ini.mesh.convention)
                        if h_sea > 0:
                            # sea area
                            P0 = seawater_property.FUNC_SEA_PRESSURE(h_sea) # including atmospheric pressure
                            T0 = seawater_property.FUNC_SEA_TEMP(h_sea)
                        else:
                            # land
                            P0 = ini.atmosphere.PRIMARY_AIR[ID_P] 
                            T0 = ini.atmosphere.PRIMARY_AIR[ID_T]
                    # no sea
                    else:
                        P0 = ini.atmosphere.PRIMARY_AIR[ID_P] 
                        T0 = ini.atmosphere.PRIMARY_AIR[ID_T]
                    
                    h = suf_elev_t2block(blk, geo, ini.mesh.convention) - blk.centre[2] \
                            if blk.centre is not None else 0.
                        
                    P = P0 + WATER_DENSITY * G * h
                    T = T0 + II['initial_t_grad'] / 1000 * h
                    var = [None for _ in range(len(ID_Xs+[ID_P,ID_T]))]
                    var[ID_P] = P
                    var[ID_T] = T
                    for id in ID_Xs:
                        var[id] = II['PRIMARY_default'][id]
                    inc[blk.name].variable = var

                else:
                    # TODO quantize may be required for ini.toughInput['water_table_elevation']

                    h_suf = suf_elev_t2block(blk, geo, ini.mesh.convention)
                    
                    # (1-1) no sea, above WT 
                    if not hasattr(ini, 'sea') \
                            and blk.centre[2] >= ini.toughInput['water_table_elevation']:
                        
                        inc[blk.name].variable = ini.atmosphere.PRIMARY_AIR
                    
                    # (2-1-1) considering sea, land area, above WT 
                    elif hasattr(ini, 'sea') \
                            and h_suf >= ini.sea.sea_level \
                            and blk.centre[2] >= ini.toughInput['water_table_elevation']:
                    
                        inc[blk.name].variable = ini.atmosphere.PRIMARY_AIR
                    
                    else:
                        # (1-2) no sea, below WT 
                        if not hasattr(ini, 'sea') \
                                and blk.centre[2] < ini.toughInput['water_table_elevation']:
                            
                            P0 = ini.atmosphere.PRIMARY_AIR[ID_P] 
                            T0 = ini.atmosphere.PRIMARY_AIR[ID_T]
                            h = min(ini.toughInput['water_table_elevation'], h_suf) - blk.centre[2]
                        
                        # (2-1-2) considering sea, land area, below WT 
                        elif hasattr(ini, 'sea') \
                                and h_suf >= ini.sea.sea_level \
                                and blk.centre[2] < ini.toughInput['water_table_elevation']:
                        
                            P0 = ini.atmosphere.PRIMARY_AIR[ID_P] 
                            T0 = ini.atmosphere.PRIMARY_AIR[ID_T]
                            h = min(ini.toughInput['water_table_elevation'], h_suf) - blk.centre[2]

                        # (2-2) considering sea, sea area (water_table_elevation not applied)
                        elif hasattr(ini, 'sea') and h_suf < ini.sea.sea_level:
                            # sea area
                            P0 = seawater_property.FUNC_SEA_PRESSURE(ini.sea.sea_level - h_suf) # including atmospheric pressure
                            T0 = seawater_property.FUNC_SEA_TEMP(ini.sea.sea_level - h_suf)
                            h = h_suf - blk.centre[2]
                
                        P = P0 + WATER_DENSITY * G * h
                        T = T0 + II['initial_t_grad'] / 1000 * h
                        var = [None for _ in range(len(ID_Xs+[ID_P,ID_T]))]
                        var[ID_P] = P
                        var[ID_T] = T
                        for id in ID_Xs:
                            var[id] = II['PRIMARY_default'][id]
                        inc[blk.name].variable = var
    
        print("[tough3exec] INCON created (hydrostatic)")
    else:
        # case use result of previous run as initial contion
        pnpr = os.path.join(baseDir, II['problemNamePreviousRun'], SAVE_FILE_NAME)
        previousRunResultFp = \
            os.path.join(baseDir, ini.configuration.TOUGH_INPUT_DIR, 
                                    II['problemNamePreviousRun'], SAVE_FILE_NAME)
        
        # if inputini.problemNamePreviousRun is arbitrary relative path of problemname including SAVE, 
        if os.path.isfile(pnpr): previousRunResultFp = pnpr
        # if inputini.problemNamePreviousRun is just problemname, search SAVE in TOUGH_INPUT_DIR  
        elif os.path.isfile(previousRunResultFp): pass
        else:
            # no SAVE found
            sys.exit("[tough3exec] ERROR: NO SAVE FILE FOUND")
        
        inc = t2incon(previousRunResultFp)
        print(f"\n[tough3exec] USE RESULT OF RUN: {II['problemNamePreviousRun']} AS INCON\n")

    ## atmosphere INCON
    if ini.atmosphere.includesAtmos: 
        inc[ATM_BLK_NAME(ini.mesh.convention)].variable = ini.atmosphere.PRIMARY_AIR

    ## manually setting INCON 
    # if 'specifies_variable_INCON' is True, 
    # the INCON created so far will be overwritten by primary variables specified in 
    #    p_sec.variables (section: p_sec.secName, key: 'variables' in ini-file).
    # The assignment is valid in the spatial range that satisfies the condition, 
    #    p_sec.assigning_condition. (section: p_sec.secName, key: 'assigning_condition' in ini-file).
    if II['specifies_variable_INCON']:
        print("\n[tough3exec] VARIABLE_INCON - overwrite default incon")

        # if mesh type is A_VORO, load resistivity interpolating function 
        if ini.mesh.type.upper().strip()==AMESH_VORONOI:
            pickledres = ini.mesh.resistivity_structure_fp+"_pickled"
            if os.path.isfile(pickledres):
                logger.debug(f"load pickled interpolating function: {pickledres}")
                # load selialized interpolating function
                with open(pickledres, 'rb') as f:
                    interpRes = pickle.load(f)  
            else:
                raise Exception(f"pickled interpolating function not found: {pickledres}")
        else:
            interpRes = None


        # apply primary variable to the region
        for p_sec in ini.primary_sec_list:
            print(f"*** PRIMARY REGION: {p_sec.secName}")
            count = 0
            for blk in dat.grid.blocklist:
                """
                skip atmosphere block
                """
                if blk.atmosphere:
                    continue
                """
                prepare variables, which are evaluated in judging assigning_condition
                """
                # blk position
                x = blk.centre[0]
                y = blk.centre[1]
                z = blk.centre[2]
                surface = geo.column[geo.column_name(blk.name)].surface
                depth = surface - z
                # properties of current rocktype
                phi = blk.rocktype.porosity
                k_x = blk.rocktype.permeability[0]
                k_y = blk.rocktype.permeability[1]
                k_z = blk.rocktype.permeability[2]
                # For each block, calc resistivity value at the center of the block 
                # by interpolation, 
                if interpRes is not None: rho = interpRes(blk.centre)[0]
                # judge current blk satisfies the p_sec assigning condition by evaluating given formula 
                applies = eval(p_sec.assigning_condition) 
                """
                If the property of the current block satisfies the p_sec assigning condition, or, 
                if current blk included in p_sec.blockList, 
                    assign primary variables of section p_sec to current blk
                """
                if applies or p_sec.isBlkInBlockList(blk):
                    for idx, value in enumerate(p_sec.variables):
                        if value is None:
                            # If the given value (p_sec.variables[idx]) is 'None', 
                            # INCON[idx] is not overwritten.
                            continue
                        elif idx==ID_P and KW_LITHOS in str(value).lower():
                            # if keyword 'lithos' found in p_sec.variables[ID_P],
                            # assigning lithostatic pressure.
                            inc[blk.name].variable[idx] = ini.atmosphere.PRIMARY_AIR[ID_P] + OVERBURDEN_DENSITY * G * depth
                        elif idx==ID_P and KW_HYDRST in str(value).lower():
                            # if keyword 'hydrst' found in p_sec.variables[ID_P],
                            # assigning hydrostatic pressure.
                            inc[blk.name].variable[idx] = ini.atmosphere.PRIMARY_AIR[ID_P] + WATER_DENSITY * G * depth
                        else:
                            inc[blk.name].variable[idx] = value
                    count += 1
                else:
                    continue   

            #     if not blk.atmosphere:
            #         if p_sec.xmin <= blk.centre[0] < p_sec.xmax \
            #             and p_sec.ymin <= blk.centre[1] < p_sec.ymax \
            #             and p_sec.zmin <= blk.centre[2] < p_sec.zmax :
            #             if  EOS2 == II['module'].strip().lower():
            #                 inc[blk.name].variable[INCON_ID_EOS2_TEMP] = p_sec.value[INCON_ID_EOS2_TEMP]
            #                 inc[blk.name].variable[INCON_ID_EOS2_XCO2] = p_sec.value[INCON_ID_EOS2_XCO2]
            #             if  EOS3 == II['module'].strip().lower():
            #                 inc[blk.name].variable[INCON_ID_EOS3_XAIR] = p_sec.value[INCON_ID_EOS3_XAIR]
            #                 inc[blk.name].variable[INCON_ID_EOS3_TEMP] = p_sec.value[INCON_ID_EOS3_TEMP]
            #             if  ECO2N in II['module'].strip().lower():    
            #                 inc[blk.name].variable[INCON_ID_ECO2N_XSAL] = p_sec.value[INCON_ID_ECO2N_XSAL]
            #                 inc[blk.name].variable[INCON_ID_ECO2N_XCO2] = p_sec.value[INCON_ID_ECO2N_XCO2]
            #                 inc[blk.name].variable[INCON_ID_ECO2N_TEMP] = p_sec.value[INCON_ID_ECO2N_TEMP]
            #             count += 1
                        
            # print(f"    x: {p_sec.xmin}m - {p_sec.xmax}m")
            # print(f"    y: {p_sec.ymin}m - {p_sec.ymax}m")
            # print(f"    z: {p_sec.zmin}m - {p_sec.zmax}m")
            print(f"    PRIMARY   : {p_sec.variables}")
            print(f"    CONDITION : {p_sec.assigning_condition}")
            print(f"    nCELLS    : {count}")
            
        # save INCON profiles as *.pdf
        import matplotlib.pyplot as plt
        for i in range(inc.num_variables):
            for l, line in enumerate(ini.plot.profile_lines_list):
                geo.slice_plot(line=line, 
                    variable=inc.variable[:,i],
                    title=f"INCON variable#{i}",
                    variable_name=f"INCON #{i}",
                    plot_limits=ini.plot.slice_plot_limits,
                    grid=dat.grid,
                    plt=plt)
                fp = os.path.join(baseDir, ini.t2FileDirFp, f'{IMG_INCON(i)}.{l}.pdf')
                plt.savefig(fp)
                print("saved:", fp)
                plt.close()

        print("[tough3exec] VARIABLE_INCON - finished\n")

    ## GENER ##
    print("***")
    gener_conn = [] # for COFT setting
    for i, secGener in enumerate(ini.generSecList):
        """
        inject the component into a grid block whose temperature will never change 
        and then connect this grid block to the actual grid block 
        """
        # read property of gener from configuration file
        assignsInjMultiBlk = isinstance(secGener.flux, list)
        assignType = 'MULTI' if assignsInjMultiBlk and len(secGener.flux)>1 else 'SINGLE'
        injectionType = 'INDIRECT' if secGener.injectsIndirectly else 'DILECT'

        print(f"GENER {i}: {secGener.name}")
        print(f"    type     : {secGener.type}")
        print(f"    flux_sum : {secGener.flux_sum}")
        if hasattr(secGener, 'temperature') :
            print(f"    temp     : {secGener.temperature}")
        print(f"    block    : {secGener.block}")
        print(f"    flux     : {secGener.flux}")
        print(f"    injblk assign type : {injectionType}, {assignType}")
        print(f"    LTAB     : {secGener.ltab}")
        print(f"    F1(time)      : {secGener.time}")
        print(f"    F2(flux_fact) : {secGener.flux_factor}")
        if hasattr(secGener, 'itab') :
            print(f"    ITAB     : {secGener.itab}")
            print(f"    F3(enthalpy_factor)      : {secGener.enthalpy_factor}")
        
        fluxList = secGener.flux if isinstance(secGener.flux, list) else [secGener.flux]
        if not secGener.injectsIndirectly:
            """ direct injection to specified grid block(s)"""
            for j, (block, flux) \
                in enumerate(zip(secGener.block,fluxList)):
                # get pressure value of block from incon object
                pres = inc[block][0]
                if hasattr(secGener, 'temperature') :
                    # convert to enthalpy
                    """
                    enthalpy = cowat(secGener.temperature,pres)[1]
                    """
                    if "WATE" in secGener.type.upper():
                        enthalpy = cowat(secGener.temperature,pres)[1]
                    else:
                        enthalpy = 0
                    print(f"[tough3exec] block:{block} P:{pres}\t"\
                        +f"T:{secGener.temperature}\tE:{enthalpy}[J/kg]")
                    t2g = t2generator(name=secGener.name, block=block, 
                        type=secGener.type, gx=flux, ex=enthalpy, 
                        ltab=secGener.ltab, time=secGener.time,
                        rate=[] if secGener.ltab<=1 else [ff*flux for ff in secGener.flux_factor],
                        itab=secGener.itab,
                        enthalpy=[] if secGener.itab<=1 else [ef*enthalpy for ef in secGener.enthalpy_factor])
                else:
                    print(f"[tough3exec] block:{block} P:{pres}\t"\
                        +f"T: -- ")
                    t2g = t2generator(name=secGener.name, block=block, 
                        type=secGener.type, gx=flux, 
                        ltab=secGener.ltab, time=secGener.time,
                        rate=[] if secGener.ltab<=1 else [ff*flux for ff in secGener.flux_factor],
                        itab=0,enthalpy=[])
                dat.add_generator(t2g)

        if (not assignsInjMultiBlk) and secGener.injectsIndirectly:
            """indirect injection to specified grid block(s) by single injection block"""
            """if 'injectsIndirectly' is True and 'flux' set in inifile is not list, 
            assign single injection block for actual grid blocks"""
            print(f"    area     : {secGener.area}")
            # create & set an injblock 
            if i>99: sys.exit()
            blknm = f"INJ{i:>2d}"
            blockInj = t2block(name=blknm, volume=secGener.vol_injblock, blockrocktype=inj)
            dat.grid.add_block(blockInj)
            # define & set a connection bet. injblock and adjacent block in computational domain
            for block, area in zip(secGener.block,secGener.area):
                blockAdjacentInj = dat.grid.block[block] 
                conn = t2connection(blocks=[blockInj, blockAdjacentInj], 
                                    distance=secGener.dist_injblock, area=area)
                dat.grid.add_connection(conn)
                gener_conn.append(conn) # for COFT
            # Any value is ok
            enthalpy_tekitou = 100
            # add gener
            t2g = t2generator(name=secGener.name, block=blknm, 
                    type=secGener.type, gx=secGener.flux, ex=enthalpy_tekitou, 
                        ltab=secGener.ltab, time=secGener.time,
                        rate=[] if secGener.ltab<=1 else [ff*secGener.flux for ff in secGener.flux_factor])
            dat.add_generator(t2g)

            # add incon
            # get incon of blockAdjacentInj
            primary = copy.deepcopy(inc[secGener.block[0]])
            # apply same thermodynamic properies to injblock other than temperature
            primary[ID_T] = secGener.temperature
            binc = t2blockincon(variable=primary, block=blknm)
            inc.add_incon(binc)

        if assignsInjMultiBlk and secGener.injectsIndirectly:
            """indirect injection to specified grid block(s) by multiple injection blocks"""
            """if 'injectsIndirectly' is True and 'flux' set in inifile is instance of list, 
            assign multiple injection blocks for each actual grid block"""
            print(f"    area     : {secGener.area}")
            # create & set an injblock 
            if i>9: sys.exit()
            # define & set a connection bet. injblock and adjacent block in computational domain
            if not len(secGener.block) == len(secGener.area) == len(secGener.flux):
                # check length of each list
                sys.exit(f"lengthes of 'block', 'area', 'flux' are not consistent in section:[{secGener}]")
            for j, (block, area, flux) \
                in enumerate(zip(secGener.block,secGener.area,secGener.flux)):
                ## create and add block for injection
                if j>9: sys.exit()
                blknm = f"INJ{i}{j}"
                # print(f"injection block:{blknm}")
                blockInj = \
                    t2block(name=blknm, volume=secGener.vol_injblock, blockrocktype=inj)
                dat.grid.add_block(blockInj)
                ## add connection bet. inj block and actual block
                blockAdjacentInj = dat.grid.block[block] 
                conn = t2connection(blocks=[blockInj, blockAdjacentInj], 
                                    distance=secGener.dist_injblock, area=area)
                dat.grid.add_connection(conn)
                gener_conn.append(conn) # for COFT
                ##  add gener
                # Any value is ok
                enthalpy_tekitou = 100
                # add gener
                t2g = t2generator(name=secGener.name, block=blknm, 
                        type=secGener.type, gx=flux, ex=enthalpy_tekitou, 
                        ltab=secGener.ltab, time=secGener.time,
                        rate=[] if secGener.ltab<=1 else [ff*flux for ff in secGener.flux_factor])
                dat.add_generator(t2g)

                ## add incon
                # get incon of blockAdjacentInj
                primary = copy.deepcopy(inc[secGener.block[j]])
                # apply same thermodynamic properies to injblock other than temperature
                primary[ID_T] = secGener.temperature

                binc = t2blockincon(variable=primary, block=blknm)
                inc.add_incon(binc)

    ## PRESSURE CELL ##
    # initialization of the number of cells added
    n = 0
    # initialization of the number of rocktype added
    m = 0
    
    # each fixed_p_regions_sec
    for  i, fps in enumerate(ini.fixed_p_regions_seclist):
        fps:_readConfig.InputIni._fixedP_RegionSec

        print(f"""***
FIXED_P_REGION {i}: {fps.secName}
    block         : {fps.block}
    type          : {fps.type}
    area          : {fps.area}
    dist_injblock : {fps.dist_injblock}
    temperature   : {fps.temperature}
    pressure      : {fps.pressure_str} 
""")
        ## single pressure cell ##
        if fps.type == FIXED_P_REGION_TYPE_SINGLE_P_CELL:
            # define rocktype to be assigned to added pressure block
            rockTypeAdded: rocktype = copy.deepcopy(dat.grid.rocktype['dfalt'])
            rockTypeAdded.name = f"ZZ{m:>3}"
            # give huge specific heat to keep constant temperature
            rockTypeAdded.specific_heat = 1e20
            # add the rocktype for pressure blocks
            # _readCongig内部のvalidationによりadded_p_block_permeability is not None
            rockTypeAdded.permeability = [fps.added_p_block_permeability for _ in range(3)]
            dat.grid.add_rocktype(rockTypeAdded)
            m = m + 1

            # get cell name to be added
            blknmAdded = get_fixed_p_region_added_cell_name(n, ini.mesh.convention)
            n = n + 1
            ## create and add block for injection
            blkAdded = \
                t2block(name=blknmAdded, volume=HUGE_VOLUME, blockrocktype=rockTypeAdded)
            dat.grid.add_block(blkAdded)

            ## add INCON
            # get incon from domain
            # TODO とりあえずATMにしといた
            kari_blk = ATM_BLK_NAME(ini.mesh.convention)
            primary = copy.deepcopy(inc[kari_blk])

            # apply same thermodynamic properies to injblock other than temperature
            # P            
            if fps.pressure_type == FIXED_P_REGION_PRESS_TYPE_NUM:
                primary[ID_P] = fps.pressure_num
            else:
                # error
                pass
            # T
            if fps.temperature is not None: 
                primary[ID_T] = fps.temperature 
            else:
                # error
                pass
            # COM1
                # TODO
            # COM2
                # TODO

            inc.add_incon(t2blockincon(variable=primary, block=blknmAdded))

            ## add connection bet. inj block and actual block
            for j, blknmInDomain in enumerate(fps.block):
                blkInDomain = dat.grid.block[blknmInDomain] 
                # areaはカラムの面積から取得
                conn = t2connection(blocks=[blkInDomain, blkAdded], 
                                    distance=fps.dist_injblock, 
                                    area=geo.column[geo.column_name(blknmInDomain)].area if fps.area is None else fps.area[j])
                dat.grid.add_connection(conn)


        ## multi pressure cell ##
        if fps.type == FIXED_P_REGION_TYPE_MULTI_P_CELL:
            
            ## define new rocktypes to be assigned to added pressure block
            ## add new blocks for fixing pressure  
            ## add new connection bet. the block and actual block in the domain
            m, n, list_blknmAdded, list_blknmInDomain = \
                    add_multiple_source_blks(dat=dat, geo=geo,
                                             n_added_rocktype_counter=m,
                                             n_added_blocks_counter=n,
                                             blocks=fps.block, 
                                             convention=ini.mesh.convention,
                                             dist_injblocks=fps.dist_injblock,
                                             # assume infiltration occurs along z direction
                                             direction=3,
                                             # put block-in-domain above block-added
                                             dircos=1,
                                             added_block_permeability = fps.added_p_block_permeability,
                                             area = fps.area)
            """ 関数化 2023/12
            # define rocktype to be assigned to added pressure block
            if fps.added_p_block_permeability is not None:
                rockTypeAdded: rocktype = copy.deepcopy(dat.grid.rocktype['dfalt'])
                rockTypeAdded.name = f"ZZ{m:>3}"
                # give huge specific heat to keep constant temperature
                rockTypeAdded.specific_heat = 1e20
                rockTypeAdded.permeability = [fps.added_p_block_permeability for _ in range(3)]
                # add the rocktype for pressure blocks
                dat.grid.add_rocktype(rockTypeAdded)
                m = m + 1
            else:
                # あとで接続先のブロックのrocktypeを割り当てる。
                pass
            
            for j, blknmInDomain in enumerate(fps.block):

                # get t2block object
                blkInDomain: t2block = dat.grid.block[blknmInDomain] 

                # define rocktype to be assigned to added pressure block
                if fps.added_p_block_permeability is None:
                    # 接続先のブロックと同じpermeabilityをもつ追加ブロック用rocktype("ZZxxx")の有無を確認。
                    # check existence of rocktype of same permeability
                    isZZrock = [bool(re.search(r'ZZ[ 0-9]{3}',type.name)) for type in dat.grid.rocktypelist]
                    zzRockPermList =  [list(_.permeability) for _ in np.array(dat.grid.rocktypelist)[isZZrock]]
                    if list(blkInDomain.rocktype.permeability) in zzRockPermList:
                        # すでに作成済みの場合は、そのrocktypeをそのまま割り当てる
                        for i, _ in enumerate(zzRockPermList):
                            if list(blkInDomain.rocktype.permeability) == _:
                                rockTypeAdded: rocktype = np.array(dat.grid.rocktypelist)[isZZrock][i]
                                break
                    else:
                        # for case adding new rocktype
                        rockTypeAdded: rocktype = copy.deepcopy(dat.grid.rocktype['dfalt'])
                        rockTypeAdded.name = f"ZZ{m:>3}"
                        # give huge specific heat to keep constant temperature
                        rockTypeAdded.specific_heat = 1e20
                        rockTypeAdded.permeability = blkInDomain.rocktype.permeability
                        # add the rocktype for pressure blocks
                        dat.grid.add_rocktype(rockTypeAdded)
                        m = m + 1

                ## add block for fixing pressure
                blknmAdded = get_fixed_p_region_added_cell_name(n, ini.mesh.convention)
                n = n + 1                
                blkAdded = \
                    t2block(name=blknmAdded, volume=HUGE_VOLUME, blockrocktype=rockTypeAdded)
                dat.grid.add_block(blkAdded)

                ## add connection bet. inj block and actual block
                # areaはカラムの面積から取得
                conn = t2connection(blocks=[blkInDomain, blkAdded], 
                                    distance=fps.dist_injblock, 
                                    area=geo.column[geo.column_name(blknmInDomain)].area if fps.area is None else fps.area[j])
                
                dat.grid.add_connection(conn)
                """
            
            ## add INCON
            # get incon of blknmInDomain
            for j, (blknmAdded, blknmInDomain) in enumerate(zip(list_blknmAdded, list_blknmInDomain)):
                
                # get t2block object
                blkInDomain: t2block = dat.grid.block[blknmInDomain] 
                
                primary = copy.deepcopy(inc[blknmInDomain])

                # apply same thermodynamic properies to injblock other than temperature
                # P            
                if fps.pressure_type == FIXED_P_REGION_PRESS_TYPE_XSTATIC:
                    h = suf_elev_t2block(blkInDomain, geo, ini.mesh.convention) - blkInDomain.centre[2] 
                    primary[ID_P] = fps.pressure_num * G * h
                elif fps.pressure_type == FIXED_P_REGION_PRESS_TYPE_OVER_P_RATIO:
                    primary[ID_P] = fps.pressure_num * primary[ID_P]
                elif fps.pressure_type == FIXED_P_REGION_PRESS_TYPE_NUM:
                    primary[ID_P] = fps.pressure_num
                # T
                if fps.temperature is not None: 
                    primary[ID_T] = fps.temperature 
                # COM1
                    # TODO
                # COM2
                    # TODO
                inc.add_incon(t2blockincon(variable=primary, block=blknmAdded))

        print(f'    Number of cells added: {n}')

    ## SEAFLOOR ##
    # this section valid only module=eco2n_v2
    if hasattr(ini, 'sea') and (
            ECO2N in II['module'].strip().lower() or \
            EWASG in II['module'].strip().lower()):

        print(f"*** SEAFLOOR")
        
        ## in use
        n # the number of cells added
        m # the number of rocktype added
        inc # t2incon object

        ## Extract the blocks that comprise the seafloor
        seafloorBlks = []
        for col in geo.columnlist:
            col:column
            if col.surface < ini.sea.sea_level: # surface elevation
                layer_top = geo.column_surface_layer(col)
                blockname_top = geo.block_name(layer_top.name, col.name)
                seafloorBlks.append(blockname_top)
                
                # この処理はmakeGridFuncにも実装したのでなくてもいい
                # If the block has a connection to ATM-blk, kill that connection.
                atmconn = (blockname_top, geo.block_name(geo.layerlist[0].name,geo.atmosphere_column_name))
                if atmconn in dat.grid.connection:
                    dat.grid.delete_connection(atmconn)
                    logger.info(f"connection killed: {atmconn}")
                elif (atmconn[1], atmconn[0]) in dat.grid.connection:
                    dat.grid.delete_connection((atmconn[1], atmconn[0]))
                    logger.info(f"connection killed: {(atmconn[1], atmconn[0])}")
        
        ## define new rocktypes to be assigned to added pressure block
        ## add new blocks for fixing pressure  
        ## add new connection bet. the block and actual block in the domain
        m, n, list_blknmAdded, list_blknmInDomain = \
                add_multiple_source_blks(dat=dat, geo=geo,
                                         n_added_rocktype_counter=m,
                                         n_added_blocks_counter=n,
                                         blocks=seafloorBlks, 
                                         convention=ini.mesh.convention,
                                         dist_injblocks=[None, ini.sea.closeness_to_seawater_blk],
                                         # assume seawater infiltration occurs along z direction
                                         direction=3,
                                         # put seawater-block above block-in-domain
                                         dircos=-1,
                                         added_block_permeability = None,
                                         area = None)

        ## add INCON
        # get incon of blknmInDomain
        for j, (blknmAdded, blknmInDomain) in enumerate(zip(list_blknmAdded, list_blknmInDomain)):
            
            # get t2block object
            blkInDomain: t2block = dat.grid.block[blknmInDomain] 
            
            primary = copy.deepcopy(inc[blknmInDomain])

            # apply same thermodynamic properies to seawater blk
            # seafloor depth
            h = ini.sea.sea_level - suf_elev_t2block(blkInDomain, geo, ini.mesh.convention) 
            # set P            
            primary[ID_P] = seawater_property.FUNC_SEA_PRESSURE(h)
            # set T
            primary[ID_T] = seawater_property.FUNC_SEA_TEMP(h)
            # set COM1
            primary[ID_XSAL] = seawater_property.FUNC_SEA_SALINITY(h)/1000
            # set other COMx
            if ECO2N in II['module'].strip().lower():
                primary[INCON_ID_ECO2N_XCO2] = ini.sea.primary_xcom
            if EWASG in II['module'].strip().lower():
                primary[INCON_ID_EWASG_XNCG] = ini.sea.primary_xcom
            
            inc.add_incon(t2blockincon(variable=primary, block=blknmAdded))

        print(f"    SEA LEVEL                   : {ini.sea.sea_level} m")
        print(f"    THE NUMBER OF SEAFLOOR BLOCK: {len(seafloorBlks)}")
    

    ## BOUNDARY ##
    print("*** BOUNDARY")
    ## top & bottom ##
    # assign crustal heat flow & railfall on top boundary
    # & focus heat flow
    layer_bot = geo.layerlist[-1]  # get property of bottom layer 
    if ini.mesh.type == REGULAR and ini.mesh.isRadial:
        # for case radial
        print(f"mesh type : radial")
        r_inner = 0
        for dr,col in zip(ini.mesh.rblocks,geo.columnlist):
            blockname_bot = geo.block_name(layer_bot.name, col.name)
            # property of top layer for each column is aquired here
            layer_top = geo.column_surface_layer(col)
            blockname_top = geo.block_name(layer_top.name, col.name)
            # r_inner = col.centre[0] - dr/2 これだと誤差が大きい
            # r_outer = col.centre[0] + dr/2 これだと誤差が大きい
            r_outer = r_inner + dr
            # check position of elem, just in case
            if col.centre[0] < r_inner or r_outer < col.centre[0]: 
                sys.exit()
            area = (r_outer**2 - r_inner**2)*math.pi
            if II['crustalHeatFlowRate'] > 0:
                gx_bot = II['crustalHeatFlowRate']*area # gx : J/s
                crust_hf = t2generator(name = blockname_bot, block = blockname_bot, 
                            type = 'HEAT', gx = gx_bot) 
                dat.add_generator(crust_hf)
            if II['rainfallAnnual_mm'] > 0 and \
                    not (hasattr(ini, 'sea') and ini.sea.sea_level > col.surface):
                # seafloorには割り当てない
                gx_top = II['rainfallAnnual_mm']/365.25/24/3600*area # gx : kg/s
                rain_entalpy = II['T_rain'] * 4.217 * 1000 # J/kg
                crust_rain = \
                    t2generator(name = blockname_top, block = blockname_top, 
                                type = 'WATE', gx = gx_top, ex = rain_entalpy) 
                dat.add_generator(crust_rain)
            if II['assignFocusHf'] \
                and II['focusHfRange'][0] <= r_inner and r_outer <= II['focusHfRange'][1]:
                gx_focus = II['focusHfRate']*area # gx : J/s
                focus_hf = t2generator(name = blockname_bot, block = blockname_bot, 
                            type = 'HEAT', gx = gx_focus) 
                dat.add_generator(focus_hf)
                
            # update
            r_inner = r_outer
    else:
        # for case rectangular
        print(f"mesh type : rectangular")
        for col in geo.columnlist:
            blockname_bot = geo.block_name(layer_bot.name, col.name)
            # property of top layer for each column is aquired here
            layer_top = geo.column_surface_layer(col)
            blockname_top = geo.block_name(layer_top.name, col.name)
            area = col.area # m^2
            gx_bot = II['crustalHeatFlowRate']*area # gx : J/s
            gx_top = II['rainfallAnnual_mm']/365.25/24/3600*area # gx : kg/s
            rain_entalpy = II['T_rain'] * 4.217 * 1000 # J/kg
            if II['crustalHeatFlowRate'] > 0:
                crust_hf = \
                    t2generator(name = blockname_bot, block = blockname_bot, 
                                type = 'HEAT', gx = gx_bot) 
                dat.add_generator(crust_hf)
            if II['rainfallAnnual_mm'] > 0:
                crust_rain = \
                    t2generator(name = blockname_top, block = blockname_top, 
                                type = 'WATE', gx = gx_top, ex = rain_entalpy) 
                dat.add_generator(crust_rain)
            if II['assignFocusHf'] \
                and (II['focusHfRange'][0] <= col.centre[0] and col.centre[0] <= II['focusHfRange'][1])\
                and (II['focusHfRange'][2] <= col.centre[1] and col.centre[1] <= II['focusHfRange'][3]):
                gx_focus = II['focusHfRate']*area # gx : J/s
                focus_hf = t2generator(name = blockname_bot, block = blockname_bot, 
                            type = 'HEAT', gx = gx_focus) 
                dat.add_generator(focus_hf)

    ## FOFT ##
    """
    A list property containing blocks 
    for which time history output is required
    """
    print("*** FOFT")
    if len(II['history_block'])==0:
        # add the first block to it manualy 
        # since at least one FOFT*.csv file is required in the visualization stage.
        dat.history_block = [dat.grid.blocklist[0].name]
    else:
        dat.history_block = II['history_block']
    ## COFT ##
    print("*** COFT")
    if II['prints_hc_surface']:
        for col in geo.columnlist:
            layer_top = geo.column_surface_layer(col)
            blockname_top = geo.block_name(layer_top.name, col.name)
            # check existence of connection and then append
            conn = (blockname_top,ATM_BLK_NAME(ini.mesh.convention))
            connr = (ATM_BLK_NAME(ini.mesh.convention), blockname_top)
            if conn in dat.grid.connection:
                II['history_connection'].append(conn)
            elif connr in dat.grid.connection:
                II['history_connection'].append(connr)
    if II['prints_hc_inj']:
        II['history_connection'].extend(gener_conn)
    # print(II['history_connection'])
    dat.history_connection = II['history_connection']

    ## TIME ##
    print("*** TIME")
    if II['setTimes']:
        dat.output_times['max_timestep'] = II['max_timestep_TIMES']
        dat.output_times['num_times_specified'] = II['num_times_specified']
        dat.output_times['num_times'] = II['num_times']
        dat.output_times['time'] = II['time']
        dat.output_times['time_increment'] = II['time_increment']

    ## SELEC ##
    print("*** SELEC")
    if ECO2N in II['module'].strip().lower() or EWASG == II['module'].strip().lower():
        dat.selection['integer'] = II['selection_line1']
        dat.selection['float'] = II['selection_line2']
        # copy co2tab
        shutil.copy(os.path.join(baseDir,'tables/CO2TAB'), ini.t2FileDirFp)

    ## SOLVR ##
    print("*** SOLVR")
    dat.solver['type'] = ini.solver.matslv
    if ini.solver.matslv == 8:
        print(f'PETSc solver')
        if ini.solver.ksp_type is not None:
            print(f'   -ksp_type {ini.solver.ksp_type}')
        if ini.solver.pc_type is not None:
            print(f'   -pc_type {ini.solver.pc_type}')
        if ini.solver.ksp_rtol is not None:
            print(f'   -ksp_rtol {ini.solver.ksp_rtol}')
    else:
        dat.solver['z_precond'] = ini.solver.z_precond
        dat.solver['o_precond'] = ini.solver.o_precond
        dat.solver['relative_max_iterations'] = ini.solver.relative_max_iterations
        dat.solver['closure'] = ini.solver.closure
    print(dat.solver)
    # # output .petscrc for parallel execution
    # from pathlib import Path
    # try: 
    #     os.remove(os.path.join(Path.home(),".petscrc"))
    # except: 
    #     pass    
    # if ini.solver.matslv == 8 \
    #     and (ini.solver.ksp_type is not None \
    #         or ini.solver.pc_type is not None \
    #         or ini.solver.ksp_rtol is not None):
    #     rc = os.path.join(ini.t2FileDirFp,'.petscrc')
    #     print(f'PETSc solver')
    #     with open(rc, 'w') as f:
    #         if ini.solver.ksp_type is not None:
    #             f.write(f'-ksp_type {ini.solver.ksp_type}\n')
    #             print(f'   -ksp_type {ini.solver.ksp_type}')
    #         if ini.solver.pc_type is not None:
    #             f.write(f'-pc_type {ini.solver.pc_type}\n')
    #             print(f'   -pc_type {ini.solver.pc_type}')
    #         if ini.solver.ksp_rtol is not None:
    #             f.write(f'-ksp_rtol {ini.solver.ksp_rtol}\n')
    #             print(f'   -ksp_rtol {ini.solver.ksp_rtol}')
    #     shutil.copy2(rc, Path.home())

    ## write vtk for paraview
    # dat.grid.write_vtk(geo, os.path.join(ini.t2FileDirFp, FILENAME_GRIDVTK))
    ## write tough input file
    TMP = os.path.join(ini.t2FileDirFp, 'tmp')
    dat.write(TMP)
    import time
    # wait until file TMP created
    while not os.path.isfile(TMP): time.sleep(1)
    # add additional keyword
    with open(TMP, 'r') as tmp, open(ini.t2FileFp, 'w') as f, \
        open(os.path.join(baseDir, 't2data_ENDCY_replace.dat'), 'r') as a:
        for line in tmp:
            if 'ENDCY' in line:
                for line_add in a:
                    f.write(line_add)
            else:
                f.write(line)
    os.remove(TMP)
    ## write incon file
    inc.write(ini.inconFp)
    ##

    print(f"""
    OUTPUT:
        {ini.t2FileFp}
        {ini.inconFp}
        {os.path.join(ini.t2FileDirFp, FILENAME_GRIDVTK)}
    """)

def create_incon_from_1d_result(ini1d:_readConfig.InputIni, 
                                iniNow:_readConfig.InputIni,
                                incNow: t2incon):
    from scipy import interpolate
    geoNow = mulgrid(iniNow.mulgridFileFp) 
    geo1d = mulgrid(ini1d.mulgridFileFp) 
    grid1d = t2grid().fromgeo(geo1d) # t2dataファイルからはt2block.atmosphereの情報が得られないためmulgridから変換する
    save1d = t2incon(ini1d.saveFp)
    z = []
    varlists = [np.array([])]*len(save1d[grid1d.blocklist[0].name].variable)
    interpFuncs = [np.array([])]*len(save1d[grid1d.blocklist[0].name].variable)

    for blk in grid1d.blocklist:
        if not blk.atmosphere:
            z.append(blk.centre[2])
            for i, var in enumerate(save1d[blk.name].variable):
                varlists[i] = np.append(varlists[i], var)

    for i, varlist in enumerate(varlists):
        interpFuncs[i] = interpolate.interp1d(z, varlist, fill_value="extrapolate")
        
    for col in geoNow.columnlist:
        layer_top = geoNow.column_surface_layer(col)
        for lay in geoNow.layerlist:
            if lay.centre > layer_top.centre: 
                continue
            elif lay.centre == layer_top.centre: 
                #最上位レイヤー
                depth = (lay.thickness-(lay.top-col.surface))/2 \
                    if iniNow.toughInput['water_table_elevation'] is None \
                    else iniNow.toughInput['water_table_elevation'] - lay.centre
            else:
                #２層目以降
                depth = col.surface-lay.centre \
                    if iniNow.toughInput['water_table_elevation'] is None \
                    else iniNow.toughInput['water_table_elevation'] - lay.centre
            
            blkname = geoNow.block_name(lay.name, col.name)
            
            # initialize incon
            incNow[blkname].variable = copy.deepcopy(iniNow.toughInput['PRIMARY_default'])
            if depth < 0:
                # if lay.center above water table, assign iniNow.atmosphere.PRIMARY_AIR
                    incNow[blkname].variable = iniNow.atmosphere.PRIMARY_AIR
            else:
                # paste 1d SAVE to voro INCON
                try:
                    if  EOS2 == iniNow.toughInput['module'].strip().lower():
                        incNow[blkname].variable[INCON_ID_EOS2_PRES] = \
                            interpFuncs[INCON_ID_EOS2_PRES](-1*depth)
                        incNow[blkname].variable[INCON_ID_EOS2_TEMP] = \
                            interpFuncs[INCON_ID_EOS2_TEMP](-1*depth)
                    elif  ECO2N in iniNow.toughInput['module'].strip().lower():
                        incNow[blkname].variable[INCON_ID_ECO2N_PRES] = \
                            interpFuncs[INCON_ID_ECO2N_PRES](-1*depth)
                        incNow[blkname].variable[INCON_ID_ECO2N_TEMP] = \
                            interpFuncs[INCON_ID_ECO2N_TEMP](-1*depth)
                    elif  EWASG in iniNow.toughInput['module'].strip().lower():
                        incNow[blkname].variable[INCON_ID_EWASG_PRES] = \
                            interpFuncs[INCON_ID_EWASG_PRES](-1*depth)
                        incNow[blkname].variable[INCON_ID_EWASG_TEMP] = \
                            interpFuncs[INCON_ID_EWASG_TEMP](-1*depth)
                except ValueError as x:
                    print(f"!!!!![ERROR] The depth value was probably beyond the interpolatable range.")
                    print(f"!!!!![ERROR] col:{col.name} layer:{lay.name} depth:{depth}m ")
                    raise x

    incNow.write(iniNow.inconFp)

def add_multiple_source_blks(dat:t2data, 
                             geo:mulgrid,
                             n_added_rocktype_counter:int, 
                             n_added_blocks_counter:int, 
                             blocks:list, 
                             convention:int, 
                             dist_injblocks:list,
                             direction:int=3, 
                             # put 1st-elem above 2nd-elem (i.e. put block-in-domain above block-added)
                             dircos:float=1,
                             added_block_permeability:float=None, 
                             area:list=None):
    """_summary_

    Args:
        dat (t2data): _description_
        geo (mulgrid): _description_
        n_added_rocktype_counter (int): _description_
        n_added_blocks_counter (int): _description_
        blocks (list): _description_
        convention (int): _description_
        dist_injblocks (list): [dist(block-in-domain), dist(block-added)]
            If direction==3, 'None' can be specified for dist_injblocks[0]. 
            In that case, half the width of the corresponding block is used instead.
            You must not specify 'None' for dist_injblocks[1].
        direction (int):  x->1, y->2, z->3. Defaults to 3.
        dircos (float): Defaults to 1.
            Cosine of the angle between the vector from the 1st-elem to the 2nd-elem and the gravitational acceleration vector
            If direction==3, dircos=1 means put block-in-domain above block-added.
        added_block_permeability (float, optional): _description_. Defaults to None.
        area (list, optional): _description_. Defaults to None.

    Returns:
        int, int, list, list: 
            updated n_added_rocktype_counter, 
            updated n_added_blocks_counter, 
            added blk list and corresponding in-domain block list
    """
    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")
    
    ## define rocktype to be assigned to added pressure block (1)
    if added_block_permeability is not None:
        # (case 1 permeability is specified)
        rockTypeAdded: rocktype = copy.deepcopy(dat.grid.rocktype['dfalt'])
        rockTypeAdded.name = f"ZZ{n_added_rocktype_counter:>3}"
        # give huge specific heat to keep constant temperature
        rockTypeAdded.specific_heat = 1e20
        rockTypeAdded.permeability = [added_block_permeability for _ in range(3)]
        # add the rocktype for pressure blocks
        dat.grid.add_rocktype(rockTypeAdded)
        n_added_rocktype_counter += 1
    else:
        # (case 2 permeability is "not" specified) --> (**)
        pass # 以下の forブロックの中でやる
    
    list_blknmAdded = []
    list_blknmInDomain = []

    for j, blknmInDomain in enumerate(blocks):

        # get t2block object
        blkInDomain: t2block = dat.grid.block[blknmInDomain] 

        ## define rocktype to be assigned to added pressure block (2) 
        if added_block_permeability is None:
            # (**) --> (case 2 permeability is "not" specified)
            # 現在のブロックと同じpermeabilityをもつ、追加済みrocktype("ZZxxx")の有無を確認。
            # (追加する岩石タイプを最小限にするため)
            # check existence of rocktype of same permeability
            isZZrock = [bool(re.search(r'ZZ[ 0-9]{3}',type.name)) for type in dat.grid.rocktypelist]
            zzRockPermList =  [list(_.permeability) for _ in np.array(dat.grid.rocktypelist)[isZZrock]]
            if list(blkInDomain.rocktype.permeability) in zzRockPermList:
                # すでに同じpermの岩石タイプ"ZZxxx"が追加されている場合は、そのrocktypeをそのまま現在のブロックに割り当てる
                for i, _ in enumerate(zzRockPermList):
                    if list(blkInDomain.rocktype.permeability) == _:
                        rockTypeAdded: rocktype = np.array(dat.grid.rocktypelist)[isZZrock][i]
                        break
            else:
                # 現在のブロックと同じpermの岩石タイプがまだ追加されていない場合は、岩石タイプを新規追加する。
                # for case adding new rocktype
                rockTypeAdded: rocktype = copy.deepcopy(dat.grid.rocktype['dfalt'])
                rockTypeAdded.name = f"ZZ{n_added_rocktype_counter:>3}"
                # give huge specific heat to keep constant temperature
                rockTypeAdded.specific_heat = HUGE_SPECIFIC_HEAT
                rockTypeAdded.porosity = 0.99
                rockTypeAdded.permeability = blkInDomain.rocktype.permeability
                # add the rocktype for pressure blocks
                dat.grid.add_rocktype(rockTypeAdded)
                n_added_rocktype_counter += 1

        ## add block for fixing pressure and temperature
        blknmAdded = get_fixed_p_region_added_cell_name(n_added_blocks_counter, convention)
        n_added_blocks_counter += 1                
        blkAdded = \
            t2block(name=blknmAdded, volume=HUGE_VOLUME, blockrocktype=rockTypeAdded)
        dat.grid.add_block(blkAdded)

        # for returning values
        list_blknmAdded.append(blknmAdded)
        list_blknmInDomain.append(blknmInDomain)

        ## add connection bet. inj block and actual block
        # calc distance in connection if required
        if direction==3 and dist_injblocks[0] is None:
            lay = geo.layer[geo.layer_name(blknmInDomain)]
            col = geo.column[geo.column_name(blknmInDomain)]
            if col.surface > lay.top:
                # other blocks
                dist_injblocks[0] = lay.thickness/2
            else:
                # surface block
                dist_injblocks[0] = (col.surface - lay.bottom)/2
        
        if None in dist_injblocks:
            logger.error(f"if direction=={direction}, 'None' cannot be included in dist_injblocks")
            raise Exception("argument error in tough3_exec_ws.added_block_permeability()")

        logger.info(f"CONNE distance: {blkInDomain, blkAdded}:{dist_injblocks}")

        # areaはカラムの面積から取得
        conn = t2connection(blocks=[blkInDomain, blkAdded], 
                            distance=dist_injblocks, 
                            direction=direction,
                            dircos=dircos,
                            area=geo.column[geo.column_name(blknmInDomain)].area if area is None else area[j])
        dat.grid.add_connection(conn)

    return n_added_rocktype_counter, n_added_blocks_counter, list_blknmAdded, list_blknmInDomain


def suf_elev_t2block(blk:t2block, geo: mulgrid, convention:int):
    if convention==0:
        col_name = blk.name[0:3]
    elif convention==1:
        col_name = blk.name[3:5]
    elif convention==2:
        col_name = blk.name[2:5]
    return geo.column[col_name].surface

def get_fixed_p_region_added_cell_name(i:int, convention:int):
    ## MULgraph geometry file Naming conventions (optional)
    # 0: 3 characters for column followed by 2 digits for layer (default)
    # 1: 3 characters for layer followed by 2 digits for column 
    # 2: 2 characters for layer followed by 3 digits for column
    if convention==0:
        # 'zaa 0' - 'zzz99'
        elem_name = mgav.col_name(17603+i//99, 0) + mgav.layer_name(i%99, 0)
    elif convention==1:
        # 'zaa 0' - 'zzz99'
        elem_name = mgav.layer_name(17603+i//99, 1) + mgav.col_name(i%99, 1)
    elif convention==2:
        # 'a 999' - 'zz999'
        elem_name = mgav.layer_name(1+i, 2) + mgav.col_name(999, 2)
    return elem_name

if __name__ == "__main__":
    main()