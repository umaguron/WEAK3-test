# from distutils.log import error
import glob
import os
import re 
import sys
import pathlib
import time
import datetime

# from unittest import result
baseDir = pathlib.Path(__file__).parent.resolve()
sys.path.append(baseDir)
sys.path.append(os.path.join(baseDir,".."))
sys.path.append(os.path.join(baseDir,"../femticUtil"))
projRoot = os.path.abspath(os.path.join(baseDir,".."))
from import_pytough_modules import *
import _readConfig
import makeGridAmeshVoro
import makeGridFunc
import tough3exec_ws
import run
from flask import Flask
from flask import render_template
from flask import Markup
from flask import request
from flask import flash
from flask import make_response
from flask import jsonify
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
from werkzeug.utils import secure_filename
import readFemticResistivityModel as rFRM
from threading import Thread
import pandas as pd
import seed_to_voronoi
import matplotlib
'Matplotlib is not thread-safe:...'
# https://matplotlib.org/stable/users/faq.html#work-with-threads
matplotlib.use('Agg') # これがないとAssertion failed:で落ちることがある
               

app = Flask(__name__, static_folder='static', static_url_path='')


UPLOAD_FOLDER = os.path.join(projRoot,'gui/static/uploaded')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# TOUGH3 run by api
IS_RUNNING_TOUGH3 = False
# list of {'thread': (threading.Thread), 'inifp': (str)}
THREADS_TOUGH_RUNNING = []

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

@app.route('/makeVoroSeedsList2')
def makeVoroSeedsList2():
    return app.send_static_file('makeVoroSeedsList2.html')

@app.route('/femtic')
def femtic():
    return render_template('femtic.html', form=request.form)

@app.route('/femtic_check', methods=['GET', 'POST'])
def femtic_check():
    print(baseDir)
    if request.method == 'POST':
        # save to app.config['UPLOAD_FOLDER']
        resistivityBlockIterDat = request.files['ResistivityBlockIterDat']
        if resistivityBlockIterDat.filename == '':
            flash('No selected file')
            return redirect(request.url)
        resFp = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(resistivityBlockIterDat.filename))
        resistivityBlockIterDat.save(resFp)
        # save to app.config['UPLOAD_FOLDER']
        meshDat = request.files['MeshDat']
        if meshDat.filename == '':
            flash('No selected file')
            return redirect(request.url)       
        meshFp = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(meshDat.filename))
        meshDat.save(meshFp)
        # call methods in readFemticResistivityModel
        db = rFRM.DB_CellElementNodeRelation(meshFp, resFp, rFRM.FP_DATABASE)
        db.restore()
        outputFp = os.path.join(projRoot, 'gui/static/output/cellCenterResistivity.txt')
        db.outputAsXYZRho(outputFp, 
                          resistivity_threshold=float(request.form['resistivity_threshold']))
        # clean
        os.remove(resFp)
        os.remove(meshFp)
        return """
        <a href="static/output/cellCenterResistivity.txt" download>download</a>
        """
        
    else:
        return redirect(url_for('femtic'))
    return render_template('femtic.html', form=request.form)
    
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
    return render_template('cmesh2.html', form=request.form, created=False, projRoot=projRoot)
    # if request.method == 'POST':
    #     return render_template('cmesh2.html', form=request.form, created=False)
    # else:
    #     return redirect(url_for('index'))

