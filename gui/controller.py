from ast import Name
from distutils.command.config import config
from imp import init_builtin
# from distutils.log import error
import os 
import sys
import pathlib

from numpy import isin
# from unittest import result
baseDir = pathlib.Path(__file__).parent.resolve()
sys.path.append(baseDir)
sys.path.append(os.path.join(baseDir,".."))
projRoot = os.path.abspath(os.path.join(baseDir,".."))
from import_pytough_modules import *
import _readConfig
import makeGridAmeshVoro
import tough3exec_ws
from flask import Flask
from flask import render_template
from flask import Markup
from flask import request
# from flask import session
# from flask import g
from flask import redirect, url_for
# from t2grids import rocktype
import define_logging
import configparser
from mulgrids import *
import math
import dict_gui
import time
import shutil
import pickle
from constants import Const

app = Flask(__name__, static_folder='static', static_url_path='')

# Constの中身をそのままjinja2でつかえるようにする
from constants import Const
app.jinja_env.globals.update(Const.__dict__)

""" In order to use sessions you have to set a secret key. """
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def create_fullpath(pathstr):
    if os.path.isabs(pathstr):
        return pathstr
    else:
        # create abspath from relpath
        return os.path.abspath(os.path.join(projRoot, pathstr))

def create_relpath(pathstr):
    # relative path from project root
    return os.path.relpath(create_fullpath(pathstr), start=projRoot)



@app.route('/')
def index():
    """
    This function returns the message we want to display in the user's browser. 
    The default content type is HTML, so HTML in the string will be rendered by the browser.
    """
    return app.send_static_file('index.html')

@app.route('/test')
def test():
    return app.send_static_file('input_voronoi_no_pmx.html')

@app.route('/cmesh1/')
def cmesh1():
    """
    Flask will look for templates in the `templates` folder. 
    So if your application is a module, this folder is next to that module, 
    if it's a package it's actually inside your package.
    For templates you can use the full power of Jinja2 templates. 
    Head over to the official `Jinja2 Template Documentation <https://jinja.palletsprojects.com/templates/>`_ for more information.
    """
    return render_template('cmesh1.html', button_str="check")

@app.route('/usage/')
def usage():
    return app.send_static_file('usage.html')

@app.route('/cmesh1_check', methods=['GET', 'POST'])
def cmesh1_check():
    if request.method == 'POST':
        configIniFp = create_fullpath(request.form['configIniFp'])
        # check file existence
        error_msg = {}
        if os.path.isfile(configIniFp):
            configlines = []
            with open(configIniFp, "r") as f:
                for line in f:
                    configlines.append(line)
            # SettingIniは一時的。またcmesh2_checkで作り直す
            settingIni = _readConfig.SettingIni(configIniFp)
            saveDir = create_fullpath(settingIni.toughConfig.TOUGH_INPUT_DIR)
            if not os.path.isdir(saveDir):
                error_msg["TOUGH_INPUT_DIR"] = f"{saveDir}   does not exist. Please create."
        else:
            error_msg["configIniFp"] = f"{configIniFp}   does not exist. Please specify correct location."
        
        if len(error_msg) > 0:
            return render_template('cmesh1.html', error_msg=error_msg, form=request.form, configIniFp=configIniFp, goes_next=False)
        else:
            # if No error,
            # then, show "Go next button"
            return render_template('cmesh1.html', form=request.form, configlines=configlines, saveDir=saveDir, configIniFp=configIniFp, goes_next=True)

    else:
        return redirect(url_for('index'))


@app.route('/cmesh2', methods=['GET', 'POST'])
def cmesh2():
    return render_template('cmesh2.html', form=request.form, created=False)
    # if request.method == 'POST':
    #     return render_template('cmesh2.html', form=request.form, created=False)
    # else:
    #     return redirect(url_for('index'))

@app.route('/cmesh2_check', methods=['GET', 'POST'])
def cmesh2_check():
    if request.method == 'POST':
        if int(request.form['createsMesh'])==1:
            """ create new mesh """
            topodata_fp_full = create_fullpath(request.form['topodata_fp'])
            voronoi_seeds_list_fp = create_fullpath(request.form['voronoi_seeds_list_fp'])

            """validation"""
            error_msg = {}
            if not os.path.isfile(topodata_fp_full):
                error_msg["topodata_fp"] = f"{topodata_fp_full}   does not exist. Please create."
            if not os.path.isfile(voronoi_seeds_list_fp):
                error_msg["voronoi_seeds_list_fp"] = f"File: {voronoi_seeds_list_fp}   does not exist. Please create."
            if os.path.isdir(create_fullpath(request.form['mulgridFileFp'])):
                error_msg["mulgridFile_fp_dir"] = f"{request.form['mulgridFileFp']} is directory. Please specify different file path."
            elif os.path.isfile(create_fullpath(request.form['mulgridFileFp'])):
                error_msg["mulgridFile_fp"] = f"{create_fullpath(request.form['mulgridFileFp'])}  already exist. Please specify different file path."
            if not os.path.isdir(create_fullpath(os.path.dirname(request.form['mulgridFileFp']))):
                error_msg["mulgridDir"] = f"Directory: {create_fullpath(os.path.dirname(request.form['mulgridFileFp']))} does not exist. Please create it beforehand."
            try:
                _ = eval(request.form['layer_thicknesses'])
                if not isinstance(_, (tuple, list, np.ndarray)):
                    error_msg["layer_thicknesses"] = f"'layer_thicknesses' must be 'list', 'tuple', or 'numpy.ndarray'."
            except:
                error_msg["layer_thicknesses"] = f"error in 'layer_thicknesses': Can not interpret '{request.form['layer_thicknesses']}'."


            if len(error_msg) > 0:
                return render_template('cmesh2.html', error_msg=error_msg, form=request.form, created=False)

            """ _readConfig.InputIniインスタンス作成"""
            inputIni = _readConfig.InputIni()
            inputIni.toughInput = {}
            inputIni.mesh.type = AMESH_VORONOI
            config = {}
            config['amesh_voronoi'] = request.form
            inputIni.mulgridFileFp = create_fullpath(request.form['mulgridFileFp'])
            inputIni.amesh_voronoi = _readConfig.InputIni._AmeshVoronoi().read_from_config(config)
            inputIni.mesh.convention = int(request.form['convention'])
            inputIni.atmosphere.includesAtmos = eval(request.form['includesAtmos'])

            # create mesh file
            makeGridAmeshVoro.create_mulgrid_with_topo(inputIni)

            # ラジオボタンcreatesMeshを"Use existing mulgrid file"に切り替える
            tmp = dict(request.form)
            return render_template('cmesh2.html', form=tmp, created = True,  msg="mulgrid file successfully created")


        elif int(request.form['createsMesh'])==0:
            print(request.form)
            """ use existing mesh """
            # check file existence
            error_msg = {}
            mulgridFileFp = create_fullpath(request.form['mulgridFileFp'])
            if not os.path.isfile(mulgridFileFp):
                error_msg["mulgridFile_fp"] = f"File: {mulgridFileFp}  was not found. Please specify correct file path."
            if len(error_msg) > 0:
                return render_template('cmesh2.html', error_msg=error_msg, form=request.form, created=False)
            
            tmp = dict(request.form)
            # 値の削除
            try:
                tmp.pop('convention')
                tmp.pop('includesAtmos')
                tmp.pop('topodata_fp')
                tmp.pop('voronoi_seeds_list_fp')
                tmp.pop('elevation_top_layer')
                tmp.pop('layer_thicknesses')
                tmp.pop('tolar')
                tmp.pop('top_layer_min_thickness')
            except:
                # 握りつぶす
                pass
            
            # int(request.form['createsMesh'])==1でcreatedのときと同じ扱い
            return render_template('cmesh2.html', form=tmp, created = True, msg=f"mulgrid file {create_relpath(mulgridFileFp)} was found")
    else:
        return redirect(url_for('index'))

