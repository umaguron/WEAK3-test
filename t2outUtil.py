# get directory name where this script is located
from import_pytough_modules import *
import define_logging
#
from t2listing import *
from t2data import *
import numpy as np
import os
from matplotlib.backends.backend_pdf import PdfPages
import re
import matplotlib.pyplot as plt
import matplotlib as mpl
import math
import _readConfig
# from define import *
import mulgrids
import pandas as pd
import copy
import glob
from scipy import interpolate
from makeGridAmeshVoro import blockname 
import quistMarshall_data_interpl as qm
from iapws import IAPWS97
sys.path.append(os.path.join(baseDir,"scriptsCreateFig"))
import brine_density_module as bdm


# matplot setting
plt.rcParams['font.family'] ='sans-serif'#使用するフォント
plt.rcParams['xtick.direction'] = 'in'#x軸の目盛線が内向き('in')か外向き('out')か双方向か('inout')
plt.rcParams['ytick.direction'] = 'in'#y軸の目盛線が内向き('in')か外向き('out')か双方向か('inout')
plt.rcParams['xtick.major.width'] = 1.0#x軸主目盛り線の線幅
plt.rcParams['ytick.major.width'] = 1.0#y軸主目盛り線の線幅
plt.rcParams['font.size'] = 8 #フォントの大きさ
plt.rcParams['axes.linewidth'] = 1.0# 軸の線幅edge linewidth。囲みの太さ
plt.rcParams['axes.labelsize'] = 'medium'
plt.rcParams['axes.grid'] = True

# COFT variable name TOUGH3
heat = 'HEAT'
totalf = 'FLOW_total'
totalheat_heatByFlow = 'test_heatOtherThanFluidFlow'
flog = 'FLOW_G' 
flol = 'FLOW_L' 
"""
flog_w = 'FLOW_G_WATER' 
flog_nacl = 'FLOW_G_NaCl' 
flog_co2 = 'FLOW_G_CO2' 
flol_w = 'FLOW_L_WATER' 
flol_nacl = 'FLOW_L_NaCl' 
flol_co2 = 'FLOW_L_CO2' 
# col index
iheat = 1 
iflog = 2
iflol = 3
iflog_w = 4  
iflog_nacl = 5 
iflog_co2 = 6
iflol_w = 7
iflol_nacl = 8  
iflol_co2 = 9
"""
NaCl_FORMULA_WEIGHT = 58.5
NaCl_MOL_KG = NaCl_FORMULA_WEIGHT/1000
# func for converting NaCl molality[mol/kg] to molar[mol/L]
molality2molar = lambda molal, density: molal*density/(1+molal*NaCl_MOL_KG)
# func for converting NaCl molar[mol/L] to molality[mol/kg]
molar2molality = lambda molar, density: molar/(density-molar*NaCl_MOL_KG)
# func for converting NaCl molality[mol/kg] to mass fraction
molality2massfrac = lambda molal: molal*NaCl_MOL_KG/(1+molal*NaCl_MOL_KG)
# func for converting NaCl mass fraction to molar[mol/L] 
massfrac2molar = lambda x_nacl, density: x_nacl*density/NaCl_MOL_KG 
# func for converting NaCl mass fraction to molality[mol/kg] 
massfrac2molality = lambda x_nacl: x_nacl/(1-x_nacl)/NaCl_MOL_KG 

# mole frac <-> mass frac
x_mol2x_wt = lambda x_mol: 58.5*x_mol/(40.5*x_mol+18)
x_wt2x_mol = lambda x_wt: 18*x_wt/(58.5-40.5*x_wt)


def escape_t3outfiles(ini:_readConfig.InputIni):
    """escape t3outfiles to T3OUT_ESCAPE_DIRNAME set in setting.ini"""
    if ini.t2FileDirFp == ini.t3outEscapeFp: 
        return
    elif os.path.isdir(ini.t3outEscapeFp):
        return
    else:
        os.makedirs(ini.t3outEscapeFp)
        import shutil
        for f in os.listdir(ini.t2FileDirFp):
            if re.search(r"[FC]OFT.*csv", f) or re.search(r"^\..*", f) \
                    or re.search(r"CONNE*", f) or re.search(r"ELEME*", f): 
                print(f"    escape {f}")
                shutil.move(os.path.join(ini.t2FileDirFp,f), ini.t3outEscapeFp)

def create_savefig_dir(ini:_readConfig.InputIni):
    if ini.t2FileDirFp == ini.savefigFp: 
        return
    elif os.path.isdir(ini.savefigFp):
        return
    else:
        os.makedirs(ini.savefigFp)

def plot_param_time(listing_fp, elem_nm_list, param_list):
    """
    渡されたlistingファイルを読み、各パラメータの時系列変化をプロットする。
    結果はpdfでlistingファイルのある階層に保存する

    Parameters
    ----------
    listing_fp : str
        読み込むlistingファイルのパス
    elem_nm_list : list
        結果をプロットしたい要素名のリスト
    param_list : list
        プロットしたいパラメーター名のリスト
    """
    # はじめに結果ファイルの存在確認
    if not os.path.exists(listing_fp):
        print("no listing file")
        raise FileNotFoundError

    save_fp = re.sub("[^/]*listing", "rslt_plt.pdf",  listing_fp)
    num_elem = len(elem_nm_list)
    # 結果の読み込み
    lst = t2listing(listing_fp)
    
    # check convergence
    # print(lst.convergence['T'])
    # print(lst.convergence['P'])
    # print(lst.convergence['SG'])
    # print(lst.convergence['PCO2'])
    # print(lst.convergence['XCO2(av)'])

    # matplot setting
    mksize = 3 # マーカーの大きさ
    size_x = 19 # cm
    size_y = 7 * num_elem # cm
    
    # プロットの配置　行・列の数
    num_row = num_elem
    num_col = len(param_list)
    # 現在プロットしている場所の番号
    plt_pos = 1

    # figure作成
    fig = plt.figure(figsize=(size_x * 3.14 / 8, size_y * 3.14 / 8))
    plt.clf()


    # タイムステップ数数カウント用
    lc=0

    # 時系列取得
    # 読み込み位置リセット
    lst.first()
    # 取得パラメーター初期化
    t = []
    res_arr = []
    for a in elem_nm_list:
        tmp = []
        for b in param_list:
            tmp.append([])
        res_arr.append(tmp)
    # 取得
    while True:
        lc+=1  
        # 時間軸取得
        t.append(lst.time)
        # 要素ごと
        for en, elem_nm in enumerate(elem_nm_list):
            # パラメーターの種類毎に結果を格納
            for pn, param in enumerate(param_list):
                res_arr[en][pn].append(lst.element[elem_nm][param])
        if not lst.next(): break
    print("timeseries retrieved;  num timestep: " + str(lc))
            
    # 取得した時系列のプロット
    for en, elem_nm in enumerate(elem_nm_list):
        print("elem name: " + elem_nm)
        for pn, param in enumerate(param_list):
            ax = plt.subplot(num_row, num_col, plt_pos) # subplot returns axis 
            ax.set_title(param + ' @ ' + elem_nm)
            label = _xaxisFormatter(t, ax)  
            # format yaxis
            if param == "PRES":
                ax.yaxis.set_major_formatter(
                    mpl.ticker.FuncFormatter(lambda x, 
                                             pos: f"{x/10**5:,.2f} bar"))
            # plot
            plt.plot(t, res_arr[en][pn], marker='o', markersize=mksize, 
                     color='b', label=param + ' at ' + elem_nm )
            # label
            # plt.xlabel('time(second)')
            plt.xlabel(label)
            plt.ylabel(param)
            plt_pos += 1
            print("  " + param + " plotted")

    plt.tight_layout()

    # set path
    pp = PdfPages(save_fp)

    # save figure
    pp.savefig(fig, transparent=True)
    print("saved at " + save_fp)

    # close file
    pp.close()

    # geo.layer_plot(-600, np.insert(lst.element['T'], 0, 0), 'Temperature', '$\degree$C', contours = np.arange(100,200,25), flow=lst.connection['FLO(AQ.)'])
    # geo.slice_plot([np.array([0, 550]), np.array([1100, 550])], np.insert(lst.element['T'], 0, 0), 'Temperature', '$\degree$C', flow=lst.connection['FLO(AQ.)'], )
    #geo.line_plot([500, 500, 0], [500, 500, 881.1], lst3.)

def _xaxisFormatter(time:list, ax):
    """[summary]

    Args:
        time (list): [description]
        ax (axis): [description]

    Returns:
        label [str]: [description]
    """
    # format xaxis
    secOverYear = 3600*24*365.25
    secOverDay = 3600*24
    secOverHour = 3600
    secOverMin = 60
    if max(time) > secOverDay*1000:
        secOverUnit = secOverYear
        label = 'year'
    elif max(time) > secOverHour*100:
        secOverUnit = secOverDay
        label = 'day'
    elif max(time) > secOverMin*300:
        secOverUnit = secOverHour
        label = 'hour'
    elif max(time) > 300:
        secOverUnit = secOverMin
        label = 'min.'
    else:
        secOverUnit = 1
        label = 'sec.'
        
    # calc. ticker position
    unit = max(time)/secOverUnit
    log10_unit = math.log10(unit)
    log10_unit_floor = math.floor(log10_unit)
    unit_floor = 10**log10_unit_floor
    sec_floor = unit_floor * secOverUnit

    # set FuncFormatter
    ax.xaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, pos: f"{x/secOverUnit:,.0f}"))
    # set Locator
    if max(time)/sec_floor < 5 :
        ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(sec_floor)) 
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(sec_floor/10))
    elif max(time)/sec_floor >= 5 :
        ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(sec_floor*2)) 
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(sec_floor/10*2))

    return label

def _xy_axisFormatter(max_t:float, axis:mpl.axis.Axis):
    """[summary]

    Args:
        max_t (float): [description]
        axis (mpl.axis.Axis): ax.xaxis or ax.yaxis

    Returns:
        label [str]: [description]
    """
    # format xaxis
    secOverYear = 3600*24*365.25
    secOverDay = 3600*24
    secOverHour = 3600
    secOverMin = 60
    if max_t > secOverDay*1000:
        secOverUnit = secOverYear
        label = 'year'
    elif max_t > secOverHour*100:
        secOverUnit = secOverDay
        label = 'day'
    elif max_t > secOverMin*300:
        secOverUnit = secOverHour
        label = 'hour'
    elif max_t > 300:
        secOverUnit = secOverMin
        label = 'min.'
    else:
        secOverUnit = 1
        label = 'sec.'
        
    # calc. ticker position
    unit = max_t/secOverUnit
    log10_unit = math.log10(unit)
    log10_unit_floor = math.floor(log10_unit)
    unit_floor = 10**log10_unit_floor
    sec_floor = unit_floor * secOverUnit

    # set FuncFormatter
    axis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, pos: f"{x/secOverUnit:,.0f}"))
    # set Locator
    if max_t/sec_floor < 5 :
        axis.set_major_locator(mpl.ticker.MultipleLocator(sec_floor)) 
        axis.set_minor_locator(mpl.ticker.MultipleLocator(sec_floor/10))
    elif max_t/sec_floor >= 5 :
        axis.set_major_locator(mpl.ticker.MultipleLocator(sec_floor*2)) 
        axis.set_minor_locator(mpl.ticker.MultipleLocator(sec_floor/10*2))

    return label

def dfCleanElem(df_elem:pd.DataFrame, param: str):
    """
    return result array of all element except 'INJxx', 
    which added to grid by tough3exec_ws.py
    Args:
        df_elem (DataFrame): [description]
        param (str): name of parameter
    Returns:
        numpy.array: result array of all element
    """        
    # get index of element in Series 'row' which includes 'INJ', and roop
    for i in list(df_elem[df_elem.row.str.contains('INJ')].index):
        """drop the row of index i from dataFrame"""
        tmp = df_elem.drop(i)
        df_elem = tmp
    return np.array(df_elem[param])

def dfCleanElem2(df_elem:pd.DataFrame):
    """
    return reconstructed dataframe except rows including 'INJxx', 
    which added to grid by tough3exec_ws.py
    Args:
        df_elem (DataFrame): [description]
    Returns:
        numpy.array: result array of all element
    """        
    # get index of element in Series 'row' which includes 'INJ', and roop
    for i in list(df_elem[df_elem.row.str.contains('INJ')].index):
        """drop the row of index i from dataFrame"""
        tmp = df_elem.drop(i)
        df_elem = tmp
    return df_elem

def _includesINJinTuple(tuple):
    """if tuple passed includes "INJ", returns True"""
    ret = False
    for t in tuple:
        ret = "INJ" in t or ret
    # if ret: print(tuple)
    return ret

def dfCleanConn(df_conn:pd.DataFrame):
    """
    return result array of all element except 'INJxx', 
    which added to grid by tough3exec_ws.py
    Args:
        df_conn ([DataFrame]): [description]
    Returns:
        df_conn 
    """        
    # get index of connection for which mapFunc returns True, and roop
    exclude = list(df_conn[df_conn.row.map(_includesINJinTuple)].index)
    for i in exclude:
        print(f"exclude {df_conn[df_conn.index==i].row[i]}")
    for i in exclude:
        tmp = df_conn.drop(i)
        df_conn = tmp
    return df_conn