@app.route('/cmesh2_check', methods=['GET', 'POST'])
def cmesh2_check():
    if request.method == 'POST':
        error_msg = {}
        """check problem directory firstly"""
        if os.path.isdir(create_fullpath(request.form['saveDir'])) and int(request.form['createsMesh'])==1:
            # case "create new mesh" && base directory exists
            error_msg['s_dir'] = f"Directory \"{create_fullpath(request.form['saveDir'])}\" already exists"
        
        tmp = dict(request.form)
        tmp['saveDir'] = create_relpath(request.form['saveDir'])

        if len(error_msg) > 0:
            return render_template('cmesh2.html', error_msg=error_msg, form=tmp,  projRoot=projRoot)

        save_dir_fp = create_fullpath(request.form['saveDir'])
        # check saveDir 
        if os.path.isfile(save_dir_fp):
            error_msg["prob_dir_isfile"] = f"Problem directory: {save_dir_fp} is exists and is file. Provide the different file path."

        # if No error, then check mesh
        if int(request.form['createsMesh'])==1:
            """ create new mesh """
            voronoi_seeds_list_fp_org = create_fullpath(request.form['voronoi_seeds_list_fp'])
            topodata_fp_org = create_fullpath(request.form['topodata_fp'])
            mulgridFile_fp_new = os.path.join(save_dir_fp, request.form['mulgridFileName'])
            voronoi_seeds_list_fp_new = os.path.join(save_dir_fp, "seed.txt")
            topodata_fp_link = os.path.join(save_dir_fp, os.path.basename(request.form['topodata_fp']))

            """validation"""
            if not os.path.isfile(topodata_fp_org):
                error_msg["topodata_fp"] = f"topodata_fp: {topodata_fp_org}   does not exist. Provide the correct file path."
            if not os.path.isfile(voronoi_seeds_list_fp_org):
                error_msg["voronoi_seeds_list_fp"] = f"voronoi_seeds_list_fp: {voronoi_seeds_list_fp_org}   does not exist. Provide the correct file path."
            if os.path.isdir(mulgridFile_fp_new):
                error_msg["mulgridFile_fp_dir"] = f"{mulgridFile_fp_new} is directory. Please specify different file path."
            elif os.path.isfile(mulgridFile_fp_new):
                error_msg["mulgridFile_fp"] = f"mulgridFile_fp: {mulgridFile_fp_new}  already exist. Please specify different file path."
            
            try:
                _ = eval(request.form['layer_thicknesses'])
                if not isinstance(_, (tuple, list, np.ndarray)):
                    error_msg["layer_thicknesses"] = f"'layer_thicknesses' must be 'list', 'tuple', or 'numpy.ndarray'."
            except:
                error_msg["layer_thicknesses"] = f"error in 'layer_thicknesses': Can not interpret '{request.form['layer_thicknesses']}'."

            if len(error_msg) > 0:
                return render_template('cmesh2.html', error_msg=error_msg, form=request.form, created=False, projRoot=projRoot)

            """ _readConfig.InputIniインスタンス作成"""
            inputIni = _readConfig.InputIni()
            inputIni.toughInput = {}
            inputIni.mesh.type = AMESH_VORONOI
            inputIni.mulgridFileFp = mulgridFile_fp_new
            inputIni.mesh.convention = int(request.form['convention'])
            inputIni.atmosphere.includesAtmos = eval(request.form['includesAtmos'])
            # 入力値はdict化してからconfigparser.ConfigParserオブジェクトに変換し、read_from_configにわたす
            config = {}
            config['amesh_voronoi'] = dict(request.form)
            parser = configparser.ConfigParser()
            parser.read_dict(config)
            inputIni.amesh_voronoi = _readConfig.InputIni._AmeshVoronoi().read_from_config(parser)
            inputIni.amesh_voronoi.uses_amesh = eval(request.form['uses_amesh'])
            inputIni.amesh_voronoi.topodata_fp = create_relpath(topodata_fp_org)
            inputIni.amesh_voronoi.voronoi_seeds_list_fp = create_relpath(voronoi_seeds_list_fp_org)

            # create problemDir before generation
            msg = {}
            if not os.path.isdir(save_dir_fp):
                msg['dir'] = f"Directory: {save_dir_fp}  newly created"
            os.makedirs(save_dir_fp, exist_ok=True)

            # create mesh file
            makeGridAmeshVoro.create_mulgrid_with_topo(inputIni)

            # if succeeded, create link and copy in saveDir 
            if Const.DUPLICATES_ORG_TOPO:
                os.symlink(inputIni.amesh_voronoi.topodata_fp, topodata_fp_link)
            if Const.DUPLICATES_ORG_SEEDS:
                shutil.copy(inputIni.amesh_voronoi.voronoi_seeds_list_fp, 
                            voronoi_seeds_list_fp_new)

            #メモを残す
            with open(os.path.join(save_dir_fp, "cmesh2_memo.txt"), 'a') as f:
                f.write(f"\n--- {datetime.datetime.now()} ---\n")
                f.write(f"mulgrid file was newly created by cmesh2 (create new mulgrid file).\n")
                f.write(f"constants.DUPLICATES_ORG_SEEDS: {Const.DUPLICATES_ORG_SEEDS}\n")
                if Const.DUPLICATES_ORG_SEEDS:
                    f.write(f"Original 'voronoi_seeds_list_fp': {voronoi_seeds_list_fp_org}\n")
                f.write(f"constants.DUPLICATES_ORG_TOPO: {Const.DUPLICATES_ORG_TOPO}\n")
                if Const.DUPLICATES_ORG_TOPO:
                    f.write(f"Original 'topodata_fp': {Const.DUPLICATES_ORG_TOPO}\n")

            # form のファイルパスを書き換える
            tmp = dict(request.form)
            tmp['mulgridFileFp'] = create_relpath(mulgridFile_fp_new)
            if Const.DUPLICATES_ORG_TOPO:
                tmp['topodata_fp'] = create_relpath(topodata_fp_link)
            else:
                tmp['topodata_fp'] = create_relpath(topodata_fp_org)
            if Const.DUPLICATES_ORG_SEEDS:
                tmp['voronoi_seeds_list_fp'] = create_relpath(voronoi_seeds_list_fp_new)
            else:
                tmp['voronoi_seeds_list_fp'] = create_relpath(voronoi_seeds_list_fp_org)

            msg['mul'] = "mulgrid file successfully created"
                
            # ラジオボタンcreatesMeshを"Use existing mulgrid file"に切り替える
            return render_template('cmesh2.html', form=tmp, created = True,  msg=msg, projRoot=projRoot)


        elif int(request.form['createsMesh'])==0:
            """ use existing mesh """
            # check file existence
            mulgridFileFp = create_fullpath(request.form['mulgridFileFp'])
            mulgridFile_fp_copied = os.path.join(save_dir_fp, 
                                               os.path.basename(mulgridFileFp))
            if not os.path.isfile(mulgridFileFp):
                error_msg["mulgridFile_fp"] = f"File: {mulgridFileFp}  was not found. Please specify correct file path."
            if len(error_msg) > 0:
                return render_template('cmesh2.html', error_msg=error_msg, form=request.form, created=False, projRoot=projRoot)
            
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
                tmp.pop('mulgridFileName')
            except:
                # 握りつぶす
                pass
            
            # create problemDir before generation
            msg = {}
            if not os.path.isdir(save_dir_fp):
                msg['dir'] = f"Directory: {save_dir_fp}  newly created"
            os.makedirs(save_dir_fp, exist_ok=True)
            
            # create link in saveDir 
            if Const.DUPLICATES_ORG_MULGRID:
                if os.path.abspath(mulgridFileFp) != os.path.abspath(mulgridFile_fp_copied):
                    shutil.copy(mulgridFileFp, mulgridFile_fp_copied)
                    msg['mul'] = f"A copy of mulgrid file {create_relpath(mulgridFileFp)} was created in {save_dir_fp}"
                # form のファイルパスを書き換える
                tmp['mulgridFileFp'] = create_relpath(mulgridFile_fp_copied)
            else:
                tmp['mulgridFileFp'] = create_relpath(mulgridFileFp)
            
            #メモを残す
            with open(os.path.join(save_dir_fp, "cmesh2_memo.txt"), 'a') as f:
                f.write(f"\n--- {datetime.datetime.now()} ---\n")
                f.write(f"cmesh2 (use existing mulgrid file).\n")
                f.write(f"constants.DUPLICATES_ORG_MULGRID: {Const.DUPLICATES_ORG_MULGRID}\n")
                if Const.DUPLICATES_ORG_MULGRID:
                    f.write(f"mulgrid file was copied from: {mulgridFileFp}\n")
                else:
                    f.write(f"mulgrid file: {mulgridFileFp}\n")

            # read atmosphere_type from mulgrid and set to form
            tmp['includesAtmos'] = mulgrid(mulgridFileFp).atmosphere_type==0

            print(tmp)

            # int(request.form['createsMesh'])==1でcreatedのときと同じ扱い
            return render_template('cmesh2.html', form=tmp, created = True, msg=msg, projRoot=projRoot)
    else:
        return redirect(url_for('index'))

