from import_pytough_modules import *
#
from matplotlib.pyplot import colorbar
from t2listing import *
from t2data import *
import os
import configparser
import json
import _readConfig
from define import *
import t2outUtil as t2o
from PIL import Image, ImageDraw, ImageFile 
ImageFile.LOAD_TRUNCATED_IMAGES = True
import makeGridFunc
import shutil
import pandas as pd


## get argument
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("inputIni", 
        help="fullpath of toughInput setting input.ini", type=str)
parser.add_argument("-v","--writesVtu", 
        help="if given, write *.vtu files for paraview", 
        action='store_true')
parser.add_argument("-t","--plotsTimeSeries", 
        help="if given, plot timeseries", 
        action='store_true')
parser.add_argument("-ts","--plotsTimeSeriesSurface", 
        help="if given, plot timeseries of surface flow", 
        action='store_true')
parser.add_argument("-coft","--plotsTimeSeriesSurfaceAreaCoft", 
        help="if given, plot timeseries of surface flow within pre-defined areas in define.COFT_TS_AREAS", 
        action='store_true')
parser.add_argument("-cofts","--plotsTimeSeriesSurfaceSumAllCoft", 
        help="if given, plot timeseries of surface flow by reading COFT", 
        action='store_true')
parser.add_argument("-foft","--plotsTimeSeriesFoft", 
        help="if given, plot timeseries of variable for each block by reading FOFT", 
        action='store_true')
parser.add_argument("-pl","--plotsProfileLast", 
        help="if given, plot vertical profile at end timestep", 
        action='store_true')
parser.add_argument("-pa","--plotsProfileAll", 
        help="if given, plot vertical profile at all printed timestep", 
        action='store_true')
parser.add_argument("-gif","--createGif", 
        help="if given, create gif for all printed timestep", 
        action='store_true')
parser.add_argument("-plc","--plotsProfileLastCsv", 
        help="if given, plot vertical profile at end timestep from OUTPUT_ELEME.csv", 
        action='store_true')
parser.add_argument("-pac","--plotsProfileAllCsv", 
        help="if given, plot vertical profile at all printed timestep", 
        action='store_true')
parser.add_argument("-gifc","--createGifCsv", 
        help="if given, create gif for all printed timestep from OUTPUT_ELEME.csv", 
        action='store_true')
parser.add_argument("-incon","--inconColumn", 
        help="if given, plot vertical variation for each column from INCON and SAVE file", 
        action='store_true')
parser.add_argument("-suf","--surfaceFlowMap", 
        help="if given, plot surface flow map at the end of simulation", 
        action='store_true')
parser.add_argument("-sufall","--interval", 
        help="plot surface flow map by given time interval. read data from coft csv.", 
        type=int)
# parser.add_argument("-f","--forceOverWrite", 
#         help="forceOverWrite", 
#         action='store_true')
args = parser.parse_args()

## read inputIni ##
ini = _readConfig.InputIni().read_from_inifile(args.inputIni)
II = ini.toughInput


t2o.create_savefig_dir(ini)
# make grid
makeGridFunc.makeGrid(ini, overWrites=True if ini.mesh.type.upper().strip() == REGULAR else False)

# check file existence

# read required file 
# if args.plotsProfileAll or args.plotsProfileLast or args.createGif \
#         or args.writesVtu or args.plotsTimeSeriesSurfaceAreaCoft \
#         or args.plotsTimeSeriesSurfaceSumAllCoft \
#         or args.plotsProfileLastCsv or args.plotsProfileAllCsv \
#         or args.createGifCsv or args.surfaceFlowMap:
if not os.path.exists(ini.mulgridFileFp): 
    sys.exit(f"no geo file: {ini.mulgridFileFp}")
geo = mulgrid(ini.mulgridFileFp)