def _includesATMinTupleElem0(tuple):
    """if tuple[0] passed includes "ATM", returns True"""
    ret = "ATM" in tuple[0]
    # if ret: print(tuple)
    return ret
def _includesATMinTupleElem1(tuple):
    """if tuple[1] passed includes "ATM", returns True"""
    ret = "ATM" in tuple[1]
    # if ret: print(tuple)
    return ret

def dfGetSurfaceBudget(df_conn):
    """returns surface HEAT budget (upward +)

    Args:
        df_conn ([pandas.DataFrame]): [description]

    Returns:
        pandasSeries: [description]
    """
    sr_sumUppwd = df_conn[df_conn.row.map(_includesATMinTupleElem0)].\
                    sum(numeric_only=True)
    sr_sumDownwd = df_conn[df_conn.row.map(_includesATMinTupleElem1)].\
                    sum(numeric_only=True)
    return sr_sumUppwd.add(sr_sumDownwd*-1)

def _dfGetInjBudget(df_conn):
    """returns surface HEAT budget (upward +)

    Args:
        df_conn ([pandas.DataFrame]): [description]

    Returns:
        pandasSeries: [description]
    """
    sr_sum = df_conn[df_conn.row.map(_includesINJinTuple)].\
                sum(numeric_only=True)
    return sr_sum

def plot_surface_flow_lst(lst: t2listing):
    """
    plots flow at surface and injblock 
    data is read from listing file.
    pdf files are saved in same dir where listing file put in.

    Args:
        lst (t2listing): [description]
    """
    resArr = {}
    resArrInj = {}
    save_fp = re.sub("[^/]*listing", "surface_flow.png",  lst.filename)
    save_fp_inj = re.sub("[^/]*listing", "injection_cell.png",  lst.filename)
    dfc = lst.connection.DataFrame
    budget = dfGetSurfaceBudget(dfc)
    budgetInj = _dfGetInjBudget(dfc)
    for variable in list(budget.index):
        resArr[variable] = []
        resArr[variable].append(budget[variable])
    for variable in list(budgetInj.index):
        resArrInj[variable] = []
        resArrInj[variable].append(budgetInj[variable])
   
    while lst.next():
        dfc = lst.connection.DataFrame
        budget = dfGetSurfaceBudget(dfc)
        budgetInj = _dfGetInjBudget(dfc)
        for variable in list(budget.index):
            resArr[variable].append(budget[variable])
        for variable in list(budgetInj.index):
            resArrInj[variable].append(budgetInj[variable])

    fig = plt.figure(figsize=(15, 5))
    fig2 = plt.figure(figsize=(15, 5))
    t = lst.fulltimes
    for i,variable in enumerate(list(budget.index)):
        ax = fig.add_subplot(1, len(budget.index), i+1) # subplot returns axis 
        ax2 = fig2.add_subplot(1, len(budget.index), i+1) # subplot returns axis 
        ax.set_title(variable)
        ax2.set_title(variable)
        # format xaxis
        label = _xaxisFormatter(t, ax)
        label2 = _xaxisFormatter(t, ax2)        
        # plot
        ax.plot(t, resArr[variable], marker='o', markersize=3, color='b', 
                label=variable )
        ax2.plot(t, resArrInj[variable], marker='o', markersize=3, color='b', 
                label=variable )
        # label
        # plt.xlabel('time(second)')
        ax.set_xlabel(label)
        ax2.set_xlabel(label2)
        # plt.ylabel(variable)
        print("  " + variable + " plotted")
    fig.tight_layout()
    fig2.tight_layout()
    fig.savefig(save_fp)
    fig2.savefig(save_fp_inj)
    plt.show()

class SurfaceAreaCircle(object):
    """[summary]
    define circuler area on the surface of the computational domain
    To generate this object,
    area = t2outUtil.SurfaceAreaCircle([center_x[m], center_y[m], radius[m]], label="XXX")

    Args:
        object ([Boolean]): whether passed column is within this surface area 
    """
    def __init__(self, range, label:str):
        """
        range: [center_x[m], center_y[m], radius[m]]
        """
        self.range = range
        self.label = label
    
    def isColumnInArea(self, col:column, geo:mulgrid):
        """[summary]
        Check if the given column is included in this circular surface area.
        Args:
            col (column): column object
            geo (mulgrid): mulgrid object
        Returns:
            [Boolean]: if included, returns True
        """
        layer_top = geo.column_surface_layer(col)
        centre = geo.block_centre(layer_top.name, col.name)
        if (centre[0]-self.range[0])**2+(centre[1]-self.range[1])**2 <= self.range[2]**2:
            return True
        return False    

def plot_surface_flow_COFT(
        ini:_readConfig.InputIni, dat:t2data, geo:mulgrids, 
        saveDir:str=None, xrangeMax:list=None, isXscaleLog=False, 
        isYscaleLog=False, inversesY=False):
    """
    plots flow at surface and injblock. 
    data is read from multiple COFT files.
    pdf files are saved in specified dir.
    if saveDir is not given, pdfs are saved in ini.t2FileDirFp 

    Args:
        ini (_readConfig.InputIni): [description]
        dat (t2data): [description]
        geo (mulgrids): [description]
        saveDir (str, optional): [description]. Defaults to None.
        xrangeMax (list, optional): range of time to plot. 
    """
    # escape outputfiles
    escape_t3outfiles(ini)
    create_savefig_dir(ini)
    if saveDir is None: saveDir = ini.t2FileDirFp
    
    ii = ini.toughInput
    # layer_top = geo.layerlist[1]  # get property of top layer 
    """
    # prepare container suf
    conn_list_suf = {}
    sufAreaObjects = []
    for label,range in COFT_TS_AREAS.items():
        sufAreaObjects.append(SurfaceAreaCircle(range, label))
        conn_list_suf[label] = []
    """
    conn_list_suf = []
    conn_list_inj = []

    # get surface-atmos connection list
    if ii['prints_hc_surface']:
        for col in geo.columnlist:
            layer_top = geo.column_surface_layer(col)
            blockname_top = geo.block_name(layer_top.name, col.name)
            conn = (blockname_top,'ATM 0')
            if (conn[0],conn[1]) in dat.grid.connection \
                    or (conn[1],conn[0]) in dat.grid.connection:
                conn_list_suf.append(conn)
            """
            if (conn[0],conn[1]) in dat.grid.connection \
                    or (conn[1],conn[0]) in dat.grid.connection:
                for obj in sufAreaObjects:
                    if obj.isColumnInArea(col, geo):
                        conn_list_suf[obj.label].append(conn)
            """
    else: 
        print(f"[t2outUtil.plot_surface_flow_COFT] option "\
                +"'prints_hc_surface' is False in ini file. skip")
        return

    # get injblk-atmos connection list
    if ii['prints_hc_inj']:
        for k in dat.grid.connection.keys():
            if 'INJ' in k[1]:
                conn_list_inj.append((k[1],k[0]))
            elif 'INJ' in k[0]:
                conn_list_inj.append((k[0],k[1]))
    else: 
        print(f"[t2outUtil.plot_surface_flow_COFT] option "\
                +"'prints_hc_inj' is False in ini file. skip")
        return

    colsName4CalcNetFlow = \
        ['FLOF'] if ii['simulator']=='TOUGH2' else ['FLOW_L', 'FLOW_G']
    surfaceBudget, _, _ = _sum_COFTcsvs_inDir(
                        ini.t3outEscapeFp, conn_list_suf, 
                        colsName4CalcNetFlow,
                        timemax=None if xrangeMax is None else max(xrangeMax))
    """
    # get time series from COFT csv file
    surfaceBudget = {}    
    for obj in sufAreaObjects:
        surfaceBudget[obj.label].append(
            _sum_COFTcsvs_inDir(ini.t3outEscapeFp, conn_list_suf, colsName4CalcNetFlow))
    """
    injBudget, _, _ = _sum_COFTcsvs_inDir(
                        ini.t3outEscapeFp, conn_list_inj, 
                        colsName4CalcNetFlow, 
                        timemax=None if xrangeMax is None else max(xrangeMax))
    
    # surface flow
    ts_plotter({"ALL":surfaceBudget}, saveDir, "coft_surfaceflow", isXscaleLog, isYscaleLog, inversesY, xrangeMax)
    # inj flow
    ts_plotter({"ALL": injBudget}, saveDir, "coft_injflow", isXscaleLog, isYscaleLog, inversesY, xrangeMax)

def plot_surface_flow_COFT_multiple_area(
        ini:_readConfig.InputIni, dat:t2data, geo:mulgrids, 
        saveDir:str=None, xrangeMax:list=None, isXscaleLog=False, 
        isYscaleLog=False, inversesY=False):
    """
    plots surface flow within the pre-defined areas (define.COFT_TS_AREAS). 
    data is read from multiple COFT files.
    pdf files are saved in specified dir.
    if saveDir is not given, pdfs are saved in ini.t2FileDirFp 

    Args:
        ini (_readConfig.InputIni): [description]
        dat (t2data): [description]
        geo (mulgrids): [description]
        saveDir (str, optional): [description]. Defaults to None.
        xrangeMax (list, optional): range of time to plot. 
    """
    surfaceBudgetDict = get_surface_flow_COFT_multiple_area(ini, dat, geo, xrangeMax, remove_last_two=False)
    # plot
    if saveDir is None: saveDir = ini.t2FileDirFp
    ts_plotter(surfaceBudgetDict[SUF_SURFLOW_NET], saveDir, "coft_surfaceflow_area"+SUF_SURFLOW_NET, isXscaleLog, isYscaleLog, inversesY, xrangeMax)
    ts_plotter(surfaceBudgetDict[SUF_SURFLOW_DIRC1], saveDir, "coft_surfaceflow_area"+SUF_SURFLOW_DIRC1, isXscaleLog, isYscaleLog, inversesY, xrangeMax)
    ts_plotter(surfaceBudgetDict[SUF_SURFLOW_DIRC2], saveDir, "coft_surfaceflow_area"+SUF_SURFLOW_DIRC2, isXscaleLog, isYscaleLog, inversesY, xrangeMax)

def get_surface_flow_COFT_multiple_area(
        ini:_readConfig.InputIni, dat:t2data, geo:mulgrids, 
        xrangeMax:list=None, remove_last_two=True):
    """[summary]
    sum surface flow within the pre-defined areas (define.COFT_TS_AREAS). 
    data is read from multiple COFT files.

    Args:
        ini (_readConfig.InputIni): [description]
        dat (t2data): [description]
        geo (mulgrids): [description]
        xrangeMax (list, optional): [description]. Defaults to None.
        remove_last_two (Boolean): 
    Returns:
        [dict]: dictionary of dictionary of dictionary. 
            {
                SUF_SURFLOW_NET: {
                    'area1':{
                        'TIME(S)': pandas.Series,
                        'HEAT': pandas.Series,
                        'FLOW_(total)': pandas.Series,
                        'FLOW_G': pandas.Series,
                        ...
                    },
                    'area2': {
                        ...
                    }
                }, #** 'area1', 'area2' -> key of define.COFT_TS_AREAS
                SUF_SURFLOW_DIRC1: {...},
                SUF_SURFLOW_DIRC2: {...}
            }
    """
    # escape outputfiles
    escape_t3outfiles(ini)
    create_savefig_dir(ini)
    tb_savedir = os.path.join(ini.t2FileDirFp,DIR_SURFACE_FLOW_AREA_TABLE)

    # check existence of saved csv.
    if not os.path.isdir(tb_savedir):
        # if not found, reorganize COFT*.csv and save time table as csv. (for each 'area')
        reorganize_COFT_into_surface_flow_timetable_csv(ini,dat,geo)
    for SUF in (SUF_SURFLOW_NET,SUF_SURFLOW_DIRC1,SUF_SURFLOW_DIRC2):
        if len(glob.glob(os.path.join(tb_savedir,f"*{SUF}.csv")))==0:
            reorganize_COFT_into_surface_flow_timetable_csv(ini,dat,geo)
    
    # read saved csv
    surfaceBudgetDict={}
    for SUF in (SUF_SURFLOW_NET,SUF_SURFLOW_DIRC1,SUF_SURFLOW_DIRC2):
        surfaceBudgetDict[SUF]={}
        for csv in glob.glob(os.path.join(tb_savedir,f"*{SUF}.csv")):
            dftmp = pd.read_csv(csv)

            # Since the result value of the last time step is often irregular, 
            # it is removed from the data frame before plotting.
            if remove_last_two:
                dftmp = dftmp[dftmp.index<(len(dftmp.index)-2)]

            # get colname for 'TIME'
            colname_time = None
            for col in dftmp.columns:
                if re.search('TIME', col): colname_time=col
            
            # cut out dftmp by xrangeMax
            df = dftmp if xrangeMax is None else dftmp[dftmp[colname_time]<max(xrangeMax)]

            budget = {}
            for col in df.columns:
                if re.search('TIME', col):
                    budget['TIME'] = df[col]
                else:
                    budget[col.strip()] = df[col]
            # distinguish area from csv filename
            key = None
            for area in COFT_TS_AREAS:
                if area.strip().lower() in csv.lower():
                    key = area

            surfaceBudgetDict[SUF][key] = budget
    
    return surfaceBudgetDict