@app.route('/cmesh3', methods=['GET', 'POST'])
def cmesh3():
    if request.method == 'POST':
        return render_template('cmesh3.html', form=request.form)
    else:
        return redirect(url_for('index'))


def cmesh3_validate(request:request):
    error_msg = {}
    if not os.path.isdir(create_fullpath(request.form['saveDir'])):
        error_msg['saveDir']= f"Problem directory: {request.form['saveDir']}"\
                              f" was not found. Please create the directory first."

    if not os.path.isfile(create_fullpath(request.form['resistivity_structure_fp'])):
        error_msg['resistivity_structure_fp']= \
            f"Resistivity structure data: "\
            f"'{create_fullpath(request.form['resistivity_structure_fp'])}'"\
            " not found" 
    if os.path.isdir(os.path.join(request.form['saveDir'], 
                                  request.form['problemName']))\
            and not 'overwrites_prob' in request.form:
        error_msg['problemName']= \
            f"problem: "\
            f"'{os.path.join(request.form['saveDir'],request.form['problemName'])}'"\
            f" already exists." 

    # validation用ダミー変数&クラス
    rho, x, y, z, k_x, k_y, k_z, phi, surface, depth, porosity, perm = 1,2,3,4,5,6,7,8,9,10,11,12
    class fu():
        def HS_U_conductivity2porosity(self, rho, cond_matrix, cond_liq, upper, lower):
            pass

    for rock_id in range(Const.ROCKTYPE_LEN):
        try:
            # 長さが0だとevalでエラーになる
            if len(request.form[f'rock{rock_id}_formula_permeability'])>0:
                eval(request.form[f'rock{rock_id}_formula_permeability'])
        except:
            error_msg[f'rock{rock_id}_formula_permeability'] = \
                f"Rocktype#{rock_id}[formula_permeability]:python cannot interpret '{request.form[f'rock{rock_id}_formula_permeability']}'"
        else:
            if len(request.form[f'rock{rock_id}_formula_permeability'])>0:
                if 'seedFlg' in request.form and eval(request.form[f'rock{rock_id}_formula_permeability']) is None:
                    error_msg[f'rock{rock_id}_formula_permeability'] = \
                        f"Rocktype#{rock_id}[formula_permeability] must not be None when 'seedFlg' is True"
        try:
            if len(request.form[f'rock{rock_id}_formula_porosity'])>0:
                eval(request.form[f'rock{rock_id}_formula_porosity'])
        except:
            error_msg[f'rock{rock_id}_formula_porosity'] = \
                f"Rocktype#{rock_id}[formula_porosity]:python cannot interpret '{request.form[f'rock{rock_id}_formula_porosity']}'"
        try:
            if len(request.form[f'rock{rock_id}_rock_assign_condition'])>0:
                eval(request.form[f'rock{rock_id}_rock_assign_condition'])
        except:
            error_msg[f'rock{rock_id}_rock_assign_condition'] = \
                f"Rocktype#{rock_id}[rock_assign_condition]:python cannot interpret '{request.form[f'rock{rock_id}_rock_assign_condition']}'"
    
    return error_msg
        