# if args.plotsProfileAll or args.plotsProfileLast or args.createGif \
#     or args.writesVtu or args.plotsTimeSeriesSurfaceAreaCoft or args.plotsTimeSeriesFoft: 
#     if not os.path.exists(ini.t2FileFp): 
#         sys.exit(f"no t2data file: {ini.t2FileFp}")
#     dat = t2data(ini.t2FileFp)
if not os.path.exists(ini.t2FileFp): 
    sys.exit(f"no t2data file: {ini.t2FileFp}")
dat = t2data(ini.t2FileFp)
datG = t2data(ini.t2GridFp)

if args.plotsProfileAll or args.plotsProfileLast or args.createGif \
        or args.writesVtu or args.plotsTimeSeriesSurface or args.surfaceFlowMap:
    if not os.path.exists(ini.tOutFileFp): 
        sys.exit(f"no listing file {ini.tOutFileFp}")
    try:
        lst2 = t2listing(ini.tOutFileFp)
    except:
        print(f"[makeVtu] ERROR. failed to open {ini.tOutFileFp}")
        args.plotsProfileAll = False
        args.plotsProfileLast = False
        args.createGif = False
        args.writesVtu = False

# define function
def original_plot(var_name, timeNow, df_elem, line, l, ini, dat, plt, df_conn=None, 
                  saveDir:str=None, overWrites=False, extension='pdf'):
    
    # prepare parameters for plot
    colourmap = None
    
    saveDir = os.path.join(saveDir, "slice_images")
    os.makedirs(saveDir, exist_ok=True)
    fn = f'{var_name}_{timeNow}_line{l}.{extension}'
    fp = os.path.join(saveDir, fn)
    if os.path.isfile(fp) and not overWrites:
        print(f"    Already exist. skip creating {fn}")
        return fp

    if FLAG_NAME_FLOW in var_name.lower():
        if df_conn is None: 
            # skip creating fig
            return None
        _slice_plot_flow(geo,df_conn,ini,dat,plt,line,l,timeNow,saveDir,overWrites)
        return 
        
    if FLAG_NAME_RES == var_name.lower().strip(): #'PRES'とかぶるのでinでなく==使用
        variable = t2o.calc_bulk_resistivity(t2o.dfCleanElem2(df_elem, ini.mesh.convention))
        colourmap = CMAP_RESISTIVITY
    else:
        variable = t2o.dfCleanElem(df_elem,var_name, ini.mesh.convention)
    
    geo.slice_plot(line=line, 
                variable=variable,
                title=f"{var_name} in vertical slice {line} \n t={t2o.sec2year(timeNow)}",
                variable_name=var_name,
                plot_limits=ini.plot.slice_plot_limits,
                colourbar_limits=t2o.get_cbar_limits(var_name),
                colourmap=colourmap,
                contour_label_format='%.1f',
                grid=dat.grid,
                plt=plt,
                contours = t2o.get_contour_intbal(var_name),
                unit=t2o.get_unit(var_name))
    plt.grid(False)
    plt.savefig(fp)
    print("saved:", fp)
    plt.close()
    return fp