def reorganize_COFT_into_surface_flow_timetable_csv(
        ini:_readConfig.InputIni, dat:t2data, geo:mulgrids):
    """
    Read the COFT csv file and reorganize it into a timetable for each pre-defined "area".
    """
    ii = ini.toughInput
    # prepare container suf
    conn_list_dict = {}
    for_check = {} # only for check
    sufAreaObjects = []
    for label,range in COFT_TS_AREAS.items():
        sufAreaObjects.append(SurfaceAreaCircle(range, label))
        conn_list_dict[label] = []
        for_check[label] = [] # only for check

    # get surface-atmos connection list
    if not ii['prints_hc_surface']:
        print(f"[t2outUtil.plot_surface_flow_COFT] option "\
                +"'prints_hc_surface' is False in ini file. skip")
        return

    for col in geo.columnlist:
        layer_top = geo.column_surface_layer(col)
        blockname_top = geo.block_name(layer_top.name, col.name)
        conn = (blockname_top,'ATM 0')
        if (conn[0],conn[1]) in dat.grid.connection \
                or (conn[1],conn[0]) in dat.grid.connection:
            for obj in sufAreaObjects:
                if obj.isColumnInArea(col, geo):
                    conn_list_dict[obj.label].append(conn)
                    for_check[obj.label].append(col.name)
    
    # show area for check
    for key in conn_list_dict.keys():
        if "all" in key.lower(): continue
        print("#### "+key)
        for val in conn_list_dict[key]:
            print(f"    {val[0]}")
        geo.layer_plot(layer=None, column_names=for_check[key], title=f"area: {key}", plt=plt)
        for place, tup in TOPO_MAP_SYMBOL.items():
            plt.annotate(place, xy=tup, xytext=(tup[0], tup[1]+500), 
                arrowprops=dict(facecolor='black', width=0.5, headwidth=2, headlength=2, shrink=0.05))    
        plt.savefig(os.path.join(ini.t2FileDirFp,f"area-{key}"))
        print("saved:", os.path.join(ini.t2FileDirFp,f"area-{key}"))
        plt.close()
    """
    """

    colsName4CalcNetFlow = \
        ['FLOF'] if ii['simulator']=='TOUGH2' else ['FLOW_L', 'FLOW_G']

    # get time series from COFT csv file
    surfaceBudgetDict = {}    
    surfaceBudgetDict_dirc1 = {}    
    surfaceBudgetDict_dirc2 = {}    
    for key, conn_list in conn_list_dict.items():
        # check
        if len(conn_list)==0:
            # if any connections are contained in the current [surfaceArea], skip.
            continue
        surfaceBudgetDict[key], surfaceBudgetDict_dirc1[key], surfaceBudgetDict_dirc2[key] =\
            _sum_COFTcsvs_inDir(ini.t3outEscapeFp, conn_list, 
                                colsName4CalcNetFlow, 
                                timemax=None)

    # output surface flow timetable for each area
    tb_savedir = os.path.join(ini.t2FileDirFp,DIR_SURFACE_FLOW_AREA_TABLE)
    os.makedirs(tb_savedir, exist_ok=True)
    for area, sufBudget in surfaceBudgetDict.items():
        # area_dir = os.path.join(tb_savedir,area)
        # os.makedirs(area_dir, exist_ok=True)
        dfconcat = pd.concat(list(sufBudget.values()),axis=1)
        dfconcat.to_csv(os.path.join(tb_savedir,area.strip())+SUF_SURFLOW_NET+".csv", index=False)

    for area, sufBudget in surfaceBudgetDict_dirc1.items():
        # area_dir = os.path.join(tb_savedir,area)
        # os.makedirs(area_dir, exist_ok=True)
        dfconcat = pd.concat(list(sufBudget.values()),axis=1)
        dfconcat.to_csv(os.path.join(tb_savedir,area.strip())+SUF_SURFLOW_DIRC1+".csv", index=False)

    for area, sufBudget in surfaceBudgetDict_dirc2.items():
        # area_dir = os.path.join(tb_savedir,area)
        # os.makedirs(area_dir, exist_ok=True)
        dfconcat = pd.concat(list(sufBudget.values()),axis=1)
        dfconcat.to_csv(os.path.join(tb_savedir,area.strip())+SUF_SURFLOW_DIRC2+".csv", index=False)


def ts_plotter(budget_dict:dict, saveDir:str, info:str, isXscaleLog, isYscaleLog, inversesY, xrangeMax):
    """[summary]
    Args:
        budget_dict (dict): dictionary of budgets
            key-> name of each line, 
            item-> return value of t2outUtil._sum_COFTcsvs_inDir
        saveDir (str): [description]
        info (str): [description]
        isXscaleLog (bool): [description]
        isYscaleLog (bool): [description]
        inversesY ([type]): [description]
        xrangeMax ([type]): [description]
    """
    import matplotlib.cm as cm
    
    # get plot range and variable list
    t_max = None
    t_min = None
    variables = []
    if len(budget_dict) == 0: return
    for _, budget in budget_dict.items():
        if len(budget) == 0: continue
        if len(variables)==0:
            t_max = max(budget['TIME'])
            t_min = min(budget['TIME']) if isXscaleLog else 0
            for var in budget:
                variables.append(var)
    if len(variables)==0: return

    if xrangeMax is None:
        range = [t_min, t_max]
    else:
        if t_max < xrangeMax[1]: range = [t_min, t_max]
        else: range = xrangeMax

    fig = plt.figure(figsize=(12*INCH_OVER_CM, 6*INCH_OVER_CM*8)) # inch to cm
    for i,variable in enumerate(variables):
        if re.search('TIME', variable): continue
        ax = fig.add_subplot(len(variables)-1, 1, i) # subplot returns axis 
        ax.set_title(variable)

        # format xaxis
        if isXscaleLog: 
            # log scale
            ax.set_xscale('log')
            label = "[s]"
        else:
            # linear scale
            label = _xy_axisFormatter(range[1], ax.xaxis)
        # range
        ax.set_xlim(range, auto=False)
        # format yaxis
        # format yaxis
        if "HEAT" in variable:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x/10**6:,.2f} MW"))
        if 'FLOW' in variable:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x:,.３f} kg/s"))
                # mpl.ticker.FuncFormatter(lambda x, pos: f"{x*3600*24:,.2f} kg/day"))
        
        if isYscaleLog: ax.set_yscale('log')
        # plot multiple line
        for j, (key, budget) in enumerate(budget_dict.items()):
            if inversesY: y = budget[variable]*(-1)
            else: y = budget[variable]  
            ax.plot(budget['TIME'], y, marker='o', markersize=3, 
                    color=cm.viridis(j/len(budget_dict)), label=key)
        # label
        ax.set_xlabel(label)
        ax.legend()
        # plt.ylabel(variable)
        print("  " + variable + " plotted")

    info += "_logx" if isXscaleLog else ""
    info += "_logy" if isYscaleLog else ""
    info += "_inverse" if inversesY else ""
    savefp = os.path.join(saveDir, f"{info}.pdf")
    fig.tight_layout()
    fig.savefig(savefp)
    print("saved:", savefp)
    fig.clf()

def get_inner_surface_flow_sum_COFT_radial(
        ini:_readConfig.InputIni, radius=1000, timemax:float=None):
    """
    calc sum of flow discarging in the circle whose radius = given radius.
    data is read from multiple COFT files.

    Args:
        ini (_readConfig.InputIni): [description]
        radius (float, optional): [description]. Defaults 1000 [m]
    Returns:
        dictionary of dataframes : whose keys is variables name
    """
    # escape outputfiles
    escape_t3outfiles(ini)
    create_savefig_dir(ini)

    geo = mulgrid(ini.mulgridFileFp)

    ii = ini.toughInput
    layer_top = geo.layerlist[1]  # get property of top layer 
    conn_list_suf = []
    if ii['prints_hc_surface']:
        for i, col in enumerate(geo.columnlist):
            # radius (position of col from the centre)
            r = sum(geo.column_side_ratio[0:i+1])
            if r < radius:
                # if position of column is in the circle whose radius=radius(argument)
                blockname_top = geo.block_name(layer_top.name, col.name)
                conn_list_suf.append((blockname_top,'ATM 0'))
    else: 
        print(f"[t2outUtil.plot_surface_flow_COFT] option "\
                +"'prints_hc_surface' is False in ini file. skip")
        return

    colsName4CalcNetFlow = \
        ['FLOF'] if ii['simulator']=='TOUGH2' else ['FLOW_L', 'FLOW_G']
    surfaceBudget, _, _ = _sum_COFTcsvs_inDir(
                        ini.t3outEscapeFp, conn_list_suf, colsName4CalcNetFlow, 
                        timemax=timemax)
    return surfaceBudget

def _sum_COFTcsvs_inDir(
        dir: str, connections:list, 
        colsName4CalcNetFlow:list=["FLOW_L","FLOW_G"], 
        timemax:float=None, excludesInflow:bool=True):
    """
    sum all result in COFT csv files, whose connection is given by 
    connections:list, for each variables and return dictionary of dataframes 
    whose keys is variables name.
    Search COFTcsv files in given dir:str.
    flow direction is defined by order of element in tuple in connections
    (flow: elem[0] --> elem[1])
    2021/11/20
        net, inflow, outflowでそれぞれ合算するように変更
    Args:
        dir (str): 
            fullpath of directory includes COFT csv files
        connections (list of tuple): 
            list of tuple which represents connection (in no particular order)
        colsName4CalcNetFlow (list or tuple):
            list of column name of gas and liquid flow.
            (Used for calc total flow. Total flow is not printed out by COFT)

    Returns:
        tuple of 
            dictionary of dataframes : whose keys is variables name
    """
    budget = {}
    budget_dirc1 = {}
    budget_dirc2 = {}
    for tup in connections:    
        try:
            csv = \
                f"COFT_{tup[0].replace(' ','_')}_{tup[1].replace(' ','_')}.csv"
            csvfp = os.path.join(dir, csv)
            dftmp = pd.read_csv(csvfp)
            direction = -1
        except FileNotFoundError:
            csvfp = os.path.join(dir, csv)
            csv = \
                f"COFT_{tup[1].replace(' ','_')}_{tup[0].replace(' ','_')}.csv"
            dftmp = pd.read_csv(csvfp)
            direction = 1
        
        # trim the dataframe
        if timemax is None:
            df = dftmp
        else:
            for col in dftmp.columns:
                if re.search('TIME', col):
                    df = dftmp[dftmp[col]<=timemax]

        for col in df.columns:
            # get time steps
            if re.search('TIME', col):
                if not 'TIME' in budget: 
                    budget['TIME'] = copy.deepcopy(df[col])
                    budget_dirc1['TIME'] = copy.deepcopy(df[col])
                    budget_dirc2['TIME'] = copy.deepcopy(df[col])
                continue
            # calc. total flow (gas + liquid)
            if col.strip() in colsName4CalcNetFlow:
                if 'FLOW_(total)' in budget: 
                    budget['FLOW_(total)'] += df[col]*direction
                    budget_dirc1['FLOW_(total)'] += df[col].mask(df[col]>0,0)*direction
                    budget_dirc2['FLOW_(total)'] += df[col].mask(df[col]<0,0)*direction
                else: 
                    budget['FLOW_(total)'] = copy.deepcopy(df[col])*direction
                    budget_dirc1['FLOW_(total)'] = copy.deepcopy(df[col].mask(df[col]>0,0))*direction
                    budget_dirc2['FLOW_(total)'] = copy.deepcopy(df[col].mask(df[col]<0,0))*direction
            # sum the result (for each variable) of all the csv files
            if col.strip() in budget: 
                budget[col.strip()] += df[col]*direction
                budget_dirc1[col.strip()] += df[col].mask(df[col]>0,0)*direction
                budget_dirc2[col.strip()] += df[col].mask(df[col]<0,0)*direction
            else: 
                budget[col.strip()] = copy.deepcopy(df[col])*direction
                budget_dirc1[col.strip()] = copy.deepcopy(df[col].mask(df[col]>0,0))*direction
                budget_dirc2[col.strip()] = copy.deepcopy(df[col].mask(df[col]<0,0))*direction

    # rename Series.name
    budget['FLOW_(total)'] = budget['FLOW_(total)'].rename('FLOW_(total)')
    budget_dirc1['FLOW_(total)'] = budget_dirc1['FLOW_(total)'].rename('FLOW_(total)')
    budget_dirc2['FLOW_(total)'] = budget_dirc2['FLOW_(total)'].rename('FLOW_(total)')
    
    return budget, budget_dirc1, budget_dirc2 