@app.route('/cmesh3_check', methods=['GET', 'POST'])
def cmesh3_check():
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    if request.method == 'POST':
        # print(request.form)
        config = {}
        rocktype_names = []
        logger.debug(request.form)
        
        """validate"""
        error_msg = cmesh3_validate(request)
        logger.debug(error_msg)
        if len(error_msg) > 0:
            return render_template('cmesh3.html', form=request.form, error_msg=error_msg)
        
        """ _readConfig.InputIniインスタンス作成"""
        if len(request.form["original_iniFp"])>0:
            # cmesh3_readFromIniからのとき、ファイルから読み込み、画面で入力された値で上書きする
            try:
                # cmesh3_readFromIniで完全なiniファイルを読んだ場合
                inputIni = _readConfig.InputIni().read_from_inifile(request.form["original_iniFp"])
                # rockSecListをリセットしておく
                inputIni.toughInput['rockSecList'] = []
                inputIni.rockSecList = []
            except InvalidToughInputException:
                # cmesh3_readFromIniで不完全なiniファイル読んだ場合(cmesh4終了時にできるiniなど)、もう一度作る
                inputIni = _readConfig.InputIni()
                inputIni.toughInput = {}
        else:
            # cmesh2からのときもう一度作る
            inputIni = _readConfig.InputIni()
            inputIni.toughInput = {}
            
        inputIni.mesh.type = AMESH_VORONOI
        inputIni.mesh.mulgridFileFp = create_relpath(request.form['mulgridFileFp'])
        if int(request.form['createsMesh'])==1:
            config_av = {}
            config_av['amesh_voronoi'] = request.form
            inputIni.amesh_voronoi = _readConfig.InputIni._AmeshVoronoi().read_from_config(config_av)
            inputIni.mesh.convention = int(request.form['convention'])
            # inputIni.atmosphere.includesAtmos = eval(request.form['includesAtmos'])
        else: 
            # detect mesh convention
            geo = mulgrid(inputIni.mesh.mulgridFileFp)
            inputIni.mesh.convention = geo.convention
        
        """problem dir."""
        config['configuration'] = {}
        config['configuration']['TOUGH_INPUT_DIR'] = create_relpath(request.form['saveDir'])
        inputIni.configuration = _readConfig.InputIni._Configuration().read_from_config(config)
        """problem name"""
        inputIni.toughInput['problemName'] = request.form[f'problemName']
        """resistivity_structure_fp"""
        inputIni.mesh.resistivity_structure_fp = create_relpath(request.form[f'resistivity_structure_fp'])
        inputIni.construct_path()


        """seedflg"""
        inputIni.toughInput['seedFlg'] =  True if 'seedFlg' in request.form else False
        """boundary_side_permeable"""
        inputIni.boundary.boundary_side_permeable =  True if 'boundary_side_permeable' in request.form else False
        """atmosphere"""
        config['atmosphere'] = {}
        # config['atmosphere']['includesAtmos'] = 'True' if 'includes_atmos' in request.form else 'False'
        config['atmosphere']['includesAtmos'] = request.form[f'includesAtmos']
        config['atmosphere']['PRIMARY_AIR'] = '[]' # 仮 (cmesh5で埋める)
        config['atmosphere']['density'] = request.form[f'atmos_density']
        config['atmosphere']['porosity'] = request.form[f'atmos_porosity']
        config['atmosphere']['permeability'] = (f'[{request.form["atmos_permeability_x"]}, '
                                                f'{request.form["atmos_permeability_y"]}, '
                                                f'{request.form["atmos_permeability_z"]}]')
        config['atmosphere']['conductivity'] = request.form[f'atmos_conductivity']
        config['atmosphere']['specific_heat'] = request.form[f'atmos_specific_heat']
        config['atmosphere']['nad'] = 0
        if len(request.form[f'atmos_tortuosity'])>0:
            config['atmosphere']['nad'] = 1
            config['atmosphere']['tortuosity'] = request.form[f'atmos_tortuosity']
        if int(request.form['atmos_irp'])!=0 or int(request.form['atmos_icp'])!=0:
            config['atmosphere']['nad'] = 2
            config['atmosphere']['RP'] = request.form['atmos_rp']
            config['atmosphere']['IRP'] = request.form['atmos_irp']
            config['atmosphere']['CP'] = request.form['atmos_cp']
            config['atmosphere']['ICP'] = request.form['atmos_icp']
        inputIni.atmosphere = _readConfig.InputIni._Atmosphere().read_from_config(config)

        """rocktypes"""
        for rock_id in range(Const.ROCKTYPE_LEN):
            name = request.form[f'rock{rock_id}_name']
            if len(name.strip())==0: 
                continue
            else: 
                config[name] = {}
                config[name]['name'] = name
                rocktype_names.append(name)
                config[name]['density'] = float(request.form[f'rock{rock_id}_density'])
                config[name]['porosity'] = float(request.form[f'rock{rock_id}_porosity'])
                config[name]['permeability_x'] = float(request.form[f'rock{rock_id}_permeability_x'])
                config[name]['permeability_y'] = float(request.form[f'rock{rock_id}_permeability_y'])
                config[name]['permeability_z'] = float(request.form[f'rock{rock_id}_permeability_z'])
                config[name]['conductivity'] = float(request.form[f'rock{rock_id}_conductivity'])
                config[name]['specific_heat'] = float(request.form[f'rock{rock_id}_specific_heat'])
            
                irp = int(request.form[f'rock{rock_id}_irp'])
                icp = int(request.form[f'rock{rock_id}_icp'])
                if irp==0 and icp==0:
                    config[name]['nad'] = 0
                else:
                    config[name]['nad'] = 2
                    config[name]['IRP'] = irp
                    config[name]['RP'] = request.form[f'rock{rock_id}_rp']
                    config[name]['ICP'] = icp
                    config[name]['CP'] = request.form[f'rock{rock_id}_cp']
                
                config[name]['blocklist'] = request.form[f'rock{rock_id}_blockList'] \
                    if len(request.form[f'rock{rock_id}_blockList'])>0 else "[]"
                config[name]['formula_porosity'] = request.form[f'rock{rock_id}_formula_porosity'] \
                    if len(request.form[f'rock{rock_id}_formula_porosity'])>0 else "None"
                config[name]['formula_permeability'] = request.form[f'rock{rock_id}_formula_permeability'] \
                    if len(request.form[f'rock{rock_id}_formula_permeability'])>0 else "None"
                config[name]['rock_assign_condition'] = request.form[f'rock{rock_id}_rock_assign_condition'] \
                    if len(request.form[f'rock{rock_id}_rock_assign_condition'])>0 else "True"

                regionSecList = []
                for region_id in range(0,int(request.form[f'rock{rock_id}_region_length'])):
                    if len(request.form[f'rock{rock_id}_reg{region_id}_xmin'].strip())==0\
                            or len(request.form[f'rock{rock_id}_reg{region_id}_xmax'].strip())==0\
                            or len(request.form[f'rock{rock_id}_reg{region_id}_ymin'].strip())==0\
                            or len(request.form[f'rock{rock_id}_reg{region_id}_ymax'].strip())==0\
                            or len(request.form[f'rock{rock_id}_reg{region_id}_zmin'].strip())==0\
                            or len(request.form[f'rock{rock_id}_reg{region_id}_zmax'].strip())==0:
                        continue

                    regionSecName = f'{name}_region{region_id}'
                    regionSecList.append(regionSecName)
                    config[regionSecName] = {}
                    config[regionSecName]['xmin'] = float(request.form[f'rock{rock_id}_reg{region_id}_xmin'])
                    config[regionSecName]['xmax'] = float(request.form[f'rock{rock_id}_reg{region_id}_xmax'])
                    config[regionSecName]['ymin'] = float(request.form[f'rock{rock_id}_reg{region_id}_ymin'])
                    config[regionSecName]['ymax'] = float(request.form[f'rock{rock_id}_reg{region_id}_ymax'])
                    config[regionSecName]['zmin'] = float(request.form[f'rock{rock_id}_reg{region_id}_zmin'])
                    config[regionSecName]['zmax'] = float(request.form[f'rock{rock_id}_reg{region_id}_zmax'])
                
                config[name]['regionSecList'] = repr(regionSecList)
                logger.debug(regionSecList)

                if not 'rockSecList' in inputIni.toughInput:
                    inputIni.toughInput['rockSecList'] = [name]
                    inputIni.rockSecList = [_readConfig.InputIni._RocktypeSec(name, config)]
                else:
                    inputIni.toughInput['rockSecList'].append(Name)
                    inputIni.rockSecList.append(_readConfig.InputIni._RocktypeSec(name, config))
        
        """check & create"""
        inputIni.rocktypeDuplicateCheck()
        # create save dir. 
        os.makedirs(inputIni.t2FileDirFp, exist_ok=True)

        inputIni.inputIniFp = os.path.join(projRoot, inputIni.t2FileDirFp, "input.ini")
        inputIni.output2inifile(inputIni.inputIniFp)
        
        # pickle for cmesh4_visualize()
        with open(os.path.join(os.path.dirname(inputIni.inputIniFp), 
                               PICKLED_INPUTINI), 
                  'wb') as f:
            pickle.dump(inputIni, f)   
        logger.debug(inputIni.mulgridFileFp)
        # create t2data
        makeGridAmeshVoro.makePermVariableVoronoiGrid(inputIni, fex="png")

        """copy images to static/output"""
        show_images = copy_visualized_mulgrid_imgs(inputIni)
        
        """prepare form"""
        new_prob_fp = inputIni.t2FileDirFp
        tmp = dict(request.form)
        tmp['inputIniFp'] = inputIni.inputIniFp
        tmp['t2GridFp'] = inputIni.t2GridFp
        tmp['t2FileDirFp'] = inputIni.t2FileDirFp
        if inputIni.plot.slice_plot_limits is not None:
            tmp['xmin'] = min(inputIni.plot.slice_plot_limits[0])
            tmp['xmax'] = max(inputIni.plot.slice_plot_limits[0])
            tmp['zmin'] = min(inputIni.plot.slice_plot_limits[1])
            tmp['zmax'] = max(inputIni.plot.slice_plot_limits[1])
        for i in range(6):
            tmp[f'line_{i}'] = ""
        for i, line in enumerate(inputIni.plot.profile_lines_list):
            if isinstance(line, np.ndarray): 
                # 文字列に変換するとおかしくなるのでlistに戻す
                tmp[f'line_{i}'] = repr([list(line[0]), list(line[1])])
            else: 
                tmp[f'line_{i}'] = line
        
        # return render_template('cmesh4.html', form=tmp, rocktypes=config, rocktype_names=rocktype_names, new_prob_fp=new_prob_fp, show_images=show_images, inputIniFp=inputIni.inputIniFp)
        return render_template('cmesh4.html', 
                               form=tmp, 
                               new_prob_fp=new_prob_fp, 
                               show_images=show_images,
                               inputIniFp=inputIni.inputIniFp)
    else:
        return redirect(url_for('index'))