@app.route('/cmesh3', methods=['GET', 'POST'])
def cmesh3():
    if request.method == 'POST':
        return render_template('cmesh3.html', form=request.form, projRoot=projRoot)
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
    newIni = os.path.join(request.form['saveDir'], f'input_cmesh4_{request.form["problemName"]}.ini')
    if os.path.isfile(newIni)\
            and not 'overwrites_prob' in request.form:
        error_msg['problemName']= \
            f"The .ini file to which we are trying to export the entered information: "\
            f"'{newIni}'  already exists.\n"\
            f"If you want to proceed anyway, check the 'Force overwrite' checkbox." 

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
            return render_template('cmesh3.html', form=request.form, error_msg=error_msg, projRoot=projRoot)
        
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
            # 入力値はdict化してからconfigparser.ConfigParserオブジェクトに変換し、read_from_configにわたす
            config_av = {}
            config_av['amesh_voronoi'] = dict(request.form)
            parser = configparser.ConfigParser()
            parser.read_dict(config)
            inputIni.amesh_voronoi = _readConfig.InputIni._AmeshVoronoi().read_from_config(parser)
            inputIni.mesh.convention = int(request.form['convention'])
            # inputIni.atmosphere.includesAtmos = eval(request.form['includesAtmos'])
        else: 
            # detect mesh convention
            geo = mulgrid(inputIni.mesh.mulgridFileFp)
            inputIni.mesh.convention = geo.convention
        
        """problem dir."""
        config['configuration'] = {}
        config['configuration']['TOUGH_INPUT_DIR'] = create_relpath(request.form['saveDir'])
        # configparser.ConfigParserオブジェクトに変換してからread_from_configにわたす
        parser = configparser.ConfigParser()
        parser.read_dict(config)
        inputIni.configuration = _readConfig.InputIni._Configuration().read_from_config(parser)
        """problem name"""
        inputIni.toughInput['problemName'] = request.form[f'problemName']
        """resistivity_structure_fp"""
        if Const.DUPLICATES_ORG_RESMODEL:
            inputIni.mesh.resistivity_structure_fp = create_relpath(os.path.join(request.form[f'saveDir'], os.path.basename(request.form[f'resistivity_structure_fp'])))
            os.symlink(create_fullpath(request.form[f'resistivity_structure_fp']), create_fullpath(inputIni.mesh.resistivity_structure_fp))
        else:
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
        # 空気層の設定の中で唯一cmesh3で設定されない項目。元iniファイルに設定がある場合は引き継ぐようにする。
        try:
            config['atmosphere']['PRIMARY_AIR'] = repr(inputIni.atmosphere.PRIMARY_AIR)
        except:
            # 仮 (cmesh5で設定する)
            config['atmosphere']['PRIMARY_AIR'] = '[]' 
        # cmesh3の処理に追加しようと思ったがやめた。現段階ではP,Tの設定をcmesh3ではしない。
        # config['atmosphere']['primary_tmp_pres'] = request.form[f'primary_tmp_pres']
        # config['atmosphere']['primary_tmp_temp'] = request.form[f'primary_tmp_temp']
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
        # configparser.ConfigParserオブジェクトに変換してからread_from_configにわたす
        parser = configparser.ConfigParser()
        parser.read_dict(config)
        inputIni.atmosphere = _readConfig.InputIni._Atmosphere().read_from_config(parser)

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

                # configparser.ConfigParserオブジェクトに変換
                parser = configparser.ConfigParser()
                parser.read_dict(config)

                if not 'rockSecList' in inputIni.toughInput:
                    inputIni.toughInput['rockSecList'] = [name]
                    inputIni.rockSecList = [_readConfig.InputIni._RocktypeSec(name, parser)]
                else:
                    inputIni.toughInput['rockSecList'].append(name)
                    inputIni.rockSecList.append(_readConfig.InputIni._RocktypeSec(name, parser))
        
        """check & create"""
        inputIni.rocktypeDuplicateCheck()
        # create save dir. 
        os.makedirs(inputIni.t2FileDirFp, exist_ok=True)

        inputIni.inputIniFp = os.path.join(projRoot, 
                                           inputIni.configuration.TOUGH_INPUT_DIR, 
                                           f"input_cmesh4_{inputIni.toughInput['problemName']}.ini")
        inputIni.output2inifile(inputIni.inputIniFp)
        
        # pickle for cmesh4_visualize()
        # 不完全なファイルの場合_readConfig.InputIni().read_from_inifile()では読み込めないため。
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

        return render_template('cmesh3.html', form=form, projRoot=projRoot)
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
    ret["saveDir"] = create_relpath(ini.configuration.TOUGH_INPUT_DIR)
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

    # cmesh3で表示しようかと思ったがやめる。かわりにcmesh5のprimary variablesで設定する。
    # if 'module' in ini.toughInput \
    #         and hasattr(ini.atmosphere, 'PRIMARY_AIR') \
    #         and len(ini.atmosphere.PRIMARY_AIR)>0:
    #     if EOS2 == ini.toughInput['module'].lower().strip():
    #         ret["primary_tmp_pres"] =  ini.atmosphere.PRIMARY_AIR[INCON_ID_EOS2_PRES]
    #         ret["primary_tmp_temp"] =  ini.atmosphere.PRIMARY_AIR[INCON_ID_EOS2_TEMP]
    #     elif ECO2N in ini.toughInput['module'].lower().strip():
    #         ret["primary_tmp_pres"] =  ini.atmosphere.PRIMARY_AIR[INCON_ID_ECO2N_PRES]
    #         ret["primary_tmp_temp"] =  ini.atmosphere.PRIMARY_AIR[INCON_ID_ECO2N_TEMP]
    # else:
    #     ret["primary_tmp_pres"] = ""
    #     ret["primary_tmp_temp"] = ""


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