def _slice_plot_flow(geo:mulgrid, df_conn:pd.DataFrame, ini:_readConfig.InputIni, dat:t2data, 
                     plt, line, l, timeNow, saveDir, overWrites):
    
    # prepare parameters for plot
    if ini.toughInput['simulator']==SIMULATOR_NAME_T3:
        floAllColName = 'FLOW'
        floLiqColName = 'FLOW_L'
        floGasColName = 'FLOW_G'
        temp = "TEMP"
    if ini.toughInput['simulator']==SIMULATOR_NAME_T2:
        floAllColName = 'FLOF'
        floLiqColName = 'FLO(AQ.)'
        floGasColName = 'FLO(GAS)'
        temp = "T"

    # flow_scale=0.001
    # flow_scale=0.0001
    flow_scale=1000
    # flow_scale=0.00002
    
    kwds = {
        'line': line,
        'variable': t2o.dfCleanElem(df_elem, temp, ini.mesh.convention),
        'title': f"{temp} in vertical slice {line} \n t={t2o.sec2year(timeNow)}",
        'variable_name': temp,
        'plot_limits': ini.plot.slice_plot_limits,
        'colourbar_limits': t2o.get_cbar_limits(temp),
        'colourmap': None,
        'contour_label_format': '%.1f',
        'grid': dat.grid,
        'plt': plt,
        'flow_arrow_width': 0.0015,
        'flow_unit': "kg/s",
        'flow_scale': flow_scale,
        'contours': t2o.get_contour_intbal(temp),
        'unit': t2o.get_unit(temp),
        'linecolour': 'black'
    }

    for fcn in [floAllColName, floLiqColName, floGasColName]:
        # determine filename
        fn = f'{fcn}_{timeNow}_line{l}.pdf'
        fp = os.path.join(saveDir, fn)

        # check file existence
        if os.path.isfile(fp) and not overWrites:
            print(f"    Already exist. skip creating {fn}")
            continue
        
        # plot
        kwds['flow'] = np.array(t2o.dfCleanConn(df_conn, ini.mesh.convention)[fcn])
        geo.slice_plot(**kwds)
        
        # save
        plt.grid(False)
        plt.savefig(fp)
        print("saved:", fp)
        plt.close()
    return 


def original_surfacemap(variable_name:str, values:list, 
                        ini:_readConfig.InputIni, geo:mulgrid, 
                        title, cbarlim=None ,info:str="", saveDir:str=None,
                        overWrites=False, extension='pdf'):
    if saveDir is None:
        saveDir = ini.t2FileDirFp
    saveDir = os.path.join(saveDir, "sufmap_images")
    os.makedirs(saveDir, exist_ok=True)
    
    fn = os.path.join(saveDir, f'surfaceflow_{variable_name}_{info}.{extension}')
    if os.path.isfile(fn) and not overWrites:
        print(f"    Already exist. skip creating surfaceflow_{variable_name}_{info}.pdf")
        return fn

    if cbarlim is None:
        # full range
        cbarlim = (min([v for v in values if v is not None]), 
                   max([v for v in values if v is not None]))
    # reset figure
    plt.figure()
    # plot flow data
    geo.layer_plot(layer=None, variable=values, plt=plt, variable_name=variable_name+"/m^2",
                title=title,
                xlabel="Northing (m)", ylabel="Easting (m)", 
                colourbar_limits=cbarlim)
    
    # draw elevation contour
    elevations, X, Y = [], [], []
    for col in geo.columnlist:
        X.append(col.centre[0])
        Y.append(col.centre[1])
        elevations.append(col.surface)
    plt.tricontour(X, Y, elevations, np.arange(1000,2500,100), 
                colors='white', linewidths=0.5)
    plt.tricontour(X, Y, elevations, np.arange(500,2500,500), 
                colors='white', linewidths=1)

    # add symbol
    for place, tup in TOPO_MAP_SYMBOL.items():
        plt.plot(tup[0], tup[1], marker='o', markersize=1, color='black')
        # plt.annotate(place, xy=tup, xytext=(tup[0], tup[1]+500), 
        #     arrowprops=dict(facecolor='black', width=0.5, headwidth=2, headlength=2, shrink=0.05))
    # invert y axis
    lim = plt.ylim()    
    plt.ylim((lim[1],lim[0]))
    # plt.xticks(rotation=-90)
    # plt.yticks(rotation=-90)
    # plt.xlabel(rotation=-90)
    # plt.ylabel(rotation=-180)

    plt.grid(False)
    plt.savefig(os.path.join(ini.t2FileDirFp,fn))
    print("saved:", os.path.join(ini.t2FileDirFp,fn))
    plt.close()
    return fn