@app.route('/cmesh3_readFromIni', methods=['GET', 'POST'])
def cmesh3_readFromIni():
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    if request.method == 'POST':
        
        iniFp = create_fullpath(request.form["original_iniFp"])
        if not os.path.isfile(iniFp):
            return redirect(url_for('index'))
        
        #_readConfig.InputIniインスタンス作成
        inputIni = _readConfig.InputIni()
        config = configparser.ConfigParser(defaults=None)
        config.read(iniFp)
        
        # エラー承知で読み込む
        try:
            inputIni.read_from_inifile(iniFp)
        except InvalidToughInputException:
            # [toughInput]が不完全な場合はエラーになる。
            # エラーは握りつぶして、変わりに必要となる処理をここで行う
            inputIni.toughInput = {}
            inputIni.toughInput['rockSecList'] = eval(config['toughInput']['rockseclist'])
            inputIni.rockSecList = []
            for rockSec in inputIni.toughInput['rockSecList']:
                inputIni.rockSecList.append(inputIni._RocktypeSec(rockSec, config))
            inputIni.toughInput['problemName'] = config['toughInput']['problemname']
            try:
                # for backward compatibility (inputIni.mesh.mulgridFileFpに移動済み)
                inputIni.toughInput['mulgridFileName'] = config['toughInput']['mulgridfilename']
            except:
                # 握りつぶす
                pass
            inputIni.toughInput['seedFlg'] = eval(config['toughInput']['seedflg'])
            inputIni.construct_path()
            inputIni.validation()

        # htmlで表示できるようにformに展開する
        form = convert_InputIni2form_cmesh3(inputIni, dict(request.form))
        logger.debug(form)

        return render_template('cmesh3.html', form=form)
    else:
        return redirect(url_for('index'))