def plot_inj_flow_COFT(ini:_readConfig.InputIni, dat:t2data, geo:mulgrids):
    pass

def plot_timestep_growth(ini:_readConfig.InputIni, dat:t2data, 
                         saveDir:str=None):
    # escape t3outfiles
    escape_t3outfiles(ini)
    create_savefig_dir(ini)
    if saveDir is None: saveDir = ini.savefigFp
    fig = plt.figure(figsize=(10,6))
    csv = f"FOFT_{str(dat.history_block[0]).replace(' ','_')}.csv"
    csvfp = os.path.join(ini.t3outEscapeFp, csv)    
    df = pd.read_csv(csvfp)
    colname_time = ""
    for var in df.columns:
        if re.search('TIME', var): colname_time = var
    ax = fig.add_subplot(1,2,1)
    ax.plot(np.arange(1,1+len(df[colname_time])), df[colname_time], 
            marker='o', markersize=3, color='b')
    t_max = max(df[colname_time])
    label = _xy_axisFormatter(t_max, ax.yaxis)
    ax.set_xlabel("timestep(N)")
    ax.set_ylabel(label)
    
    ax2 = fig.add_subplot(1,2,2)
    ax2.plot(np.arange(1,1+len(df[colname_time])), df[colname_time], 
            marker='o', markersize=3, color='b')
    t_max = max(df[colname_time])
    ax2.set_xlabel("timestep(N)")
    ax2.set_yscale('log')
    ax2.set_ylabel("[s]")
    
    savefp = os.path.join(saveDir, f"timestep_growth.png")
    fig.tight_layout()
    fig.savefig(savefp)


def plot_block_timeseries_FOFT(ini:_readConfig.InputIni, dat:t2data, 
                                saveDir:str=None, xrangeMax:list=None,
                                isXscaleLog=False, isYscaleLog=False):
    # escape t3outfiles
    escape_t3outfiles(ini)
    create_savefig_dir(ini)
    if saveDir is None: saveDir = ini.savefigFp

    nrows = len(dat.history_block)
    inchOverCm = 1/2.54
    fig = plt.figure(figsize=(7*inchOverCm*8, 7*inchOverCm*nrows)) # inch to cm
    # fig = plt.figure(figsize=(10, 30)) # inch to cm
    for ib, blk in enumerate(dat.history_block):
        # open csv
        csv = f"FOFT_{str(blk).replace(' ','_')}.csv"
        csvfp = os.path.join(ini.t3outEscapeFp, csv)
        print(f"open: {csv}")
        df = pd.read_csv(csvfp)
        ncols = len(df.columns)
        colname_time = ""
        range = []
        for var in df.columns:
            if re.search('TIME', var): colname_time = var
        # set plot range
        t_max = max(df[colname_time])
        t_min = min(df[colname_time]) if isXscaleLog else 0
        if xrangeMax is None:
            range = [t_min, t_max]
        else:
            if t_max < xrangeMax[1]: range = [t_min, t_max]
            else: range = xrangeMax
        
        for ivar, var in enumerate(df.columns):
            if re.search('TIME', var): 
                continue
            ax = fig.add_subplot(nrows, ncols, ib*ncols+ivar+1) # subplot returns axis 
            ax.set_title(f"{var.strip()}@{str(blk).strip()}")

            # range
            # ax.set_xlim(range, auto=False)
            # format xaxis
            if isXscaleLog: 
                # log scale
                ax.set_xscale('log')
                label = "[s]"
            else:
                ax.set_xlim(range, auto=False)
                # linear scale
                label = _xy_axisFormatter(range[1], ax.xaxis)
            # format yaxis
            if "PRES" in var:
                ax.yaxis.set_major_formatter(
                    mpl.ticker.FuncFormatter(
                        lambda x,pos: f"{x/10**5:,.2f} bar")
                    )
            if isYscaleLog: ax.set_yscale('log')
            # plot
            ax.plot(df[colname_time], df[var], marker='o', markersize=3, 
                    color='b', label=f"{var.strip()}" )
            # label
            # if isXscaleLog: label = "[s]" 
            ax.set_xlabel(label) 
            print("  " + var.strip() + " plotted")
    
    info = "_logx" if isXscaleLog else ""
    info += "_logy" if isYscaleLog else ""
    
    savefp = os.path.join(saveDir, f"foft_variables{info}.png")
    fig.tight_layout()
    fig.savefig(savefp)
    print("saved:", savefp)
    # plt.show()

def csv_plotter_multi(label_and_csvfp_dict:dict, filename:str="", xrange:list=None, isXscaleLog=False, 
                      isYscaleLog=False, inversesY=False, saveDir=None):
    """
    Plot timeseries of given csv files.
    Each csv files must have a column whose name contain 'TIME'.
    Different type of [FCG]OFT*.csv can be mixed

    Args:
        label_and_csvfp_dict (dict): label and filepath of [FCG]OFT*.csv.
        saveDir ([type], optional): if None, use dirpath of csvfp
    """
    import matplotlib.cm as cm
    dfdict = {}
    var_tmp = set()
    for label,csvfp in label_and_csvfp_dict.items():
        print(f"open: {csvfp}")
        dftmp = pd.read_csv(csvfp)    
        for c in dftmp.columns:
            if 'TIME' in c.upper():
                dfdict[label] = dftmp[dftmp[c]>=min(xrange)][dftmp[c]<=max(xrange)][dftmp.index<(len(dftmp.index)-2)]
        # 和集合
        var_tmp = var_tmp.union(set(dfdict[label].columns))

    # いらないcolumnを除去
    variables = []
    for v in var_tmp:
        if re.search('TIME', v): 
            continue
        variables.append(v)
    
    variables.sort()

    # プロットエリアの準備
    nrows = len(variables)
    inchOverCm = 1/2.54
    fig = plt.figure(figsize=(13*inchOverCm, 7*inchOverCm*nrows)) # inch to cm
    ax = {}
    xrange
    for ivar, var in enumerate(variables):
        ax[var] = fig.add_subplot(nrows, 1, ivar+1) # subplot returns axis 

    # plot
    for i, (label, df) in enumerate(dfdict.items()):
        colname_time = ""
        for dfcol in df.columns:
            if re.search('TIME', dfcol): 
                colname_time = dfcol
                continue
            ax[dfcol].set_title(f"{dfcol.strip()}")
 
            # plot
            y = df[dfcol]*-1 if inversesY else df[dfcol]
            ax[dfcol].plot(df[colname_time], y, marker='o', markersize=2, color=cm.viridis(i/(len(dfdict)-1)), 
                    label=f"{label}" )
            print(f"{label}:{dfcol.strip()} plotted")
    
    # 凡例など見た目の整理
    for ivar, var in enumerate(variables):
        ax[var].legend()
        if not xrange is None:
            ax[var].set_xlim(xrange, auto=False)

        # format xaxis
        if isXscaleLog: 
            # log scale
            ax[var].set_xscale('log')
            unit = "[s]"
        else:
            # linear scale
            unit = _xaxisFormatter(ax[var].get_xlim(), ax[var])
        ax[var].set_xlabel(unit)
        
        # format yaxis
        if "PRES" in var:
            ax[var].yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x/10**5:,.2f} bar"))
        if isYscaleLog: ax[var].set_yscale('log')

    if saveDir is None: saveDir = os.path.dirname(csvfp)
    savefp = os.path.join(saveDir, f"{filename}.png")
    fig.tight_layout()
    fig.savefig(savefp)

def plot_timeseries_FOFT_single(
        csvfp:str, isXscaleLog=False, isYscaleLog=False, inversesY=False, 
        saveDir=None):
    """
    plot timeseries of given csv file whose first column is 'TIME'

    Args:
        csvfp (str): filepath of [FCG]OFT*.csv 
        saveDir ([type], optional): if None, use dirpath of csvfp
    """
    print(f"open: {csvfp}")
    df = pd.read_csv(csvfp)
    ncols = len(df.columns)
    colname_time = ""
    inchOverCm = 1/2.54
    fig = plt.figure(figsize=(7*inchOverCm*8, 7*inchOverCm)) # inch to cm
    for ivar, var in enumerate(df.columns):
        if re.search('TIME', var): 
            colname_time = var
            continue
        ax = fig.add_subplot(1, ncols, ivar+1) # subplot returns axis 
        ax.set_title(f"{var.strip()}")
        # format xaxis
        if isXscaleLog: 
            # log scale
            ax.set_xscale('log')
            label = "[s]"
        else:
            # linear scale
            label = _xaxisFormatter(df[colname_time], ax)
        # format yaxis
        if "PRES" in var:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x/10**5:,.2f} bar"))
        if isYscaleLog: ax.set_yscale('log')
        # plot
        y = df[var]*-1 if inversesY else df[var]
        ax.plot(df[colname_time], y, marker='o', markersize=3, color='b', 
                label=f"{var.strip()}" )
        # label
        ax.set_xlabel(label)
        print("  " + var.strip() + " plotted")
    if saveDir is None: saveDir = os.path.dirname(csvfp)
    name = os.path.basename(csvfp).split('.')[0]
    savefp = os.path.join(saveDir, f"{name}.png")
    fig.tight_layout()
    fig.savefig(savefp)