def save_gif(fp_var_list_list, variables, ini, args):
    print("[makeVtu.createGif] create GIF")
    for i, fp_var_list in enumerate(fp_var_list_list):
        if (len(fp_var_list)<=1):
            print(f"[makeVtu.createGif] Length of slice data:{variables[i]}",
                    f" in output.listing <= 1. Skip create GIF.")
        else:
            print(f"[makeVtu.createGif] data:{variables[i]}",
                    f" number of total frames of GIF={len(fp_var_list)}")
            toGif = []
            for img in fp_var_list:
                toGif.append(Image.open(img, mode='r'))
                if not args.plotsProfileAll: os.remove(img)
            toGif[0].save(os.path.join(ini.savefigFp,f"{variables[i]}.gif"),
                    save_all=True, append_images=toGif[1:], optimize=False, 
                    duration=100, loop=0)

def save_gif2(fp_list_list, gifnameheaders, saveDir, duration=100):
    print("[makeVtu.createGif] create GIF")
    for i, fp_list in enumerate(fp_list_list):
        if (len(fp_list)<=1):
            print(f"[makeVtu.createGif] Length of slice data:{gifnameheaders[i]}",
                    f" in output.listing <= 1. Skip create GIF.")
        else:
            print(f"[makeVtu.createGif] data:{gifnameheaders[i]}",
                    f" number of total frames of GIF={len(fp_list)}")
            toGif = []
            for img in fp_list:
                toGif.append(Image.open(img, mode='r'))
                # os.remove(img)
            toGif[0].save(os.path.join(saveDir,f"{gifnameheaders[i]}.gif"),
                    save_all=True, append_images=toGif[1:], optimize=False, 
                    duration=duration, loop=0)


# if option -pl, -pa given, plot profile of region
if args.plotsProfileAll or args.plotsProfileLast or args.createGif :
    # write
    if II['simulator']==SIMULATOR_NAME_T3:
        variables = ini.plot.slice_plot_variables_T3
    if II['simulator']==SIMULATOR_NAME_T2:
        variables = ini.plot.slice_plot_variables_T2

    import matplotlib.pyplot as plt
    if args.plotsProfileAll or args.createGif:
        print("[makeVtu.plotsProfileAll] create snapshots ")

        fp_var_list_list = [[] for _ in range(0,len(ini.plot.profile_lines_list))]
        gifnameheader = [[] for _ in range(0,len(ini.plot.profile_lines_list))]
        for i,_ in enumerate(ini.plot.profile_lines_list): 
            for var in variables: 
                fp_var_list_list[i].append([])
                gifnameheader[i].append(f"{var}_line{i}")
        
        allTimesteps = t2o.readAllTimestepsFromFOFT(ini)
        time_last_image_saved = 0
        atFirstFlg = True
        stepNow = II['print_interval'] 
        print(f"CREATE GIF  minimum interval sec:",
                f" {ini.plot.gif_minimun_print_interval_sec}[s]")
        exists_next_step = True
        while exists_next_step:
            # this loop start at step==1
            # always save snapshot at first timestep
            stepNow += II['print_interval'] # !lst2.stepだと正しくない場合がある
            if len(allTimesteps) >= stepNow:
                timeNow = allTimesteps[stepNow-1] 
            else:
                continue
            if not atFirstFlg:
                # if interval of snapshot is too short, skip saving snapshot.
                dt = timeNow - time_last_image_saved
                if dt < ini.plot.gif_minimun_print_interval_sec: 
                    # skip this timestep and go next
                    print(f"    SKIP: step={stepNow} time={timeNow}[s]")
                    continue

            # save snapshot
            print(f"    save: step={stepNow} time={timeNow}[s]")
            time_last_image_saved = timeNow
            # turn off flg
            atFirstFlg = False

            df_elem = lst2.element.DataFrame
            df_conn = lst2.connection.DataFrame
            for l, line in enumerate(ini.plot.profile_lines_list):
                for i, var_name in enumerate(variables):
                    fp = original_plot(var_name, lst2.time, df_elem, line, l, ini, datG, plt, 
                                       saveDir=ini.t2FileDirFp, df_conn=df_conn,
                                       extension='png' if args.createGif else 'pdf')
                    if fp is not None and os.path.isfile(fp): 
                        fp_var_list_list[l][i].append(fp)
                    
            exists_next_step = lst2.next()

        # print(fp_var1_list)
        # print(fp_var2_list)

    if args.createGif:
        for i,_  in enumerate(ini.plot.profile_lines_list):
            save_gif2(fp_var_list_list[i], gifnameheader[i], ini.savefigFp, duration=30)

    if args.plotsProfileLast:
        lst2.last()
        print(f"PROFILE save: step={lst2.step} time={lst2.time}[s]")
        df_elem = lst2.element.DataFrame
        df_conn = lst2.connection.DataFrame
        # plt.show()
        plt.close()
        for l, line in enumerate(ini.plot.profile_lines_list):
            for i, var_name in enumerate(variables):
                fp = original_plot(var_name, lst2.time, df_elem, line, l, ini, datG, plt, saveDir=ini.t2FileDirFp, df_conn=df_conn, overWrites=True)
                if fp is not None: shutil.copy2(fp, ini.t2FileDirFp)