def convert_InputIni2form_cmesh3(ini:_readConfig.InputIni, form=None):
    """ 
    InputIniオブジェクトをhtmlで表示できるようにdictionaryに展開する 

    [amesh_voronoi]
    voronoi_seeds_list_fp
    elevation_top_layer
    layer_thicknesses
    tolar
    top_layer_min_thickness

    saveDir
    convention
    createsMesh
    topodata_fp
    
    mulgridFileFp
    problemName
    resistivity_structure_fp
    seedFlg
    boundary_side_permeable
    includes_atmos
    
    atmos_tortuosity
    atmos_irp
    atmos_rp
    atmos_icp
    atmos_cp
    atmos_density
    atmos_porosity
    atmos_permeability_x
    atmos_permeability_y
    atmos_permeability_z
    atmos_conductivity
    atmos_specific_heat
    atmos_primary    

    """
    logger = define_logging.getLogger(f"controller.{sys._getframe().f_code.co_name}")
    if form is None:
        # 新規作成モード
        ret = {}
    else:
        # 追記モード
        ret = form
    ret["saveDir"] = create_fullpath(ini.configuration.TOUGH_INPUT_DIR)
    ret["convention"] = ini.mesh.convention
    if hasattr(ini, 'amesh_voronoi'):
        if hasattr(ini.amesh_voronoi, 'topodata_fp')\
                and hasattr(ini.amesh_voronoi, 'voronoi_seeds_list_fp')\
                and hasattr(ini.amesh_voronoi, 'elevation_top_layer')\
                and hasattr(ini.amesh_voronoi, 'layer_thicknesses')\
                and hasattr(ini.amesh_voronoi, 'tolar')\
                and hasattr(ini.amesh_voronoi, 'top_layer_min_thickness'):
            ret["createsMesh"] = 1
            ret["topodata_fp"] = ini.amesh_voronoi.topodata_fp
            ret["voronoi_seeds_list_fp"] = ini.amesh_voronoi.voronoi_seeds_list_fp
            ret["elevation_top_layer"] = ini.amesh_voronoi.elevation_top_layer
            ret["layer_thicknesses"] = ini.amesh_voronoi.layer_thicknesses
            ret["tolar"] = ini.amesh_voronoi.tolar
            ret["top_layer_min_thickness"] =  ini.amesh_voronoi.top_layer_min_thickness
        else:
            ret["createsMesh"] = 0
    else:
        ret["createsMesh"] = 0
    ret["mulgridFileFp"] = create_fullpath(ini.mesh.mulgridFileFp)
    ret["problemName"] = ini.toughInput['problemName']
    ret["resistivity_structure_fp"] = create_relpath(ini.mesh.resistivity_structure_fp)
    ret["seedFlg"] = "uses" if ini.toughInput['seedFlg'] else ""
    ret["boundary_side_permeable"] = "uses" if ini.boundary.boundary_side_permeable else ""
    # ret["includes_atmos"] = "uses" if ini.atmosphere.includesAtmos else ""
    ret["includesAtmos"] = "True" if ini.atmosphere.includesAtmos else "False"
    if ini.atmosphere.atmos.nad >= 1:
        ret["atmos_tortuosity"] =  ini.atmosphere.atmos.tortuosity
    if ini.atmosphere.atmos.nad >= 2:
        ret["atmos_irp"] = str(ini.atmosphere.atmos.relative_permeability['type'])
        ret["atmos_rp"] = ini.atmosphere.atmos.relative_permeability['parameters']
        ret["atmos_icp"] = str(ini.atmosphere.atmos.capillarity['type'])
        ret["atmos_cp"] = ini.atmosphere.atmos.capillarity['parameters']
    ret["atmos_density"] =  ini.atmosphere.atmos.density
    ret["atmos_porosity"] =  ini.atmosphere.atmos.porosity
    ret["atmos_permeability_x"] =  ini.atmosphere.atmos.permeability[0]
    ret["atmos_permeability_y"] =  ini.atmosphere.atmos.permeability[1]
    ret["atmos_permeability_z"] =  ini.atmosphere.atmos.permeability[2]
    ret["atmos_conductivity"] =  ini.atmosphere.atmos.conductivity
    ret["atmos_specific_heat"] =  ini.atmosphere.atmos.specific_heat
    ret["atmos_primary"] =  ini.atmosphere.PRIMARY_AIR

    for rock_id, rock in enumerate(ini.rockSecList):
        logger.debug(rock.secName)
        ret[f"rock{rock_id}_name"] = rock.name
        ret[f"rock{rock_id}_density"] = rock.density
        ret[f"rock{rock_id}_porosity"] = rock.porosity
        ret[f"rock{rock_id}_permeability_x"] = rock.permeability_x
        ret[f"rock{rock_id}_permeability_y"] = rock.permeability_y
        ret[f"rock{rock_id}_permeability_z"] = rock.permeability_z
        ret[f"rock{rock_id}_conductivity"] = rock.conductivity
        ret[f"rock{rock_id}_specific_heat"] = rock.specific_heat
        if rock.nad >= 2:
            ret[f"rock{rock_id}_irp"] = str(rock.IRP)
            ret[f"rock{rock_id}_rp"] = rock.RP
            ret[f"rock{rock_id}_icp"] = str(rock.ICP)
            ret[f"rock{rock_id}_cp"] = rock.CP
        ret[f"rock{rock_id}_blockList"] = rock.blockList if len(rock.blockList) > 0 else ""
        ret[f"rock{rock_id}_formula_porosity"] = rock.formula_porosity
        ret[f"rock{rock_id}_formula_permeability"] = rock.formula_permeability
        ret[f"rock{rock_id}_rock_assign_condition"] = rock.rock_assign_condition
        ret[f"rock{rock_id}_region_length"] = len(rock.regionSecList)

        for reg_id, reg in enumerate(rock.regionSecList):
            logger.debug(reg.secName)
            ret[f"rock{rock_id}_reg{reg_id}_xmin"] = reg.xmin
            ret[f"rock{rock_id}_reg{reg_id}_ymin"] = reg.ymin
            ret[f"rock{rock_id}_reg{reg_id}_zmin"] = reg.zmin
            ret[f"rock{rock_id}_reg{reg_id}_xmax"] = reg.xmax
            ret[f"rock{rock_id}_reg{reg_id}_ymax"] = reg.ymax
            ret[f"rock{rock_id}_reg{reg_id}_zmax"] = reg.zmax
    
    return ret

def copy_visualized_mulgrid_imgs(inputIni: _readConfig.InputIni):
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    
    show_images = {}
    shutil.copy2(os.path.join(inputIni.t2FileDirFp, f"{IMG_LAYER_SURFACE}.png"),
                    create_fullpath("gui/static/output/"))
    show_images['layer'] = \
        {'path':f'output/{IMG_LAYER_SURFACE}.png',
         'caption':'IMG_LAYER_SURFACE'}
    
    show_images['slice'] = {}
    for l, line in enumerate(inputIni.plot.profile_lines_list):
        shutil.copy2(os.path.join(inputIni.t2FileDirFp, f"{IMG_PERM_SLICE_LINE}{l}.png"),
                        create_fullpath("gui/static/output/"))
        shutil.copy2(os.path.join(inputIni.t2FileDirFp, f"{IMG_RESIS_SLICE_LINE}{l}.png"),
                        create_fullpath("gui/static/output/"))
        show_images['slice'][f'{l}'] = \
            {'resis_path':f'output/{IMG_RESIS_SLICE_LINE}{l}.png',
             'perm_path':f'output/{IMG_PERM_SLICE_LINE}{l}.png',
             'caption':repr(line)}
        
    logger.info('imgs copied to gui/static/output/ : '+repr(show_images))
    
    return show_images


@app.route('/cmesh4_visualize', methods=['GET', 'POST'])
def cmesh4_visualize():
    # iniファイルを新規作成するとき
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    if request.method == 'POST':
        
        form = dict(request.form)
        
        # load inputIni pickled in cmesh3_check()
        with open(os.path.join(os.path.dirname(form['inputIniFp']), 
                               PICKLED_INPUTINI), 
                  'rb') as f:
            ini = pickle.load(f)  
        geo_topo = mulgrid(ini.mulgridFileFp)
        
        # load arrays pickled in makeGridAmeshVoro.makePermVariableVoronoiGrid()
        variable_perm = np.load(os.path.join(ini.savefigFp, PICKLED_MULGRID_PERM))
        variable_res = np.load(os.path.join(ini.savefigFp, PICKLED_MULGRID_RES))
        
        # overwrites ini.plot.slice_plot_limits
        if len(form['xmin'])>0 and len(form['xmax'])>0 \
                and len(form['zmin'])>0 and len(form['zmax'])>0 :
            ini.plot.slice_plot_limits = [[float(form['xmin']),float(form['xmax'])],
                                          [float(form['zmin']),float(form['zmax'])]]  
        else:
            form['xmin'],form['xmax'],form['zmin'],form['zmax'] = "", "", "", ""
            ini.plot.slice_plot_limits = None
        
        # overwrites ini.plot.profile_lines_list 
        ini.plot.profile_lines_list = []
        for line in ['line_0', 'line_1', 'line_2', 'line_3', 'line_4', 'line_5']:
            try:
                if len(request.form[line])>0:
                    if request.form[line].lower().strip() in ('x', 'y'):
                        ini.plot.profile_lines_list.append(request.form[line])
                        logger.debug(f"{line} {request.form[line]}: x or y")
                    elif isinstance(eval(request.form[line]),(list, np.ndarray)):
                        logger.debug(f"{line} {request.form[line]}:type np.ndarray")
                        ini.plot.profile_lines_list.append(np.array(eval(request.form[line])))
                    elif isinstance(eval(request.form[line]),(float,int)):
                        logger.debug(f"{line} {request.form[line]}: type float")
                        ini.plot.profile_lines_list.append(float(request.form[line]))
            except:
                logger.debug(f"{line} {request.form[line]}: eval error")
        
        # update input.ini
        ini.output2inifile(ini.inputIniFp)
        
        logger.debug(ini.plot.profile_lines_list)
        
        # create slices
        makeGridAmeshVoro.visualize(ini,geo_topo,variable_res,variable_perm, fex='png')
        # copy created slice images to static/output
        show_images = copy_visualized_mulgrid_imgs(ini)
        
        return render_template('cmesh4.html', 
                               form=form,
                               new_prob_fp=ini.t2FileDirFp, 
                               show_images=show_images,
                               inputIniFp=request.form['inputIniFp'])
    else:
        return redirect(url_for('index'))