def plot_spatial_flow_distribution_at_surface_COFT_radial(
        ini:_readConfig.InputIni, dat:t2data, 
        geo:mulgrids, saveDir:str=None, xrangeMax:list=None):
    
    # escape t3outfiles
    escape_t3outfiles(ini)
    create_savefig_dir(ini)
    if saveDir is None: saveDir = ini.savefigFp
    if ini.mesh.type != REGULAR \
            or (ini.mesh.type == REGULAR and not ini.mesh.isRadial): 
        return

    ii = ini.toughInput
    layer_top = geo.layerlist[1]  # get property of top layer 
    conn_list_suf = []
    xPosList = []
    areaList = []
    r_inner = 0
    if ii['prints_hc_surface']:
        for dr,col in zip(ini.mesh.rblocks,geo.columnlist):
            blockname_top = geo.block_name(layer_top.name, col.name)
            
            # name of connection
            conn_list_suf.append((blockname_top,'ATM 0'))
            
            # position
            xPosList.append(col.centre[0])

            # area
            r_outer = r_inner + dr
            # check position of elem, just in case
            if col.centre[0] < r_inner or r_outer < col.centre[0]: 
                sys.exit()
            areaList.append((r_outer**2 - r_inner**2)*math.pi)
            # update
            r_inner = r_outer
    else: 
        print(f"[t2outUtil.plot_surface_flow_COFT] option "\
                +"'prints_hc_surface' is False in ini file. skip")
    
    budget = None
    bdgLast = {}
    bdgLastAcc = {}
    bdgLastArea = {}
    bdgLast['xpos'] = xPosList
    bdgLastArea['xpos'] = xPosList
    bdgLastAcc['xpos'] = xPosList
    endtime = None
    for iconn,tup in enumerate(conn_list_suf):    
        try:
            csv = \
                f"COFT_{tup[0].replace(' ','_')}_{tup[1].replace(' ','_')}.csv"
            csvfp = os.path.join(ini.t3outEscapeFp, csv)
            direction = -1
        except FileNotFoundError:
            csvfp = os.path.join(ini.t3outEscapeFp, csv)
            csv = \
                f"COFT_{tup[1].replace(' ','_')}_{tup[0].replace(' ','_')}.csv"
            direction = 1
        df = pd.read_csv(csvfp)
        arr = np.array(df)


        for icol, col in enumerate(df.columns):
            # get time steps
            if re.search('TIME', col.upper()):
                if endtime is None: endtime = arr[-1][icol]
                break


        if budget is None:
            NCONN=len(conn_list_suf)
            NTIME=len(arr)
            iTimeLast = NTIME -1
            # budget = np.array([[None]*NCONN]*NTIME)

        
        for icol, col in enumerate(df.columns):
            # get time steps
            if re.search('TIME', col.upper()):continue

            if col.strip() in bdgLast: 
                bdgLast[col.strip()] = \
                    np.append(bdgLast[col.strip()], arr[-1][icol]*direction)
                bdgLastArea[col.strip()] = \
                    np.append(
                        bdgLastArea[col.strip()], 
                        arr[-1][icol]*direction/areaList[iconn])
                bdgLastAcc[col.strip()] = \
                    np.append(
                        bdgLastAcc[col.strip()],
                        arr[-1][icol]*direction + bdgLastAcc[col.strip()][-1])
            else: 
                bdgLast[col.strip()] = \
                    np.array([arr[-1][icol]*direction])
                bdgLastArea[col.strip()] = \
                    np.array([arr[-1][icol]*direction/areaList[iconn]])
                bdgLastAcc[col.strip()] = \
                    np.array([arr[-1][icol]*direction])
        

        """
        if iconn == 0:
            bdgLast[heat] = np.array([arr[-1][iheat]*direction])
            bdgLast[flog] = np.array([arr[-1][iflog]*direction])
            bdgLast[flol] = np.array([arr[-1][iflol]*direction])
            bdgLast[flog_w] = np.array([arr[-1][iflog_w]*direction])
            bdgLast[flog_nacl] = np.array([arr[-1][iflog_nacl]*direction])
            bdgLast[flog_co2] = np.array([arr[-1][iflog_co2]*direction])
            bdgLast[flol_w] = np.array([arr[-1][iflol_w]*direction])
            bdgLast[flol_nacl] = np.array([arr[-1][iflol_nacl]*direction])
            bdgLast[flol_co2] = np.array([arr[-1][iflol_co2]*direction])
            bdgLastAcc[heat] = np.array([arr[-1][iheat]*direction])
            bdgLastAcc[flog] = np.array([arr[-1][iflog]*direction])
            bdgLastAcc[flol] = np.array([arr[-1][iflol]*direction])
            bdgLastAcc[flog_w] = np.array([arr[-1][iflog_w]*direction])
            bdgLastAcc[flog_nacl] = np.array([arr[-1][iflog_nacl]*direction])
            bdgLastAcc[flog_co2] = np.array([arr[-1][iflog_co2]*direction])
            bdgLastAcc[flol_w] = np.array([arr[-1][iflol_w]*direction])
            bdgLastAcc[flol_nacl] = np.array([arr[-1][iflol_nacl]*direction])
            bdgLastAcc[flol_co2] = np.array([arr[-1][iflol_co2]*direction])
        else:
            bdgLast[heat] = np.append(bdgLast[heat], arr[-1][iheat]*direction)
            bdgLast[flog] = np.append(bdgLast[flog], arr[-1][iflog]*direction)
            bdgLast[flol] = np.append(bdgLast[flol], arr[-1][iflol]*direction)
            bdgLast[flog_w] = np.append(bdgLast[flog_w], arr[-1][iflog_w]*direction)
            bdgLast[flog_nacl] = np.append(bdgLast[flog_nacl], arr[-1][iflog_nacl]*direction)
            bdgLast[flog_co2] = np.append(bdgLast[flog_co2], arr[-1][iflog_co2]*direction)
            bdgLast[flol_w] = np.append(bdgLast[flol_w], arr[-1][iflol_w]*direction)
            bdgLast[flol_nacl] = np.append(bdgLast[flol_nacl], arr[-1][iflol_nacl]*direction)
            bdgLast[flol_co2] = np.append(bdgLast[flol_co2], arr[-1][iflol_co2]*direction)
            bdgLastAcc[heat] = np.append(bdgLastAcc[heat], arr[-1][iheat]*direction + bdgLastAcc[heat][-1])
            bdgLastAcc[flog] = np.append(bdgLastAcc[flog], arr[-1][iflog]*direction + bdgLastAcc[flog][-1])
            bdgLastAcc[flol] = np.append(bdgLastAcc[flol], arr[-1][iflol]*direction + bdgLastAcc[flol][-1])
            bdgLastAcc[flog_w] = np.append(bdgLastAcc[flog_w], arr[-1][iflog_w]*direction + bdgLastAcc[flog_w][-1])
            bdgLastAcc[flog_nacl] = np.append(bdgLastAcc[flog_nacl], arr[-1][iflog_nacl]*direction + bdgLastAcc[flog_nacl][-1])
            bdgLastAcc[flog_co2] = np.append(bdgLastAcc[flog_co2], arr[-1][iflog_co2]*direction + bdgLastAcc[flog_co2][-1])
            bdgLastAcc[flol_w] = np.append(bdgLastAcc[flol_w], arr[-1][iflol_w]*direction + bdgLastAcc[flol_w][-1])
            bdgLastAcc[flol_nacl] = np.append(bdgLastAcc[flol_nacl], arr[-1][iflol_nacl]*direction + bdgLastAcc[flol_nacl][-1])
            bdgLastAcc[flol_co2] = np.append(bdgLastAcc[flol_co2], arr[-1][iflol_co2]*direction + bdgLastAcc[flol_co2][-1])
"""
                
    bdgLast[totalf] = bdgLast[flol] + bdgLast[flog]
    bdgLastArea[totalf] = bdgLastArea[flol] + bdgLastArea[flog]
    bdgLastAcc[totalf] = bdgLastAcc[flol] + bdgLastAcc[flog]

    # calc heat flow by other than fluid flow
    bdgLast[totalheat_heatByFlow] = bdgLast[heat] - bdgLast[flol]*4200
    for iconn, conn in enumerate(bdgLast[totalheat_heatByFlow]):
        if iconn == 0:
            bdgLastAcc[totalheat_heatByFlow] = np.array([conn])
            bdgLastArea[totalheat_heatByFlow] = np.array([conn/areaList[iconn]])
        else:
            bdgLastAcc[totalheat_heatByFlow] = \
                np.append(bdgLastAcc[totalheat_heatByFlow], 
                          conn+bdgLastAcc[totalheat_heatByFlow][-1])
            bdgLastArea[totalheat_heatByFlow] = \
                np.append(bdgLastArea[totalheat_heatByFlow], 
                          conn/areaList[iconn])

    # set plot range
    if xrangeMax is None:
        range = [0, xPosList[-1]]
    else:
        if xPosList[-1] < xrangeMax[1]: range = [0, xPosList[-1]]
        else: range = xrangeMax

    # plot
    for ivar, var in enumerate(bdgLast):
        if re.search('xpos', var): continue
        # # toggle
        # if flog_w == var.strip() or \
        #         flog_co2 == var.strip() or \
        #         flog_nacl == var.strip() or \
        #         flol_w == var.strip() or \
        #         flol_co2 == var.strip() or \ 
        #         flol_nacl == var.strip():
        #     continue

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)     
        ax.set_title(f"{var.strip()} t={endtime}")
        # range
        ax.set_xlim(range, auto=False)
        # format yaxis
        if heat in var or totalheat_heatByFlow in var:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x/10**6:,.2f} MW"))
        if 'FLOW_total' in var:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x:,.2f} kg/s"))
        elif 'FLOW' in var:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x*3600*24:,.2f} kg/day"))
        # plot
        ax.plot(bdgLast['xpos'], bdgLast[var],  marker='o', markersize=3, 
                color='r', label=f"{var.strip()}" )
        ax.plot(bdgLastAcc['xpos'], bdgLastAcc[var],  marker='o', markersize=3, 
                color='b', label=f"{var.strip()}" )
        # label
        ax.set_xlabel('m')
        print("  " + var.strip() + " plotted")
        savefp = os.path.join(saveDir, f"{var}_surface.png")
        fig.tight_layout()
        fig.savefig(savefp)
        plt.close()

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)     
        ax.set_title(f"{var.strip()}/area t={endtime}")
        # range
        ax.set_xlim(range, auto=False)
        # format yaxis
        if heat in var or totalheat_heatByFlow in var:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x*10**3:,.2f} mW/m^2"))
        if 'FLOW' in var:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x:.2e} kg/(s-m^2)"))
        # plot
        ax.plot(bdgLastArea['xpos'], bdgLastArea[var],  marker='o', 
                markersize=3, color='r', label=f"{var.strip()}" )
        # label
        ax.set_xlabel('m')
        print("  " + var.strip() + " plotted")
        savefp = os.path.join(saveDir, f"{var}_surfaceArea.png")
        fig.tight_layout()
        fig.savefig(savefp)
        plt.close()



def readAllTimestepsFromFOFT(ini:_readConfig.InputIni):
    
    # escape t3outfiles
    escape_t3outfiles(ini)
    
    times = np.array([])
    foftList = glob.glob(os.path.join(ini.t3outEscapeFp, "FOFT*"))
    if len(foftList) == 0: 
        print("[readAllTimestepsFromFOFT] No FOFT* found. "\
             +"Timesteps cannot be aquired.")
        return times

    df = pd.read_csv(foftList[0])
    for ivar, var in enumerate(df.columns):
        if re.search('TIME', var): 
            return  np.array(df[var])

def read_output_eleme_csv(ini:_readConfig.InputIni):
    """[summary]

    Args:
        ini (_readConfig.InputIni): [description]

    Returns:
        out : list of pandas.DataFrame
        time: list
        label: list of colname in dataframe out[i]
        unit: list of unit of column in dataframe out[i]
    """
    # escape t3outfiles
    escape_t3outfiles(ini)
    
    elemCsv = os.path.join(ini.t3outEscapeFp,
                           ini.setting.toughConfig.OUTPUT_ELEME_CSV_FILE_NAME)
    with open(elemCsv, 'r') as f:
        label = None
        unit = None
        time_indx = -1
        elem_indx = None
        time = []
        outtmp = []
        out = []
        for i, line in enumerate(f):
            if i == 0:
                # first line (label)
                print([ re.sub(r'"',"",l).strip() for l in  line.split(",")])
                label = [ re.sub(r'"',"",l).strip() for l in  line.split(",")]
                for j,l in enumerate(label):
                    if "elem" in l.lower(): 
                        elem_indx = j 
                        label[j] = 'row' # same col name as t2listing.element.DataFrame
                continue
            if i == 1:
                # second line (unit)
                print([ re.sub(r'"',"",l).strip() for l in  line.split(",")])
                unit = [ re.sub(r'"',"",l).strip() for l in  line.split(",")]
                continue
            if "time [sec]" in line.lower():
                time_indx += 1
                # read time[s]
                time.append(
                    float(re.match(r'.*([0-9]+\.[0-9]*[Ee][+-][0-9]+).*', line)\
                        .groups()[0])
                    )
                outtmp.append([]) #out[time_idx]
                out.append([]) #out[time_idx]
            else:
                valtmp = re.sub(r'\n',"",line).split(",")
                vals = []
                for k, val in enumerate(valtmp):
                    if k == elem_indx: vals.append(str(val[-6:-1]))
                    else: vals.append(float(val))
                # for sorting by element name
                vals.append(valtmp[elem_indx][-6:-3])
                # for sorting by element name
                vals.append(valtmp[elem_indx][-3:-1])
                outtmp[time_indx].append(vals)
        
        # for sorting by element name
        label.append("EL")
        # for sorting by element name
        label.append("NE")

        for i, tmp in enumerate(outtmp):
            # sorting by element name in the same order as output.listing
            # sorting by NE and EL
            tmp.sort(key=lambda x: (x[len(label)-1], x[len(label)-2]))
            # then convert to dataframe
            out[i] = pd.DataFrame(tmp, columns=label)
    return out, time, label, unit


def read_output_conne_csv(ini:_readConfig.InputIni):
    """[summary]

    Args:
        ini (_readConfig.InputIni): [description]

    Returns:
        out : list of pandas.DataFrame
        time: list
        label: list of colname in dataframe out[i]
        unit: list of unit of column in dataframe out[i]
    """
    # escape t3outfiles
    escape_t3outfiles(ini)
    
    conneCsv = os.path.join(
        ini.t3outEscapeFp,ini.setting.toughConfig.OUTPUT_CONNE_CSV_FILE_NAME)
    with open(conneCsv, 'r') as f:
        label = None
        unit = None
        time_indx = -1
        elem1_indx = None
        elem2_indx = None
        time = []
        outtmp = []
        out = []
        for i, line in enumerate(f):
            if i == 0:
                # first line (label)
                print([ re.sub(r'"',"",l).strip() for l in  line.split(",")])
                label = [ re.sub(r'"',"",l).strip() for l in  line.split(",")]
                for j,l in enumerate(label):
                    if "elem1" in l.lower(): 
                        elem1_indx = j 
                    if "elem2" in l.lower(): 
                        elem2_indx = j 
                continue
            if i == 1:
                # second line (unit)
                print([ re.sub(r'"',"",l).strip() for l in  line.split(",")])
                unit = [ re.sub(r'"',"",l).strip() for l in  line.split(",")]
                continue
            if "time [sec]" in line.lower():
                time_indx += 1
                # read time[s]
                time.append(
                    float(re.match(r'.*([0-9]+\.[0-9]*[Ee][+-][0-9]+).*', line)\
                        .groups()[0]))
                outtmp.append([]) #out[time_idx]
                out.append([]) #out[time_idx]
            else:
                valtmp = re.sub(r'\n',"",line).split(",")
                vals = []
                for k, val in enumerate(valtmp):
                    if k == elem1_indx or k == elem2_indx: 
                        vals.append(str(val[-6:-1]))
                    else: 
                        vals.append(float(val))
                # for sorting by element name
                vals.append((vals[elem1_indx],vals[elem2_indx]))
                vals.append(valtmp[elem1_indx][-6:-3])
                vals.append(valtmp[elem1_indx][-3:-1])
                vals.append(valtmp[elem2_indx][-6:-3])
                vals.append(valtmp[elem2_indx][-3:-1])
                outtmp[time_indx].append(vals)
        
        # for sorting by element name
        label.append("row")
        label.append("EL1")
        label.append("NE1")
        label.append("EL2")
        label.append("NE2")

        for i, tmp in enumerate(outtmp):
            # sorting by element name in the same order as output.listing
            # sorting by NE and EL
            # tmp.sort(key=lambda x: (x[len(label)-1], x[len(label)-2], x[len(label)-3], x[len(label)-4]))
            # then convert to dataframe
            tmpdf = pd.DataFrame(tmp, columns=label)
            # OUTPUT_CONNE.csv can contain duplicated rows, so drop these rows 
            out[i] = tmpdf.drop_duplicates(subset='row')
    return out, time, label, unit