# if option -plc given, plot profile of region
if args.plotsProfileLastCsv or args.createGifCsv or args.plotsProfileAllCsv:
    # write
    if II['simulator']==SIMULATOR_NAME_T3:
        variables = ini.plot.slice_plot_variables_T3
    if II['simulator']==SIMULATOR_NAME_T2:
        variables = ini.plot.slice_plot_variables_T2

    # read all printed result from OUTPUT_ELEME.csv
    outAllDfList, time, label, unit = t2o.read_output_eleme_csv(ini)
    # read all timesteps from FOFT file
    allTimesteps = t2o.readAllTimestepsFromFOFT(ini)

    import matplotlib.pyplot as plt
    if args.createGifCsv or args.plotsProfileAllCsv:
        # TODO TIMEが指定された場合にも正しく出力するようにする。この場合II['print_interval'] は使えない
        print("[makeVtu.plotsProfileAll] create snapshots ")
        
        fp_var_list_list = [[] for _ in range(0,len(ini.plot.profile_lines_list))]
        gifnameheader = [[] for _ in range(0,len(ini.plot.profile_lines_list))]
        for i,_ in enumerate(ini.plot.profile_lines_list): 
            for var in variables: 
                fp_var_list_list[i].append([])
                gifnameheader[i].append(f"{var}_line{i}")
        
        time_last_image_saved = 0
        atFirstFlg = True
        stepNow = II['print_interval'] 
        print(f"CREATE GIF  minimum interval sec:",
                f" {ini.plot.gif_minimun_print_interval_sec}[s]")
        for res_index, out in enumerate(outAllDfList):
            # !! this loop start at step>=2
            # always save snapshot at first timestep
            stepNow = (res_index+1) * II['print_interval'] 
            if len(allTimesteps) >= stepNow:
                timeNow = allTimesteps[stepNow-1] 
                # timeNow = time[stepNow-1] 
            else:
                continue
            if not atFirstFlg:
                # if interval of snapshot is too short, skip saving snapshot.
                dt = timeNow - time_last_image_saved
                if dt < ini.plot.gif_minimun_print_interval_sec: 
                    # skip this timestep and go next
                    print(f"    SKIP: step={stepNow} time={timeNow}[s]")
                    continue

            # save snapshot
            print(f"    save: step={stepNow} time={timeNow}[s]")
            time_last_image_saved = timeNow
            # turn off flg
            atFirstFlg = False
            df_elem = out
            for l, line in enumerate(ini.plot.profile_lines_list):
                for i, var_name in enumerate(variables):
                    fp = original_plot(var_name, timeNow, df_elem, line, l, ini, datG, plt, 
                                       saveDir=ini.t2FileDirFp, df_conn=None,
                                       extension='png' if args.createGifCsv else 'pdf')
                    if fp is not None: fp_var_list_list[l][i].append(fp) 

        # print(fp_var1_list)
        # print(fp_var2_list)

    if args.createGifCsv:
        for i,_  in enumerate(ini.plot.profile_lines_list):
            save_gif2(fp_var_list_list[i], gifnameheader[i], ini.savefigFp, duration=100)

    if args.plotsProfileLastCsv:
        print(f"PROFILE save: step={len(allTimesteps)} time={allTimesteps[-1]}[s]")
        df_elem = outAllDfList[-1]
        # plt.show()
        plt.close()

        for l, line in enumerate(ini.plot.profile_lines_list):
            for i, var_name in enumerate(variables):

                fp = original_plot(var_name, allTimesteps[-1], df_elem, line, l, ini, datG, plt, saveDir=ini.t2FileDirFp, df_conn=None, overWrites=True)
                if fp is not None: shutil.copy2(fp, ini.t2FileDirFp)
                # geo.layer_plot(layer=1800, 
                #             variable=t2o.dfCleanElem(df_elem,var_name, ini.mesh.convention),
                #             variable_name=var_name,
                #             colourbar_limits=t2o.get_cbar_limits(var_name),
                #             plt=plt,
                #             unit=t2o.get_unit(var_name))
                # plt.savefig(os.path.join(ini.t2FileDirFp,f'lay{var_name}_{allTimesteps[-1]}.png'))
                # print("saved:", os.path.join(ini.t2FileDirFp,f'lay{var_name}_{allTimesteps[-1]}.png'))
                # # plt.show()
                # plt.close()