@app.route('/cmesh5', methods=['GET', 'POST'])
def cmesh5():
    # iniファイルを新規作成するとき
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    if request.method == 'POST':
        
        logger.debug('call cmesh5_read_inputIni')
        try:
            form = cmesh5_read_inputIni(request)
        except FileNotFoundError:
            return redirect(url_for('index'))
        logger.debug('end cmesh5_read_inputIni')

        return render_template('cmesh5.html', form=form)
    else:
        return redirect(url_for('index'))

@app.route('/cmesh5_check', methods=['GET', 'POST'])
def cmesh5_check():
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    if request.method == 'POST':
        """validate"""
        msg_top_i, error_msg_incon = cmesh5_validate_incon(request)
        msg_top_g, error_msg_gener = cmesh5_validate_gener(request)
        
        form = dict(request.form)
        form = construct_simulator_paths(form)

        if request.form['usesAnotherResAsINCON'] == "1":
            # get path of SAVE file of 1d vertical simulation
            one_d_path = create_fullpath(request.form['1d_hydrostatic_sim_result_ini'])
            one_d_ini = _readConfig.InputIni().read_from_inifile(one_d_path)
            form['one_d_save'] = create_relpath(one_d_ini.saveFp)
        
        if len(error_msg_incon) > 0 or len(error_msg_gener) > 0:
            return render_template('cmesh5.html', 
                                   form=form, 
                                   error_msg={**msg_top_i, **msg_top_g}, # dictを結合
                                   error_msg_incon=error_msg_incon,
                                   error_msg_gener=error_msg_gener)
        

        """save"""
        #if validate OK, add params to inifile and save
        msg = cmesh5_write_file(request)

        if len(msg) > 0 :
            return render_template('cmesh5.html', form=form, error_msg=msg)

        outfp = os.path.join('output', request.form['problemName']+'.ini')
        return render_template('cmesh5.html', 
                                form=form,
                                downloadlink=outfp, 
                                error_msg=msg)

    else:
        return redirect(url_for('index'))

def cmesh5_validate_incon(request:request):
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    
    type = int(request.form["usesAnotherResAsINCON"])
    pnPR = request.form["problemNamePreviousRun"]
    onedsim = request.form["1d_hydrostatic_sim_result_ini"]
    cfr = request.form["cfr"]
    tcond = request.form["thermal_cond"]
    initial_t_grad = request.form["initial_t_grad"]
    
    """INCON"""
    # error message to be shown in just above section INCON
    msg = {}

    if type == 0:
        # use another simulation result as initial condition
        if len(pnPR)==0:
            msg['pnPR'] = \
                "Please specify Path of directory including SAVE file"
        elif not os.path.isdir(create_fullpath(pnPR)):
            msg['pnPR'] =\
                 f"result directory of previous run: {pnPR} is not found."
        elif not os.path.isfile(os.path.join(create_fullpath(pnPR),SAVE_FILE_NAME)):
            msg['pnPR'] =\
                 f"result file 'SAVE' was not found in: {pnPR}."


    elif type == 1:
        # create initial condition by assigning another 1D sim.
        if len(onedsim)==0:
            msg['onedsim'] = \
                "Please specify Path of input INI file of the 1D vertical simulation"
        elif not os.path.isfile(create_fullpath(onedsim)):
            msg['onedsim'] =\
                 f"input INI file of 1D simulation: {onedsim} is not found."

    elif type == 2:
        # create new initial condition (hydrostatic pressure & no advection)
        try:
            if math.isinf(float(initial_t_grad)) or math.isnan(float(initial_t_grad)):
                msg["initial_t_grad"] =\
                    f"conductive temperature gradient: {initial_t_grad} is invalid"
        except:
            msg["initial_t_grad"] =\
                f"conductive temperature gradient: {initial_t_grad} is invalid"

    # 一番上に表示するエラーメッセージ    
    msg_top = {}
    if len(msg) > 0:
        msg_top['incon'] = "Error in INCON setting"

    return msg_top, msg
    
def cmesh5_validate_gener(request:request):
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")

    """GENER"""
    # error message to be shown in just above section GENER
    msg = {}
    for i in range(int(request.form['gener_length'])):
        if not f'gener_{i}_isDisable' in request.form:
            if len(request.form[f'gener_{i}_injblock'])==0 :
                msg[f'gener_{i}_injblock'] = \
                    f"#{i} injblock is empty"
            if len(request.form[f'gener_{i}_flux'])==0 :
                msg[f'gener_{i}_flux'] = \
                    f"#{i} flux is empty"
            if len(request.form[f'gener_{i}_heat'])==0 :
                msg[f'gener_{i}_heat'] = \
                    f"#{i} heat is empty"
            if len(request.form[f'gener_{i}_heatUnit'])==0 :
                msg[f'gener_{i}_heatUnit'] = \
                    f"#{i} heatUnit is empty"
            if len(request.form[f'gener_{i}_injblock'])!=0 and \
                    len(request.form[f'gener_{i}_flux'])!=0 and \
                    len(eval(request.form[f'gener_{i}_injblock']))!=\
                        len(eval(request.form[f'gener_{i}_flux'])):
                msg[f"gener_{i}_config1"] = \
                    f"#{i} length of 'blocks' and 'flux' are not consistent"

    # 一番上に表示するエラーメッセージ    
    msg_top = {}
    if len(msg) > 0:
        msg_top['gener'] = "Error in GENER setting"

    return msg_top, msg