def column_plot_INCON(ini:_readConfig.InputIni, column_names:list):
    """
    create vertical profile at each specified columns.
    create fig of vertical profile for each column from INCON and SAVE 
    """
    create_savefig_dir(ini)
    saveDir = ini.savefigFp
    dat = t2data(ini.t2FileFp)
    inc = t2incon(ini.inconFp)
    readsSAVE = os.path.isfile(ini.saveFp)
    if readsSAVE:
        save = t2incon(ini.saveFp)
    nZ = len(ini.mesh.zblocks)
    numVar = 4

    colData_inc = {}
    colData_save = {}
    for col in column_names:
        colData_inc[col] = np.array([[None]*nZ]*numVar)
        if readsSAVE: colData_save[col] = np.array([[None]*nZ]*numVar)
    
    # get list of position
    z = []
    for blk in dat.grid.blocklist:
        if blk.name[0:3] == column_names[0]:
            z.append(blk.centre[2])

    # extract data for each col
    for col in column_names:
        iz=0
        for blk in dat.grid.blocklist:
            if blk.name[0:3] == col:
                # print(f"{blk.name[0:3]} {blk.name[3:5]}")
                for k in range(numVar):
                    colData_inc[col][k][iz] = inc[blk.name].variable[k]
                    if k==3: print(f"{blk.name} {inc[blk.name].variable}")
                    if k==3: print(f"{blk.name} {colData_inc[col][k][iz]}")
                    if readsSAVE: 
                        colData_save[col][k][iz] = save[blk.name].variable[k]
                iz+=1
    
    for col in column_names:
        for k in range(0, numVar):
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)     
            ax.set_title(f"col:'{col}' variable[{k}]")
            # plot
            ax.plot(z, colData_inc[col][k],  marker='o', markersize=3, 
                    color='r', label=f"INCON" )
            if readsSAVE:
                ax.plot(z, colData_save[col][k],  linestyle='-', markersize=3, 
                        olor='b', label=f"SAVE" )
            # label
            ax.set_xlabel('m')
            ax.legend()
            savefigfp = os.path.join(saveDir, f"var{k}_col_{col}.png")
            fig.tight_layout()
            fig.savefig(savefigfp)
            plt.close()

def column_plot_INCON2(ini:_readConfig.InputIni, column_names:list=None):
    """
    !!! this method is an old one. Use column_plot_INCON3 instead.
    create vertical profile at each specified columns.
    plot multiple column sections in a single fig.
    """
    if column_names is not None:
        # use passed cols list to plot
        pass
    elif ini.plot.columns_incon_plot is not None:
        # read cols list from input*.ini file
        column_names = ini.plot.columns_incon_plot
    else:
        print("[t2outUtil.column_plot_INCON2] no column given in list")
    
    
    create_savefig_dir(ini)
    saveDir = ini.savefigFp
    dat = t2data(ini.t2FileFp)
    inc = t2incon(ini.inconFp)
    
    if inc.get_num_blocks() <= 0: 
        print("[t2outUtil.column_plot_INCON2] INCON file is empty. skip")
        return

    # plot from SAVE only if SAVE file is found
    readsSAVE = os.path.isfile(ini.saveFp)
    if readsSAVE: 
        save = t2incon(ini.saveFp)
        if save.get_num_blocks() <= 0: 
            print("[t2outUtil.column_plot_INCON2] SAVE file is empty. Plot only INCON")
            readsSAVE=False

    # the number of zblocks
    nZ = len(ini.mesh.zblocks)
    # the number of primary variables
    numVar = 4 

    # prepare data container
    colData_inc = {}
    colData_save = {}
    for col in column_names:
        colData_inc[col] = np.array([[None]*nZ]*numVar)
        if readsSAVE: colData_save[col] = np.array([[None]*nZ]*numVar)
    
    # get list of z position for col == column_names[0]
    z = []
    for blk in dat.grid.blocklist:
        if blk.name[0:3] == column_names[0]:
            z.append(blk.centre[2])

    # get x coordinate for each column
    # check the existence of col and recreate a list of col names to plot
    label_r = []
    columns_exist = []
    for blk in dat.grid.blocklist:
        for c, col in enumerate(column_names):
            if blk.name[0:3] == col and blk.name[3:5] == ' 1':
                label_r.append(blk.centre[0])
                columns_exist.append(col)


    # extract data for each col
    for col in columns_exist:
        iz=0
        for blk in dat.grid.blocklist:
            if blk.name[0:3] == col:
                # print(f"{blk.name[0:3]} {blk.name[3:5]}")
                for k in range(numVar):
                    colData_inc[col][k][iz] = inc[blk.name].variable[k]
                    if readsSAVE: 
                        colData_save[col][k][iz] = save[blk.name].variable[k]
                iz+=1
    
    for k in range(0, numVar):
        import matplotlib.cm as cm

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)     
        ax.set_title(f"variable[{k}] INCON")
        fig2 = plt.figure()
        ax2 = fig2.add_subplot(1, 1, 1)     
        ax2.set_title(f"variable[{k}] SAVE")
        # plot
        for i,col in enumerate(columns_exist):
            ax.plot(z, colData_inc[col][k],  marker='o', markersize=3, 
                    # color=cm.hot(1-i/len(columns_exist)), 
                    # color=cm.hsv(1-i/len(columns_exist)), 
                    color=cm.viridis(i/len(columns_exist)), 
                    label=f"{col}) x={label_r[i]}m" )
            if readsSAVE:
                ax2.plot(z, colData_save[col][k],  linestyle='-', markersize=3, 
                    # color=cm.hot(1-i/len(columns_exist)), 
                    # color=cm.hsv(1-i/len(columns_exist)), 
                    # color=cm.hsv(1-i/len(columns_exist)), 
                    color=cm.viridis(i/len(columns_exist)), 
                    label=f"{col}) x={label_r[i]}m"  )
        # label
        ax.set_xlabel('m')
        ax.legend()
        savefigfp = os.path.join(saveDir, f"var{k}_INCON.png")
        fig.tight_layout()
        fig.savefig(savefigfp)
        ax2.set_xlabel('m')
        ax2.legend()
        savefigfp2 = os.path.join(saveDir, f"var{k}_SAVE.png")
        fig2.tight_layout()
        if readsSAVE: fig2.savefig(savefigfp2)
        plt.close()

def column_plot_INCON3(ini:_readConfig.InputIni, col_names_plot:list=None):
    """
    create vertical profile at each specified columns.
    plot multiple column sections in a single fig.
    """
    if col_names_plot is not None:
        # use passed cols list to plot
        pass
    elif ini.plot.columns_incon_plot is not None:
        # read cols list from input*.ini file
        col_names_plot = ini.plot.columns_incon_plot
    else:
        print("[t2outUtil.column_plot_INCON2] no column given in list")
    
    create_savefig_dir(ini)
    saveDir = ini.savefigFp
    geo = mulgrid(ini.mulgridFileFp)
    inc = t2incon(ini.inconFp)

    if inc.get_num_blocks() <= 0: 
        print("[t2outUtil.column_plot_INCON2] INCON file is empty. skip")
        return

    # plot from SAVE only if SAVE file is found
    readsSAVE = os.path.isfile(ini.saveFp)
    if readsSAVE: 
        save = t2incon(ini.saveFp)
        if save.get_num_blocks() <= 0: 
            print("[t2outUtil.column_plot_INCON2] SAVE file is empty. Plot only INCON")
            readsSAVE=False
    
    pos_info = []
    columns_exist = []
    for col in geo.columnlist:
        for c, co_p in enumerate(col_names_plot):
            if col.name == co_p:
                pos_info.append(col.centre)
                columns_exist.append(col)
    
    # prepare data container
    layernames_each_col = {}
    # create grid depths list for each column 
    for col in columns_exist:
        layernames_each_col[col.name] = []
        lay_top = geo.column_surface_layer(col)
        for lay in geo.layerlist:
            if lay.centre > lay_top.centre: 
                continue
            else:
                layernames_each_col[col.name].append(lay.name)

    # prepare data container
    z_each_col = {}
    colData_inc = {}
    
    # Create a list of values for each column and each variable
    for col in columns_exist:
        # prepare (sub) data container
        z_each_col[col.name] = []
        colData_inc[col.name] = [[] for _ in range(inc.num_variables)] # initialization
    
        lay_top = geo.column_surface_layer(col)
        for lay in geo.layerlist:
            if lay.centre > lay_top.centre: 
                # skip air layer 
                continue
            else:
                z_each_col[col.name].append(lay.centre)
                for i, val in enumerate(inc[geo.block_name(lay.name, col.name)]):
                    colData_inc[col.name][i].append(val)

    if readsSAVE: 
        # prepare data container
        colData_save = {}
        # Create a list of values for each column and each variable
        for col in columns_exist:
            # prepare (sub) data container
            colData_save[col.name] =[[] for _ in range(save.num_variables)] # initialization
            lay_top = geo.column_surface_layer(col)
            for lay in geo.layerlist:
                if lay.centre > lay_top.centre: 
                    # skip air layer 
                    continue
                else:
                    for i, val in enumerate(save[geo.block_name(lay.name, col.name)]):
                        colData_save[col.name][i].append(val)
    

    import matplotlib.cm as cm
    for k in range(inc.num_variables):

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)     
        ax.set_title(f"variable[{k}] INCON")
        # plot
        for i,col in enumerate(columns_exist):
            ax.plot(z_each_col[col.name], colData_inc[col.name][k],  marker='o', markersize=3, 
                    # color=cm.hot(1-i/len(columns_exist)), 
                    # color=cm.hsv(1-i/len(columns_exist)), 
                    color=cm.viridis(i/len(columns_exist)), 
                    label=f"{col.name}) x={pos_info[i]}m" )
        # label
        ax.set_xlabel('m')
        ax.legend()
        savefigfp = os.path.join(saveDir, f"var{k}_INCON.pdf")
        fig.tight_layout()
        fig.savefig(savefigfp)
        plt.close()             
    
    if readsSAVE:
        for k in range(save.num_variables):
            fig2 = plt.figure()
            ax2 = fig2.add_subplot(1, 1, 1)     
            ax2.set_title(f"variable[{k}] SAVE")
            for i,col in enumerate(columns_exist):
                ax2.plot(z_each_col[col.name], colData_save[col.name][k],  linestyle='-', markersize=3, 
                    # color=cm.hot(1-i/len(columns_exist)), 
                    # color=cm.hsv(1-i/len(columns_exist)), 
                    # color=cm.hsv(1-i/len(columns_exist)), 
                    color=cm.viridis(i/len(columns_exist)), 
                    label=f"{col.name}) {pos_info[i]}[m]"  )
            ax2.set_xlabel('m')
            ax2.legend()
            savefigfp2 = os.path.join(saveDir, f"var{k}_SAVE.pdf")
            fig2.tight_layout()
            fig2.savefig(savefigfp2)
            plt.close()             


def plot_vertical_1D_profile(ini:_readConfig.InputIni, columns:list=None):
    create_savefig_dir(ini)
    saveDir = ini.savefigFp
    out, time, label, unit = read_output_eleme_csv(ini)
    z=out[0][out[0].row.str.contains("  a")][label[3]]
    df = out[-1]
    t=time[-1]

    for col in columns:
        for var in label[5:19]:
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)     
            ax.set_title(f"col:'{col}' variable: {var}")
            # plot
            y = df[df.row.str.contains(col)][var]
            ax.plot(z, y,  marker='o', markersize=3, color='r', 
                    label=f"{t:g}s" )
            # label
            ax.set_xlabel('m')
            ax.legend()
            savefp = os.path.join(saveDir, f"{var}_col_{col}_t={t:g}.png")
            fig.tight_layout()
            fig.savefig(savefp)
            plt.close()

def show_incon_summary(ini:_readConfig.InputIni):
    """
    show summary of INCON and SAVE
    """
    saveDir = ini.savefigFp
    dat = t2data(ini.t2FileFp)
    inc = t2incon(ini.inconFp)
    res0, res1, res2, res3 = [],[],[],[]
    # the number of primary variables
    for blk in dat.grid.blocklist:
        res0.append(inc[blk.name].variable[0])
        res1.append(inc[blk.name].variable[1])
        res2.append(inc[blk.name].variable[2])
        res3.append(inc[blk.name].variable[3])
    print(f"""
----INCON: {ini.setting.toughConfig.TOUGH_INPUT_DIR}/{ini.setting.toughConfig.INCON_FILE_NAME}
    variable 0 max {max(res0)}, min {min(res0)}
    variable 1 max {max(res1)}, min {min(res1)}
    variable 2 max {max(res2)}, min {min(res2)}
    variable 3 max {max(res3)}, min {min(res3)}""")

    # show summary of SAVE only if SAVE file is found
    if os.path.isfile(ini.saveFp):
        save = t2incon(ini.saveFp)
        if save.get_num_blocks() <= 0: 
            print("[t2outUtil.show_incon_summary] SAVE file is empty. skip")
            return
        res0, res1, res2, res3 = [],[],[],[]
        # the number of primary variables
        for blk in dat.grid.blocklist:
            res0.append(save[blk.name].variable[0])
            res1.append(save[blk.name].variable[1])
            res2.append(save[blk.name].variable[2])
            res3.append(save[blk.name].variable[3])
        print(f"""
----SAVE: {ini.setting.toughConfig.TOUGH_INPUT_DIR}/{ini.setting.toughConfig.SAVE_FILE_NAME}
    variable 0 max {max(res0)}, min {min(res0)}
    variable 1 max {max(res1)}, min {min(res1)}
    variable 2 max {max(res2)}, min {min(res2)}
    variable 3 max {max(res3)}, min {min(res3)}""")