def copy_visualized_mulgrid_imgs(inputIni: _readConfig.InputIni, layers: list=[]):
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    
    timestamp = time.time()
    
    show_images = {}
    shutil.copy2(os.path.join(inputIni.t2FileDirFp, f"{IMG_LAYER_SURFACE}.png"),
                    create_fullpath(f"gui/static/output/{IMG_LAYER_SURFACE}_{timestamp}.png"))
    show_images['layer_surface'] = \
        {'path':f'static/output/{IMG_LAYER_SURFACE}_{timestamp}.png',
         'caption':'IMG_LAYER_SURFACE'}
    
    show_images['slice_vertical'] = {}
    for l, line in enumerate(inputIni.plot.profile_lines_list):
        shutil.copy2(os.path.join(inputIni.t2FileDirFp, f"{IMG_PERM_SLICE_LINE}{l}.png"),
                        create_fullpath(f"gui/static/output/{IMG_PERM_SLICE_LINE}{l}_{timestamp}.png"))
        shutil.copy2(os.path.join(inputIni.t2FileDirFp, f"{IMG_RESIS_SLICE_LINE}{l}.png"),
                        create_fullpath(f"gui/static/output/{IMG_RESIS_SLICE_LINE}{l}_{timestamp}.png"))
        show_images['slice_vertical'][f'{l}'] = \
            {'resis_path':f'static/output/{IMG_RESIS_SLICE_LINE}{l}_{timestamp}.png',
             'perm_path':f'static/output/{IMG_PERM_SLICE_LINE}{l}_{timestamp}.png',
             'caption':repr(line)}
 
    show_images['slice_horizontal'] = {}
    for layer in layers:
        
        orginal_perm = os.path.join(inputIni.t2FileDirFp, f"{IMG_PERM_LAYER}{layer.replace(' ','_')}.png")
        copied_perm = create_fullpath(f"gui/static/output/{IMG_PERM_LAYER}{layer.replace(' ','_')}_{timestamp}.png")
        if os.path.isfile(orginal_perm):
            shutil.copy2(orginal_perm, copied_perm)

        orginal_res = os.path.join(inputIni.t2FileDirFp, f"{IMG_RESIS_LAYER}{layer.replace(' ','_')}.png")
        copied_res = create_fullpath(f"gui/static/output/{IMG_RESIS_LAYER}{layer.replace(' ','_')}_{timestamp}.png")
        print(orginal_res)
        if os.path.isfile(orginal_res):
            shutil.copy2(orginal_res, copied_res)
        
        show_images['slice_horizontal'][f'{layer}'] = \
            {'resis_path':f'static/output/{IMG_RESIS_LAYER}{layer.replace(" ", "_")}_{timestamp}.png',
             'perm_path':f'static/output/{IMG_PERM_LAYER}{layer.replace(" ", "_")}_{timestamp}.png',
             'caption':repr(layer)}

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
        
        # create vertical slices
        makeGridAmeshVoro.visualize_vslice(ini,geo_topo,variable_res,variable_perm,fex='png')
        
        # create horizontal slices
        try:
            tmp = eval(form['horizontal']) 
            if isinstance(tmp, list):
                layers = tmp
            else:
                layers = []
        except:
            layers = []

        for layer in layers:
            makeGridAmeshVoro.visualize_layer(ini,geo_topo,variable_res,variable_perm,
                                            layer_no_to_plot=layer, fex='png')
            makeGridAmeshVoro.visualize_layer(ini,geo_topo,variable_res,variable_perm,
                                            layer_no_to_plot=layer, fex='pdf')

        # copy created slice images to static/output
        show_images = copy_visualized_mulgrid_imgs(ini, layers=layers)
        
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

        return render_template('cmesh5.html', form=form, projRoot=projRoot)
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
                                   error_msg_gener=error_msg_gener,
                                   projRoot=projRoot)
        

        """save"""
        #if validate OK, add params to inifile and save
        logger.debug("into cmesh5_write_file")
        msg, outfp, outfp_inT2dir = cmesh5_write_file(request)
        logger.debug("out cmesh5_write_file")

        # set the path of created ini-format file for showing green message
        form['ini_outfp_rel'] = create_relpath(outfp_inT2dir)
        form['ini_outfp_full'] = create_fullpath(outfp_inT2dir)

        if len(msg) > 0 :
            return render_template('cmesh5.html', form=form, error_msg=msg, projRoot=projRoot)

        return render_template('cmesh5.html', 
                                form=form,
                                downloadlink=outfp, 
                                error_msg=msg,
                                projRoot=projRoot)

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
    form['inputIniFpRel'] = create_relpath(iniFp) 
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

    """parse PRIMARY variables"""
    try:
        pa = eval(config['atmosphere']['PRIMARY_AIR'])
        for i, p in enumerate(pa):
            form[f'primary_atm_{i+1}'] = "" if p is None else p
    except:
        logger.warning("cannot read [atmosphere] PRIMARY_AIR")
    try:
        pd = eval(config['toughInput']['PRIMARY_default'])
        for i, p in enumerate(pd):
            form[f'primary_def_{i+1}'] = "" if p is None else p
    except:
        logger.warning("cannot read [toughInput] PRIMARY_default")
                
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
            # cmesh5入力値がある場合
            if config.has_section(sec):
                # 元ファイルにセクションがあるとき、値を更新
                logger.debug(info + f"--> {form[name]}")
                config.set(sec, key, form[name])
            else:
                # 元ファイルにセクションがないとき、何もしない
                logger.debug(info + f"--> ")
        else:
            # cmesh5入力値がない場合
            if config.has_section(sec):
                # 元ファイルにセクションがあるとき、値を更新(空白に置き換え)
                logger.debug(info + f"--> ")
                config.set(sec, key, "")
            else:
                print(sec)
                # 元ファイルにセクションがないとき、何もしない
                logger.debug(info + f"--> ")

    # mops16
    config.set('toughInput', 'mops16', form['mops16_1'])

    # configuration
    if config.has_option('configuration', 'configIni'):
        config.remove_option('configuration', 'configIni')
    config.set('configuration', 'TOUGH_INPUT_DIR', create_relpath(form['saveDirRel']))

    # primary variables
    pr_len = 0
    if form['module']==EOS2:
        pr_len = 3
    elif ECO2N in form['module']:
        pr_len = 4
    pd = [None for _ in range(pr_len)]
    pa = [None for _ in range(pr_len)]
    for i in range(pr_len):
        if f'primary_def_{i+1}' in form:
            pd[i] = float(form[f'primary_def_{i+1}'])
        if f'primary_atm_{i+1}' in form:
            pa[i] = float(form[f'primary_atm_{i+1}'])
    config.set('toughInput', 'PRIMARY_default', repr(pd))
    if not config.has_section('atmosphere'): config.add_section('atmosphere')
    config.set('atmosphere', 'PRIMARY_AIR', repr(pa))

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
                         f'input_final_{config["toughInput"]["problemName"]}.ini')
    if os.path.isfile(outfp): os.remove(outfp)
    with open(outfp, 'w') as f:
        config.write(f)
    logger.debug(f"File saved: {outfp}")
    
    # エラーチェックを兼ねて、inputIniに読み込ませる
    logger.debug(f"-------------- test for reading Ini-file: {outfp} --------------")
    ini = _readConfig.InputIni().read_from_inifile(outfp)
    ini.rocktypeDuplicateCheck()
    logger.debug(f"-------------- finished test Ini-file: {outfp} --------------")

    # base directoryへコピー
    outfp2 = create_fullpath(os.path.join(ini.configuration.TOUGH_INPUT_DIR, os.path.basename(outfp)))
    shutil.copy(outfp, outfp2)
    logger.debug(f"Ini-file: {outfp} was copied to {ini.configuration.TOUGH_INPUT_DIR}")
    
    return msg_dict, outfp, outfp2