# if option -t given, plot time series for specified element
if args.plotsTimeSeries:
    """read result from t2listing"""
    plot = ini._readInputIniSettingPlot()
    t2o.plot_param_time(
        ini.tOutFileFp, plot['blocksPlotTimeseries'], 
        plot['variablesPlotTimeseries'])

if args.plotsTimeSeriesSurface:
    """read result from t2listing"""
    lst2.first()
    t2o.plot_surface_flow_lst(lst2)

# plot from COFT
if args.plotsTimeSeriesSurfaceSumAllCoft:
    """read result from COFT*csv files"""
    t2o.plot_spatial_flow_distribution_at_surface_COFT_radial(ini, dat, geo, 
                                saveDir=ini.savefigFp)
    t2o.plot_surface_flow_COFT(ini, dat, geo, saveDir=ini.t2FileDirFp, 
                                xrangeMax=ini.plot.xoft_t_range)
    t2o.plot_surface_flow_COFT(ini, dat, geo, saveDir=ini.t2FileDirFp, 
                                xrangeMax=ini.plot.xoft_t_range,
                                isXscaleLog=True, inversesY=False)
if args.plotsTimeSeriesSurfaceAreaCoft:
    t2o.plot_surface_flow_COFT_multiple_area(
                                ini, dat, geo, saveDir=ini.t2FileDirFp, 
                                xrangeMax=ini.plot.xoft_t_range,
                                isXscaleLog=True, inversesY=False)
    t2o.plot_surface_flow_COFT_multiple_area(
                                ini, dat, geo, saveDir=ini.t2FileDirFp, 
                                xrangeMax=ini.plot.xoft_t_range,
                                isXscaleLog=False, inversesY=False)
# plot from FOFT
if args.plotsTimeSeriesFoft:
    """read result from FOFT*csv files"""
    t2o.plot_block_timeseries_FOFT(ini, dat, saveDir=ini.t2FileDirFp, 
                                xrangeMax=ini.plot.xoft_t_range)
    t2o.plot_block_timeseries_FOFT(ini, dat, saveDir=ini.t2FileDirFp, 
                                xrangeMax=ini.plot.xoft_t_range, isXscaleLog=True)

# plot INCON & SAVE
if args.inconColumn:
    t2o.column_plot_INCON3(ini)

# if option -v given, write *.vtu files for paraview
if args.writesVtu:
    # write
    lst2.last()
    if dat.parameter['print_level'] <= 1 :
        lst2.write_vtk(geo, ini.resultVtuFileFp, None, time_unit="s")
    else : 
        lst2.write_vtk(geo, ini.resultVtuFileFp, dat.grid, None, False, 
                        time_unit="s", blockmap=dat.grid.blockmap(geo))