def construct_simulator_paths(form):
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    """ read path of simulator"""
    # path of simulators
    form['simulators'] = {}    
    if BIN_DIR is not None:
        form['simulators']['TOUGH3'] = BIN_DIR
    if BIN_DIR_LOCAL is not None:
        form['simulators']['TOUGH3_LOCAL'] = BIN_DIR_LOCAL
    if BIN_DIR_T2 is not None:
        form['simulators']['TOUGH2'] = BIN_DIR_T2
    if len(form['simulators'])==0:
        logger.error(f"please set path of simulator in define_path.py")
        raise FileNotFoundError
    logger.debug('simulators: ' + repr(form['simulators']))
    return form

    
def cmesh5_read_inputIni(request:request):
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    form = dict(request.form)
    iniFp = create_fullpath(request.form["inputIniFp"])
    logger.debug(f"check presence of file: {iniFp}")
    if not os.path.isfile(iniFp):
        logger.debug(f"ini file not found: {iniFp}")
        # return redirect(url_for('index')) # これはうまく動かない
        raise FileNotFoundError # 代わりに手動でエラーをraiseする。
    
    # parse ini file to config file
    logger.debug("parse ini file to config file")
    config = configparser.ConfigParser(defaults=None)
    config.read(iniFp)
    
    
    """ path of each simulators """
    form = construct_simulator_paths(form)
    
    """ read param values from config and substitute values to form """
    for sec, key, name in dict_gui.PARANAME_INI_GUI_CMESH5:
        try:
            form[name] = config[sec][key]
            logger.debug(f"[{sec}]{key}: {form[name]}")
        except:
            logger.debug(f"[{sec}]{key} not found")
    
    """ construct paths """
    if config.has_option('configuration', 'TOUGH_INPUT_DIR'):
        TOUGH_INPUT_DIR = config['configuration']['TOUGH_INPUT_DIR']
    elif config.has_option('configuration', 'configini'):
        setting = _readConfig.SettingIni(config['configuration']['configini'])
        TOUGH_INPUT_DIR = setting.toughConfig.TOUGH_INPUT_DIR
    else:
        logger.error(f"Please specify configutation.TOUGH_INPUT_DIR in '{iniFp}'")
        raise InvalidToughInputException(f"Please specify configutation.TOUGH_INPUT_DIR in '{iniFp}'")

    form['inputIniFp'] = iniFp
    form['saveDirRel'] = create_relpath(TOUGH_INPUT_DIR)
    form['saveDirFull'] = create_fullpath(TOUGH_INPUT_DIR)
    if config.has_option('mesh', 'mulgridFileFp'):
        form['mulgridFileFpRel'] = create_relpath(config['mesh']['mulgridFileFp'])
        form['mulgridFileFpFull'] = create_fullpath(config['mesh']['mulgridFileFp'])
    elif config.has_option('toughInput', 'mulgridFileName'):
        form['mulgridFileFpRel'] = os.path.join(
                                    setting.toughConfig.GRID_DIR, 
                                    config['toughInput']['mulgridFileName'])
        form['mulgridFileFpFull'] = create_fullpath(form['mulgridFileFpRel'])

   
    """parse MOPsXX"""
    for mop in ('mops02','mops03','mops04','mops05','mops06'):
        if config.has_option('toughInput', mop) and len(config['toughInput'][mop])>0:
            logger.debug(f"parse {mop}: {config['toughInput'][mop]}")
            if int(config['toughInput'][mop])>0 :
                form[mop] = "uses" 
            else:
                form[mop] = "0"

    if config.has_option('toughInput', 'mops18') and len(config['toughInput']['mops18'])>0:
        if int(config['toughInput']['mops18'])>0 :
            form['mops18'] = "9"
        else:
            form['mops18'] = "0"

    
    if config.has_option('toughInput', 'mops16') and len(config['toughInput']['mops16'])>0:
        if int(config['toughInput']['mops16']) <= 1:
            form['mops16'] = config['toughInput']['mops16']
        elif int(config['toughInput']['mops16']) > 1:
            form['mops16'] = "2"
            form['mops16_1'] = config['toughInput']['mops16']
        else:
            form['mops16'] = ""
    
    """parse SELEC.1, SELEC.2 (eco2n_v2)"""
    if config.has_option('toughInput', 'selection_line1') \
                and len(config['toughInput']['selection_line1'])>0:
        selec = eval(config['toughInput']['selection_line1'])
        for i, s in enumerate(selec):
            form[f'IE{i+1}'] = repr(s) if s is not None else ""
    if config.has_option('toughInput', 'selection_line2') \
                and len(config['toughInput']['selection_line2'])>0:
        selec = eval(config['toughInput']['selection_line2'])
        for i, s in enumerate(selec):
            form[f'FE{i+1}'] = repr(s) if s is not None else ""


    """FOFT/COFT"""
    if config.has_option('toughInput', 'prints_hc_surface') \
                and len(config['toughInput']['prints_hc_surface'])>0:
        form['prints_hc_surface'] = "uses" \
            if eval(config['toughInput']['prints_hc_surface']) else ""

    """parse INCON section"""
    if  config.has_option('toughInput', 'problemNamePreviousRun') \
                and len(config['toughInput']['problemNamePreviousRun']) > 0:
        form["usesAnotherResAsINCON"] = "0"
    elif config.has_option('toughInput', '1d_hydrostatic_sim_result_ini') \
                and len(config['toughInput']['1d_hydrostatic_sim_result_ini']) > 0:
        form["usesAnotherResAsINCON"] = "1"
    elif config.has_option('toughInput', 'initial_t_grad') \
                and len(config['toughInput']['initial_t_grad']) > 0:
        form["usesAnotherResAsINCON"] = "2"

    """parse GENER section"""
    if  config.has_option('toughInput', 'generSecList') \
                and len(config['toughInput']['generSecList']) > 0:
        generSecs = eval(config['toughInput']['generSecList'])
        form['gener_length'] = len(generSecs)
        for i in range(len(generSecs)):
            form[f"gener_{i}_isDisable"] = ""
            form[f"gener_{i}_type_eos2"] = config[generSecs[i]]['type']
            form[f"gener_{i}_type_eco2n"] = config[generSecs[i]]['type']
            form[f"gener_{i}_injblock"] = config[generSecs[i]]['block']
            form[f"gener_{i}_flux"] = repr(eval(config[generSecs[i]]['flux']))
            form[f"gener_{i}_heat"] = config[generSecs[i]]['temperature']
            form[f"gener_{i}_heatUnit"] = "tempc"

    return form