@app.route('/test_create', methods=['GET', 'POST'])
def test_create():
    """ get logger """
    logger = define_logging.getLogger(
        f"controller.{sys._getframe().f_code.co_name}")
    
    if request.method == 'POST':
        createdFp = os.path.join(pathlib.Path(__file__).parent.resolve(), 
                    request.form['createdIniFp'])
        
        ini = _readConfig.InputIni().read_from_inifile(createdFp)
        ini.rocktypeDuplicateCheck()

        error_msg = {}
        short_msg = ""
        os.makedirs(ini.t2FileDirFp, exist_ok=True)
        logger.debug(f"dir: {ini.t2FileDirFp} is prepared")
        if not os.path.isfile(ini.t2FileFp) or 'overwrites_prob' in request.form:
            logger.debug(f"create new:{ini.t2FileFp}")
            if not os.path.isfile(ini.t2GridFp):
                logger.debug(f"into method: makeGridFunc.makeGrid")
                makeGridFunc.makeGrid(ini=ini, force_overwrite_all=False, force_overwrite_t2data=True, open_viewer=False)
                logger.debug(f"finined: makeGridFunc.makeGrid")
            logger.debug(f"into method: tough3exec_ws.makeToughInput")
            tough3exec_ws.makeToughInput(ini)
            logger.debug(f"finished: tough3exec_ws.makeToughInput")
            short_msg = f"TOUGH inputs created in {ini.t2FileDirFp}"
        else:
            error_msg['prob_exists'] = f"The input file (t2data.dat): \"{create_relpath(ini.t2FileFp)}\"  has already been created. Please check 'Force overwrite' and try again."
        
        # return to cmesh5.html     
        form = dict(request.form)
        form.pop('overwrites_prob', None) # reset status: 'overwrites_prob'
        form = construct_simulator_paths(form)
        outfp = os.path.join('static', 'output', f'input_final_{request.form["problemName"]}.ini')
        return render_template('cmesh5.html', form=form, downloadlink=outfp, 
                                error_msg=error_msg if len(error_msg)>0 else None,
                                short_msg=short_msg,
                                projRoot=projRoot
                                )

    else:
        return redirect(url_for('index'))