if args.interval is not None:
    import matplotlib.pyplot as plt
    flowdata_dict_list, timesteps = t2o.surface_flow_map_from_COFT(ini, dat, geo)
    
    if flowdata_dict_list is not None: 
    
        gifnameheader1 = []
        gifnameheader2 = []
        fps1 = []
        fps2 = []
        for key,val in flowdata_dict_list[0].items():
            gifnameheader1.append(f"{key}_lim0")
            gifnameheader2.append(f"{key}_lim1")
            fps1.append([])
            fps2.append([])

        for i, fd in enumerate(flowdata_dict_list):
            if i%args.interval != 0: continue
            for j, (key,val) in enumerate(fd.items()):
                timeNow=timesteps[i]
                title = f"{key}/m^2 \n t={t2o.sec2year(timeNow)}"
                fn1 = original_surfacemap(key, val, ini, geo, title, info=f"lim0_time{i}", saveDir=ini.t2FileDirFp, extension='png')
                fn2 = original_surfacemap(key, val, ini, geo, title, info=f"lim1_time{i}", saveDir=ini.t2FileDirFp, cbarlim=t2o.get_cbar_limits_flow(key), extension='png')
                fps1[j].append(fn1)
                fps2[j].append(fn2)
        else:
            # last
            for j, (key,val) in enumerate(fd.items()):
                timeNow=timesteps[i]
                title = f"{key}/m^2 \n t={t2o.sec2year(timeNow)}"
                fn1 = original_surfacemap(key, val, ini, geo, title, info=f"lim0_time{i}", saveDir=ini.t2FileDirFp, extension='png')
                fn2 = original_surfacemap(key, val, ini, geo, title, info=f"lim1_time{i}", saveDir=ini.t2FileDirFp, cbarlim=t2o.get_cbar_limits_flow(key), extension='png')
                original_surfacemap(key, val, ini, geo, title, info=f"lim0_time{i}", saveDir=ini.t2FileDirFp, extension='pdf')
                original_surfacemap(key, val, ini, geo, title, info=f"lim1_time{i}", saveDir=ini.t2FileDirFp, cbarlim=t2o.get_cbar_limits_flow(key), extension='pdf')
                fps1[j].append(fn1)
                fps2[j].append(fn2)

        save_gif2(fps1, gifnameheader1, ini.savefigFp, duration=300)
        save_gif2(fps2, gifnameheader2, ini.savefigFp, duration=300)

if args.surfaceFlowMap:
    if ini.mesh.type == AMESH_VORONOI:
        import matplotlib.pyplot as plt
        lst2.last()
        flowdata_dict = t2o.surface_flow_map_from_listing(ini, dat, geo, lst2)
        for key,val in flowdata_dict.items():
            title = f"{key}/m^2 \n t={t2o.sec2year(lst2.time)}"
            fp1 = original_surfacemap(key, val, ini, geo, title, info=f"lim0_time{lst2.step}lst", overWrites=True)
            fp2 = original_surfacemap(key, val, ini, geo, title, info=f"lim1_time{lst2.step}lst", overWrites=True, cbarlim=t2o.get_cbar_limits_flow(key))
            shutil.copy2(fp1, ini.t2FileDirFp)
            shutil.copy2(fp2, ini.t2FileDirFp)
        """ plot from COFT
        flowdata_dict_list, timesteps = t2o.surface_flow_map_from_COFT(ini, dat, geo)
        for key,val in flowdata_dict_list[len(timesteps)-1].items():
            timeNow=np.array(timesteps)[-1]
            title = f"{key}/m^2 \n t={t2o.sec2year(timeNow)}"
            original_surfacemap(key, val, ini, geo, title, f"time{len(timesteps)-1}coft")
        """


if ini.toughInput['simulator'] != SIMULATOR_NAME_T2:
    t2o.plot_timestep_growth(ini, dat, saveDir=ini.t2FileDirFp)