def cmesh5_write_file(request:request):
    """
    input.iniを画面で入力された値に書き換えて、static/output以下に出力する。
    最後にチェックを兼ねてInputIniオブジェクトに変換を試みる

    1. convert request.form to dict obj. 
    2. edit the dict obj.
    3. convert the dict obj. to config obj. 
    4. output as new ini file
    5. convert to InputIni obj.
    """
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    
    msg_dict = {}
    form = dict(request.form)

    # check existence of iniFp
    if not os.path.isfile(form['inputIniFp']):
        msg_dict['inifp_not_found'] = f"{form['inputIniFp']} not found"
        return msg_dict
    
    """
    入力値を整理して適切な値をformにセットする
    """
    # mops2-6
    for mop in ('mops02','mops03','mops04','mops05','mops06'):
            form[mop] = "1" if mop in form else "0"
    
    # prints_hc_surface
    form['prints_hc_surface'] = repr('prints_hc_surface' in form)
        

    # INCON
    type = int(request.form["usesAnotherResAsINCON"])    
    if type == 0:
        # use another simulation result as initial condition
        form["1d_hydrostatic_sim_result_ini"] = ""
        form["initial_t_grad"] = ""
    elif type == 1:
        # create initial condition by assigning another 1D sim.
        form["problemNamePreviousRun"] = ""
        form["initial_t_grad"] = ""
    elif type == 2:
        # create new initial condition (hydrostatic pressure & no advection)
        form["problemNamePreviousRun"] = ""
        form["1d_hydrostatic_sim_result_ini"] = ""
    
    # GENER 
    idx = 0
    tmp = []
    for i in range(int(form['gener_length'])):
        if not f'gener_{i}_isDisable' in form:
            tmp.append(f'gener{idx}')
            idx += 1
    form['generSecList'] = repr(tmp)

        
    """
    formの値をconfigオブジェクトに追記する
    """
    logger.info(f"add params to *.ini file:{create_relpath(form['inputIniFp'])}")

    config = configparser.ConfigParser(defaults=None)
    config.read(form['inputIniFp'])
    for sec, key, name in dict_gui.PARANAME_INI_GUI_CMESH5:
        if config.has_option(sec,key):
            info = f"[{sec:<15}] {key:<25}: {config[sec][key]} "
        else:
            info = f"[{sec:<15}] {key:<25}: (not found)         "
        if name in form:
            logger.debug(info + f"--> {form[name]}")
            config.set(sec, key, form[name])
        else:
            logger.debug(info + f"--> ")
            config.set(sec, key, "")

    # mops16
    config.set('toughInput', 'mops16', form['mops16_1'])

    # configuration
    if config.has_option('configuration', 'configIni'):
        config.remove_option('configuration', 'configIni')
    config.set('configuration', 'TOUGH_INPUT_DIR', create_relpath(form['saveDirRel']))
        
    # GENER 
    idx = 0
    for i in range(int(form['gener_length'])):
        if not f'gener_{i}_isDisable' in form:
            
            # add new section
            sec = f'gener{idx}'
            if config.has_section(sec):
                config.remove_section(sec)
                logger.info(f'overwrite GENER section: {sec}')
            config.add_section(sec)   

            # 'name' and 'type'
            if ECO2N in form['module']:
                if 'WATE' in form[f'gener_{i}_type_'+ECO2N]:
                    config.set(sec, 'name', f'WAT{idx:>2}')
                else:
                    config.set(sec, 'name', 'CM'+form[f'gener_{i}_type_'+ECO2N][-1]+f'{idx:>2}')
                config.set(sec, 'type', form[f'gener_{i}_type_'+ECO2N])
            if EOS2 in form['module']:
                if 'WATE' in form[f'gener_{i}_type_'+EOS2]:
                    config.set(sec, 'name', f'WAT{idx:>2}')
                else:
                    config.set(sec, 'name', 'CM'+form[f'gener_{i}_type_'+EOS2][-1]+f'{idx:>2}')
                config.set(sec, 'type', form[f'gener_{i}_type_'+EOS2])
            
            # the others
            config.set(sec, 'block', form[f'gener_{i}_injblock'])
            config.set(sec, 'flux', form[f'gener_{i}_flux'])
            if form[f'gener_{i}_heatUnit']=='tempc':
                config.set(sec, 'temperature', form[f'gener_{i}_heat'])
            elif True:
                #TODO J/g, kJ/g なども実装する
                pass
            config.set(sec, 'injectsIndirectly', "False")
            # TODO injectsIndirectly is Trueに対応

            idx += 1
    
    # SELEC.1
    line1 = []
    for i in range(1,17):
        if f'IE{i}' in form and len(form[f'IE{i}'])>0:
            line1.append(int(form[f'IE{i}']))
        else:
            line1.append(None)
    config['toughInput']['selection_line1'] = repr(line1)
    logger.debug('selection_line1: ' + repr(line1))
    # SELEC.2
    line2 = []
    for i in range(1,17):
        if f'FE{i}' in form and len(form[f'FE{i}'])>0:
            line2.append(float(form[f'FE{i}']))
        else:
            line2.append(None)
    config['toughInput']['selection_line2'] = repr(line2)
    logger.debug('selection_line2: ' + repr(line2))

    # 書き出し1
    outfp = os.path.join(pathlib.Path(__file__).parent.resolve(),
                         'static/output', 
                         form['problemName']+'.ini')
    if os.path.isfile(outfp): os.remove(outfp)
    with open(outfp, 'w') as f:
        config.write(f)
    
    # エラーチェックを兼ねて、inputIniに読み込ませる
    ini = _readConfig.InputIni().read_from_inifile(outfp)
    ini.rocktypeDuplicateCheck()
    
    return msg_dict


@app.route('/test_create', methods=['GET', 'POST'])
def test_create():
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    
    if request.method == 'POST':
        createdFp = os.path.join(pathlib.Path(__file__).parent.resolve(),
                    'static', 
                    request.form['createdIniFp'])
        ini = _readConfig.InputIni().read_from_inifile(createdFp)
        ini.rocktypeDuplicateCheck()
        
        error_msg = {}
        short_msg = ""
        os.makedirs(ini.t2FileDirFp, exist_ok=True)
        if not os.path.isfile(ini.t2FileFp):
            if not os.path.isfile(ini.t2GridFp):
                makeGridAmeshVoro.makePermVariableVoronoiGrid(ini)
            tough3exec_ws.makeToughInput(ini)
            short_msg = f"TOUGH inputs created in {ini.t2FileDirFp}"
        else:
            error_msg['prob_exists'] = f"Problem: {create_relpath(ini.t2FileDirFp)}. Please specify different problem name and press (check)."
        
        # return to cmesh5.html     
        form = dict(request.form)
        form = construct_simulator_paths(form)
        outfp = os.path.join('output', request.form['problemName']+'.ini')
        return render_template('cmesh5.html', form=form, downloadlink=outfp, 
                                error_msg=error_msg if len(error_msg)>0 else None,
                                short_msg=short_msg
                                )

    else:
        return redirect(url_for('index'))

app.run(port=8000, debug=True)  