def plot_timeseries_of_multiple_result(
        iniList:list, flowList:list, saveDir:str=None, xrange:list=None, 
        isXscaleLog=False, isYscaleLog=False, inversesY=False, filename=""):
    """[summary]
    plot timeseries of multiple results in Single figure (for each variable)  
    Args:
        iniList (list): list of _readConfig.InputIni
        flowList (list): list of dict. 
            In dict., keys are variable name ("TIME", "FLOW_L", ...) and 
            items are timeseries (pandas.Series).
            The dict. must includes "TIME".
            The order of dict. in list must be consistent with iniList.
        saveDir (str, optional): [description]. Defaults to None.
        xrange (tuple or list, optional): [description]. Defaults to None.
        isXscaleLog (bool, optional): [description]. Defaults to False.
        isYscaleLog (bool, optional): [description]. Defaults to False.
        inversesY (bool, optional): [description]. Defaults to False.
    """
    import matplotlib.cm as cm
    if saveDir is None: saveDir = iniList[0].t2FileDirFp
    # set plot range
    t_max = 0
    t_min = 0
    variable_names = None
    for f in flowList:
        if f is None: continue
        variable_names = list(f.keys())
        t_max = t_max if t_max > max(f['TIME']) else max(f['TIME'])
        t_min = t_min if t_min < min(f['TIME']) else min(f['TIME'])
    else:
        # flowListがすべてNoneのとき
        if variable_names is None: return


    if xrange is None:
        range = [t_min, t_max]
    else:
        if t_max < max(xrange): range = [t_min, t_max]
        else: range = xrange
    
    # plot
    inchOverCm = 1/2.54
    fig = plt.figure(figsize=(15*inchOverCm, 6*inchOverCm*10)) # inch to cm
    for i,variable in enumerate(variable_names):
        if re.search('TIME', variable): continue
        ax = fig.add_subplot(len(variable_names)-1, 1, i) # subplot returns axis 
        ax.set_title(variable)

        # format xaxis
        if isXscaleLog: 
            # log scale
            ax.set_xscale('log')
            label = "[s]"
        else:
            # linear scale
            label = _xy_axisFormatter(range[1], ax.xaxis)
        # range
        ax.set_xlim(range, auto=False)
        # format yaxis
        if "HEAT" in variable:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x/10**6:,.2f} MW"))
        if 'FLOW_total' in variable:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x:,.0f} kg/s"))
        elif 'FLOW' in variable:
            ax.yaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda x, pos: f"{x*3600*24:,.0f} kg/day"))
        
        if isYscaleLog: ax.set_yscale('log')
        # plot
        # roop for each result
        for j, ini in enumerate(iniList):
            if flowList[j] is None: continue 
            flowDic4eachIni = flowList[j]    
            if inversesY: y = flowDic4eachIni[variable]*(-1)
            else: y = flowDic4eachIni[variable]
            ax.plot(flowDic4eachIni['TIME'], y, 
                    marker='o', markersize=2, color=cm.viridis(j/len(iniList)), 
                    label=f"{ini.toughInput['problemName']}" )
        # label
        ax.set_xlabel(label)
        ax.legend()
        # plt.ylabel(variable)
        print("  " + variable + " plotted")
    
    info = "_logx" if isXscaleLog else ""
    info += "_logy" if isYscaleLog else ""
    info += "_inverse" if inversesY else ""
    
    savefp_suf = os.path.join(saveDir, f"{filename}.pdf")
    fig.tight_layout()
    fig.savefig(savefp_suf)

def calc_bulk_resistivity(df_elem:pd.DataFrame):
    """[summary]
    Args:
        df_elem (pandas.DataFrame): lst.element.DataFrame or 
                                    return value of read_output_eleme_csv()
    Returns:
        numpy.array: np.array of log10resistivity values
    """
    df_elem['log10resistivity'] = df_elem.apply(_df_elem_calc_bulk_resistivity, 
                                                axis=1)
    return np.array(df_elem['log10resistivity'])

def _df_elem_calc_bulk_resistivity(row:pd.Series):
    """[summary]
    Args:
        row (pd.Series): element of returned dict. by read_output_eleme_csv()
    Returns:
        [float] : log10 bulk resistivity 
    """
    brine_resistivity_ = \
        brine_resistivity(row['X_NaCl_L'], row['DEN_L']/1000, row['TEMP'], 
                          pure_water_dens=IAPWS97(T=row['TEMP']+273.15, P=row['PRES']/1e6).rho/1000)
    if math.isnan(row['POR']):
        """応急処置2021/5/23 porosityがNaNで出力される場合がある"""
        brine_proportion = 0.1 * row['SAT_L']
    else:
        brine_proportion = row['POR'] * row['SAT_L']
    cond_upper, cond_lower = \
        HS_bounds(brine_proportion, 1/HOSTROCK_RESISTIVITY, 1/brine_resistivity_)
    if math.isnan(cond_upper):
        print(cond_upper)
        print("[t2outUtil._df_elem_calc_bulk_resistivity] conductivity: NaN")
        print(brine_proportion,1/brine_resistivity_,1/HOSTROCK_RESISTIVITY)
    if cond_upper <= 0:
        return np.nan
    else:
        return math.log10(1/cond_upper)


def brine_resistivity(x_nacl_l, density, temperature, pure_water_dens=None):
    """[summary]
    Args:
        x_nacl_l (float): weight fraction of nacl in liquid [-]
        density (float): [g/cm^3]
        temperature (float): [C]
    Returns:
        float : resistivity of brine [ohm-m]
    """
    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")
    
    molar = massfrac2molar(x_nacl_l, density)
    molality = massfrac2molality(x_nacl_l)
    
    # SK model uses density of pure water but brine density 
    if pure_water_dens is not None:
        pure_water_dens = density
    else:
        logger.warning(f" for brine res. calc., pure_water_dens should be given")
    
    if 0.1 < molality:
        # Sinmyo & Keppler (2017)
        logger.info(f"molal:{molality:.4f} use SK")
        brine_resistivity = \
            brine_resistivity_SK(x_nacl_l*100, pure_water_dens, temperature)
    elif molar < 0.01:
        # Quist & Marshall (1968)
        logger.info(f"molal:{molality:.4f} use QM")
        brine_resistivity =\
             brine_resistivity_QM(molality, density, temperature)
        # brine_resistivity = np.nan
    else:
        # molar M>=0.01 to molality m<=0.1の場合
        # まずSKとQMを切り替えるmolalityを探す
        m_max = 0.1
        M_min = 0.01
        M_max = molality2molar(m_max, density)
        m_min = molar2molality(M_min, density)
        # print(m_max, M_max, m_min, M_min)
        diff = 999999999
        m_switch = 0.05
        if m_min >= m_max: 
            # そんなことはあるわけないけど一応対応
            brine_resistivity = \
                brine_resistivity_SK(x_nacl_l*100, pure_water_dens, temperature)
        # m_minからm_maxのうち、最もスムーズにSKとQMのモデルがつながるmolalityを探す
        logger.info(f"*** QM or SK. Start to search switching molality value ")
        for m in 10**np.linspace(math.log10(m_min), math.log10(m_max), 10): 
            logger.debug(f"searching... ")
            x_nacl = molality2massfrac(m)
            br_sk = brine_resistivity_SK(x_nacl*100, pure_water_dens, temperature)
            br_qm = brine_resistivity_QM(m, density, temperature)
            if diff > abs(br_sk-br_qm): 
                diff = abs(br_sk-br_qm)
                m_switch = m
                logger.info(f"*** m_switch found: {m_switch}")
                break
            logger.debug(f"    molality: {m:.4g}, res SK:{br_sk:.3g}, QM:{br_qm:.3g}")
        else:
            # m_swichが見つからない場合、SKモデルを使用。SKがだめなら->QMを使用.これでもだめならしかたなくnp.nan.
            logger.info(f"*** m_switch NOT found")
            brsk = brine_resistivity_SK(x_nacl_l*100, pure_water_dens, temperature)
            if not math.isnan(brsk):
                logger.info(f"molal:{molality:.4f} use SK")
                return brsk
            brqm = brine_resistivity_QM(molality, density, temperature)
            if not math.isnan(brqm):
                logger.info(f"molal:{molality:.4f} use QM")
                return brqm
            else:
                return np.nan


        if molality >= m_switch:
            # 切り替え点より高濃度
            brine_resistivity = \
                brine_resistivity_SK(x_nacl_l*100, pure_water_dens, temperature)
            logger.info(f"molal:{molality:.4f} use SK")
        else:
            # 切り替え点より低濃度
            brine_resistivity = \
                brine_resistivity_QM(molality, density, temperature)
            logger.info(f"molal:{molality:.4f} use QM")

    return brine_resistivity
   

def brine_resistivity_QM(molality, density, temperature):
    """[summary]
    Calculate resistivity value of brine based on the data by Quist & Marshall 
    (1968). 
    At first, compute a 2d interpolating function (linear) for each table 
    (table.I to table.VII). (equivalent conductance=f(temperature, densitiy)).
    Next, by using above function, calc eq. conductance values in each table at 
    given temp & dens. (We get molality values and corresponding eq.conductance 
    values).
    Then, by interpolating molality values and corresponding eq. conductance 
    values, we get a eq. condactance value at given molality, density
    and temperature.

    Args:
        molality (float): molality of brine [mol/kg]. 0.001 <= m <= 0.1.
        density (float): density of brine [g/cm^3]. 
        temperature (float): temperature of brine [C]. 100C <= T <= 350C.

    Returns:
        float : resistivity of brine [ohm-m]
    """ 
    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")

    if molality <= 0.001: 
        # molality = 0.001 # 仮
        return 100 # 仮
    if 0.1 <= molality: 
        # print("[t2outUtil.brine_resistivity_QM] given molality is out of range")
        molality = 0.1 # 仮
    if temperature < 100: 
        temperature = 100
    if 600 < temperature: 
        # print("[t2outUtil.brine_resistivity_QM] given temperature is out of range")
        temperature = 600
    if density > 1:
        density = 1
    
    # conductivity [S/m]
    conductivity = \
        lambda eq_cond, density, molality: eq_cond*density*molality*0.001*1e5
    # resistivity [ohmm]
    resistivity = \
        lambda eq_cond, density, molality: 1/(eq_cond*density*molality*0.1)

    ### choise of eq_cond func ###
    eq_func = qm.F_EQCOND_LINEARND
    # eq_func = qm.F_EQCOND_CUBIC
    ##############################
  
    list_of_eqcond_at_given_dens_temp = []
    # calc equivalent conductance for each molality value at given temp. and dens.
    for molality_index, m in enumerate(qm.MOLALITY_QM):
        list_of_eqcond_at_given_dens_temp\
            .append(float(eq_func[molality_index](density,temperature)))
    # imterpolate.
    # equivalent condactance[S*cm^-2/mol] = f(molality)
    f = interpolate.interp1d(qm.MOLALITY_QM,list_of_eqcond_at_given_dens_temp, 
                             kind='linear')
    res = resistivity(f(molality),density, molality)
    # print(res)
    if math.isnan(res):
        logger.info(f"resistivity: NaN @ molal:{molality:.4f}, density:{density:3g}, T:{temperature:3g}")
    return res

def brine_resistivity_SK(NaCl_concentration_wt, density, temperature):
    """[summary]
    Calculate resistivity value of brine based on the formulation by Sinmyo & Keppler (2017)
    Args:
        NaCl_concentration_wt ([float]): 0.058(0.01M) - 5.8(1M)[wt%]
        density ([float]): the density of pure water [g/cm^3] at given pressure and temperature
        temperature ([float]): T[C] > 100[C]
    Returns:
        float : resistivity of brine [ohm-m]
    """
    """ get logger """
    logger = define_logging.getLogger(
        f"{__name__}.{sys._getframe().f_code.co_name}")
    
    if temperature <= 100: 
        temperature = 100
    # Sinmyo & Keppler (2017)
    try:
        limit_molar_cond = \
            lambda Tc, rho: 1573-1212*rho+537062/(Tc+273)-208122721/(Tc+273)**2
        log10cond = \
            lambda Tc, c, rho, limit_molar_cond: \
                -1.7060-93.78/(Tc+273)+0.8075*math.log10(c)\
                +3.0781*math.log10(rho)+math.log10(limit_molar_cond)
        lmc = limit_molar_cond(temperature,density)
        # to avoid math domain error, if limit_molar_cond is larger than 0, return NaN
        if lmc < 0:
            logger.debug(f"limit_molar_cond became negative. return log10cond=np.nan @ xnacl{NaCl_concentration_wt:.3g}, dens{density:.3f}, T{temperature}")
            return np.nan
        l10c = log10cond(temperature, NaCl_concentration_wt, density, lmc)
    except ValueError:
        logger.warning("ValueError", NaCl_concentration_wt, density, temperature,lmc)
        raise
    return 1/10**l10c