@app.route('/ajax_test/')
def ajax_test():
    return app.send_static_file('ajax_test.html')


@app.route('/ajax_test_api', methods=['GET', 'OPTIONS'])
def ajax_test_api():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":
        a = request.args.get('key1', '')
        print(a)
        # これだとブラウザでエラーになる
        # "blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource."
        # return jsonify({"data":f"I received {a}"}) 
        return _corsify_actual_response(jsonify({"ajax_test_api_return1":f"I received {a}"}))

@app.route('/checkrun', methods=['GET', 'OPTIONS'])
def checkrun():
    global THREADS_TOUGH_RUNNING
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":
        ret = []
        is_running = False
        for i,thr in enumerate(THREADS_TOUGH_RUNNING):
            is_running |= thr['thread'].is_alive()
            info = 'running' if thr['thread'].is_alive() else 'dead'
            # get number of steps and last time step length
            cofts = glob.glob(os.path.join(thr['t2FileDir'],"FOFT*.csv"))
            steps = None
            time_step_length = None
            time = None #[second]
            time_y = None #[year]
            if len(cofts)>0:
                # case if COFT* found
                with open(cofts[0], "r") as f:
                    lines = f.readlines()
                    steps = len(lines)-1 # number of lines except for 1st line
                    if steps==1:
                        time = time_step_length = float(lines[-1].split(",")[0])
                        time_y = time/365.25/24/3600
                    elif steps>2:
                        time = float(lines[-1].split(",")[0])
                        time_step_length =  time - float(lines[-2].split(",")[0])
                        time_y = time/365.25/24/3600

            msg = f'(Proc. {i+1}) inifp: {create_relpath(thr["inifp"])} is {info}. Steps: {steps}. Time: {time_y:.2f} year. Time step length: {time_step_length} [s]'
            print(msg)
            ret.append(msg)

        return _corsify_actual_response(jsonify({'status':ret, 'is_running':is_running}))