# global
FUNC_DENS = {}
def brine_resistivity_Watanabe(P, T, molality, density=None):
    """_summary_
    Implementation of Norihiro Watanabe et al., “Electrical Conductivity of H 2 O-NaCl Fluids 
    under Supercritical Geothermal Conditions and Implications for Deep Conductors Observed 
    by the Magnetotelluric Method,” Geothermics 101 (May 2022): 102361, 
    https://doi.org/10.1016/j.geothermics.2022.102361.
    
    Args:
        P (): pressure in MPa
        T (): temperature in C
        molality (_type_): mol/kg-H2O
        density (optional): [kg/m3]. If None, density is calculated using brine_density_module (とても遅くなる).      
    Returns:
        _type_: _description_
    """
    
    a1 = 4.16975e-03
    a2 = -5.08206e-03
    a3 = 5.75588e-01
    a4 = 1.00422e+00
    b1 = 2.55008e+01
    b2 = 6.04911e-02
    b3 = 2.51861e+06
    b4 = 4.30952e-01
    c1 = -4.89245e-10
    c2 = -1.75339e-11

    A = a1 + (a2 - a1) / (1 + (molality/a3)**a4)
    B = 1 / ( (b1 + (b2 - b1) / (1 + (molality**0.5/b3)**b4)) * 1e6 )
    C = c1 + c2 * molality

    x = molality2massfrac(molality)
    viscosity = brine_viscosity_Kl(x, P, T) #[Pa s]

    molar_cond = A + B/viscosity + C/viscosity**2  #[Sm^2/mol]

    """brine density"""
    if density is None:
        global FUNC_DENS
        # density functionは何度も取得しない。一度取得したものはglobalに保持する
        if not str(molality) in FUNC_DENS:
            FUNC_DENS[str(molality)] = bdm.get_dens_func(
                    pressure=None, 
                    temperature=None, 
                    x_nacl_mol=x_wt2x_mol(molality2massfrac(molality))
                    )     
        density = float(FUNC_DENS[str(molality)]([P*1e6/1e5,T])) #[kg/m^3]
    
    # print(f"molarcond {molar_cond} density {density} molality {molality}")
    return 1 / molar_cond / molality2molar(molality, density) 


def brine_viscosity_Kl(mass_frac, P, T):
    """
    Implementation of Klyukin et al. (2017)
    A revised empirical model to calculate the dynamic viscosity of H2O-NaCl fluids 
    at elevated temperatures and pressures (<1000C, <500 MPa, 0-100 wt % NaCl)
    
    Args:
        mass_frac (): mass fraction of NaCl
        P (): pressure in MPa
        T (): temperature in C
    """
    
    a1 = -35.9858
    a2 = 0.80017
    b1 = 1e-6
    b2 = -0.05239 
    b3 = 1.32936

    e1 = a1 * mass_frac ** a2
    e2 = 1 - b1 * T ** b2 - b3 * mass_frac ** a2 * T ** b2
    equiv_T = e1 + e2 * T
    
    if equiv_T <= 0:
        return math.nan

    try:
        return IAPWS97(T=equiv_T+273.15,P=P).mu # dynamic viscosity [Pa-s]
    except:
        print(f"equiv_T {equiv_T}, P {P}, T {T}, massfrac {mass_frac}")
        raise



def HS_bounds(proportion_phs2, sigma1, sigma2):
    """[summary]
    phase1 is matrix. phase2 is pore fluid.
    sigma2 > sigma1.

    Args:
        proportion_phs2 ([type]): [description]
        sigma1 ([type]): [description]
        sigma2 ([type]): [description]

    Returns:
        tuple: (conductivity[S/m](HS upper bounds), conductivity[S/m](HS lower bounds))
    """
    if sigma1 == sigma2:
        cond_upper, cond_lower = sigma1, sigma1
    else:
        a = 3*(1-proportion_phs2)*(sigma2-sigma1)\
            /(3*sigma2-proportion_phs2*(sigma2-sigma1))
        cond_upper = sigma2*(1-a)
        b = 3*proportion_phs2*(sigma2-sigma1)\
            /(3*sigma1+(1-proportion_phs2)*(sigma2-sigma1))
        cond_lower = sigma1*(1+b)

    return cond_upper, cond_lower

def calc_molality(df_elem:pd.DataFrame):
    df_elem['molality'] = df_elem.apply(_df_elem_calc_bulk_molality, axis=1)
    return np.array(df_elem['molality'])

def _df_elem_calc_bulk_molality(row:pd.Series):
    """[summary]
    Args:
        row (pd.Series): element of returned dict. by read_output_eleme_csv()
    Returns:
        [float] : bulk resistivity 
    """
    NaCl_FORMULA_WEIGHT = 58.5
    molality = 1000*row['X_NaCl_L']/(1-row['X_NaCl_L'])/NaCl_FORMULA_WEIGHT # NaCl molality[mol/kg]
    return molality

def get_cbar_limits(variable_name):
    """
    This method selects the appropriate cbar based on the FLAG NAME.
    """
    if FLAG_NAME_TEMP in variable_name.lower(): 
        return CBAR_LIM_TEMP
    elif FLAG_NAME_SAT in variable_name.lower(): 
        return CBAR_LIM_SAT
    elif FLAG_NAME_RES in variable_name.lower():
        return CBAR_LIM_LOG10RES 
    elif FLAG_NAME_X_NACL_L in variable_name.lower(): 
        return CBAR_LIM_NaCl_CONTENT
    else: 
        return None

def get_cbar_limits_flow(variable_name):
    """
    This method selects the appropriate cbar based on the FLAG NAME.
    """
    if FLAG_NAME_FLOW in variable_name.lower(): 
        return CBARLIMIT_DEFAULT_FLOW
    elif FLAG_NAME_HEAT in variable_name.lower(): 
        return CBARLIMIT_DEFAULT_HEAT
    return None

def get_unit(variable_name):
    """
    This method selects the appropriate unit name based on the FLAG NAME.
    """
    if FLAG_NAME_TEMP in variable_name.lower(): 
        return UNIT_TEMP
    elif FLAG_NAME_SAT in variable_name.lower(): 
        return UNIT_SAT
    else: 
        return None

def get_contour_intbal(variable_name):
    """
    This method selects the appropriate contour interbal from define.py based on the FLAG NAME.
    """
    if FLAG_NAME_TEMP in variable_name.lower(): 
        return CONTOUR_TEMP
    elif FLAG_NAME_SAT in variable_name.lower(): 
        return CONTOUR_SAT
    elif FLAG_NAME_RES in variable_name.lower(): 
        return CONTOUR_RES
    else: 
        return False

def surface_flow_map_from_listing(ini:_readConfig.InputIni, 
                                  dat:t2data, geo:mulgrid,
                                  lst:t2listing):
    # escape outputfiles
    escape_t3outfiles(ini)
    create_savefig_dir(ini)

    # prepare df
    df_conn = lst.connection.DataFrame

    # prepare container to be returned
    # ret['HEAT']->地表での'HEAT'の流量リスト(geo.columnlistと同じ順番で格納)
    ret = {}
    for col in df_conn.columns:
        if 'row' in col.lower(): continue
        ret[col] = []

    # get list of connection     
    # conn_list_suf = []
    # surfblk_name_list = []
    # surfblk_pos_x_list = []
    # surfblk_pos_y_list = []
    # surf_area_list = []
    for col in geo.columnlist:
        layer_top = geo.column_surface_layer(col)
        blockname_top = geo.block_name(layer_top.name, col.name)
        # surfblk_name_list.append(blockname_top)
        # surfblk_pos_x_list.append(col.centre[0])
        # surfblk_pos_y_list.append(col.centre[1])
        conn = (blockname_top,'ATM 0')
        connr = ('ATM 0', blockname_top)
        if conn in dat.grid.connection: 
            # conn_list_suf.append(conn)
            for key, value in ret.items():
                ret[key].append(-1*float(df_conn[df_conn['row'] == conn][key])/col.area)
        elif connr in dat.grid.connection: 
            # conn_list_suf.append(connr)
            for key, value in ret.items():
                ret[key].append(float(df_conn[df_conn['row'] == connr][key])/col.area)
        else:
            for key in ret:
                ret[key].append(None)
    return ret

    
    # cols = np.array(df_conn.columns)
    # df_uppwd = df_conn[df_conn.row.map(_includesATMinTupleElem0)]
    # df_uownwd = -1*df_conn[df_conn.row.map(_includesATMinTupleElem1)]
    # # return df_uppwd
    # return df_uownwd

def surface_flow_map_from_COFT(ini:_readConfig.InputIni, dat:t2data, geo:mulgrid):
    """[summary]
    全timestepにおけるsurfaceflowをCOTから作成

    Args:
        ini (_readConfig.InputIni): [description]
        dat (t2data): [description]
        geo (mulgrid): [description]

    Returns:
        (allflows, timesteps) [tuple]:
            example)
            allflows[i]['              HEAT']-> 時刻timesteps[i]の各columnのtopの流量のリスト
                                               （順番はgeo.columnlistに従うのでそのままlayer_plotに渡してOK）
    """
    # 使い所??
    # escape outputfiles
    escape_t3outfiles(ini)
    create_savefig_dir(ini)

    if not ini.toughInput['prints_hc_surface']:
        print(f"[t2outUtil.surface_flow_map] option "\
                +"'prints_hc_surface' is False in ini file. skip")
        return None, None

    conn_list_suf = []
    surfblk_name_list = []
    surfblk_pos_x_list = []
    surfblk_pos_y_list = []
    for col in geo.columnlist:
        layer_top = geo.column_surface_layer(col)
        blockname_top = geo.block_name(layer_top.name, col.name)
        surfblk_name_list.append(blockname_top)
        surfblk_pos_x_list.append(col.centre[0])
        surfblk_pos_y_list.append(col.centre[1])
        conn = (blockname_top,'ATM 0')
        if (conn[0],conn[1]) in dat.grid.connection\
            or (conn[1],conn[0]) in dat.grid.connection: 
            conn_list_suf.append(conn)
        else:
            # geo.columnlistの順番との一貫性を保つためダミー要素を追加
            conn_list_suf.append(None)

    
    # read COFT file of surface flow
    coft_df_list = []
    direction_list = []
    for tup in conn_list_suf:
        if tup is None: 
            # geo.columnlistの順番との一貫性を保つためダミー要素を追加
            coft_df_list.append(None)
            direction_list.append(None)
            continue

        # read csv file and convert to dataframe
        try:
            csv = \
                f"COFT_{tup[0].replace(' ','_')}_{tup[1].replace(' ','_')}.csv"
            csvfp = os.path.join(ini.t3outEscapeFp, csv)
            df = pd.read_csv(csvfp)
            direction_list.append(-1)
        except FileNotFoundError:
            csvfp = os.path.join(ini.t3outEscapeFp, csv)
            csv = \
                f"COFT_{tup[1].replace(' ','_')}_{tup[0].replace(' ','_')}.csv"
            df = pd.read_csv(csvfp)
            direction_list.append(1)

        coft_df_list.append(df)

    # get timesteps and column names
    timesteps = None
    variable_names = []
    for cdf in coft_df_list:
        if cdf is None: continue
        for var in cdf.columns:
            if re.search('TIME', var):
                timesteps = copy.deepcopy(cdf[var])
            else:
                variable_names.append(var)
        break
        
    # タイムステップごとの辞書Aを格納。順番はtimestepsに従う
    # B[i]['HEAT']-> 時刻iの各
    B = []
    for itime,_ in enumerate(timesteps):
        #　あるタイムステップにおいて、flow変数名がキー、各surface flowの値のリストがアイテムとなる辞書。
        A={}
        for var in variable_names:
            key=var.strip()
            A[key] = []
            for i,col in enumerate(geo.columnlist):
                if coft_df_list[i] is None:
                    A[key].append(None)
                    continue
                A[key].append(direction_list[i]*coft_df_list[i][var][itime]/col.area)
        B.append(A)
    return B, timesteps

sec2yearDayTime = lambda y : \
            f'{y//31557600}yr{y%31557600//86400:03}day '\
            +f'{y%31557600%86400//3600:02}:'\
            +f'{y%31557600%86400%3600//60:02}:'\
            +f'{y%31557600%86400%3600%60:02}'

sec2year = lambda y : \
            f'{y//31557600:>10.0f}yr {y%31557600//86400:>4.3f}day'

if  __name__ == '__main__':
    pass