@app.route('/run_tough3', methods=['GET', 'OPTIONS'])
def run_tough3():
    # global IS_RUNNING_TOUGH3
    global THREADS_TOUGH_RUNNING
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":
        ret = {'status_msg':[], 'error_msg':[], 'flg_started':False}
        inifp = request.args.get('key1', '').strip()

        if not os.path.isfile(create_fullpath(inifp)):
            ret['error_msg'].append(f"Flie not found: {inifp}")
            return _corsify_actual_response(jsonify(ret))
        
        if not os.path.isfile(MPIEXEC):
            ret['error_msg'].append(f"MPIEXEC not found: {MPIEXEC}")
            return _corsify_actual_response(jsonify(ret))
        
        ini = _readConfig.InputIni().read_from_inifile(create_fullpath(inifp))

        if not os.path.isfile(ini.configuration.COMM_EXEC):
            ret['error_msg'].append(f"Executable not found: {ini.configuration.COMM_EXEC}")
            return _corsify_actual_response(jsonify(ret))
        
        # Check if tough3 simulation for the passed ini-file is running.
        isrunning = create_relpath(inifp) in get_running_inifp_list()
        
        if isrunning:
            ret['error_msg'].append(f"process for '{os.path.basename(inifp)}' is running")
        else:
            # If there are threads involving the same inifp, delete the older one
            for i, thr in enumerate(THREADS_TOUGH_RUNNING):
                if inifp in thr['inifp']:
                    del THREADS_TOUGH_RUNNING[i]
            # create new thread
            thread = Thread(target=run.execute, 
                            args=(_readConfig.InputIni().read_from_inifile(create_fullpath(inifp)),), 
                            name="SubThread", 
                            daemon=True)
            # start execution
            thread.start()
            ret['status_msg'].append(f"start tough3 run for: {os.path.basename(inifp)}")
            ret['flg_started'] =    True
            THREADS_TOUGH_RUNNING.append({'thread':thread, 'inifp':create_fullpath(inifp), 't2FileDir':ini.t2FileDirFp})

        ret['running_processes'] = get_running_inifp_list()
        return _corsify_actual_response(jsonify(ret))

@app.route('/python_str_to_eval_api', methods=['GET', 'OPTIONS'])
def python_str_to_eval_api():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":
        ret = None
        error_msg = None
        try:
            ret = eval(request.args.get('key1', ''))
        except:
            error_msg = "Error in python eval()"

        return _corsify_actual_response(jsonify({"eval_result":ret, "error_msg":error_msg}))

@app.route('/api_voronoi_plot_qhull', methods=['GET', 'OPTIONS'])
def api_voronoi_plot_qhull():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":
        error_msg = None

        seedfp = request.args.get('seedfp', '')
        try:
            min_edge_len = float(request.args.get('min_edge_len', ''))
        except:
            error_msg = "invalid tolar: {request.args.get('min_edge_len', '')}"
            return _corsify_actual_response(jsonify({"error_msg":error_msg}))
        
        if not os.path.isfile(create_fullpath(seedfp)):
            error_msg = f"voronoi_seeds_list_fp not found: '{seedfp}'"
            return _corsify_actual_response(jsonify({"error_msg":error_msg}))

        """
        'Matplotlib is not thread-safe:...'
        https://matplotlib.org/stable/users/faq.html#work-with-threads
        """
        now = time.time()
        savefp = f'gui/static/output/vorocheck_{now}.png'
        try:
            seed_to_voronoi.creates_2d_voronoi_grid(
                create_fullpath(seedfp), min_edge_len, 
                preview_save_fp=create_fullpath(savefp), show_preview=False
            )
        except:
            error_msg = f"Error in seed_to_voronoi.creates_2d_voronoi_grid"

        return _corsify_actual_response(jsonify({"img_fp":re.sub("gui/", "", savefp), "error_msg":error_msg}))

def get_running_inifp_list():
    global THREADS_TOUGH_RUNNING
    ret = []
    for proc in THREADS_TOUGH_RUNNING:
        thr: Thread = proc['thread']
        if thr.is_alive():
            ret.append(create_relpath(proc['inifp']))
    return ret

def _build_cors_preflight_response():
    # ajax開発用 CORS対策
    # https://stackoverflow.com/questions/25594893/how-to-enable-cors-in-flask
    # https://qiita.com/Shoma0210/items/4405898205a1822f5826
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    # ajax開発用 CORS対策
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

app.run(port=8000, debug=True)  