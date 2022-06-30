#-------------------------------------------------------------------------------
from attr import has
from import_pytough_modules import *
#
from io import DEFAULT_BUFFER_SIZE
import os
# import sys
import datetime
import math
import configparser
import numpy as np
import pathlib
from t2data import rocktype, t2block
from define import *
import define_logging

# get directory name where this script is located
# import pathlib
# baseDir = pathlib.Path(__file__).parent.resolve()

def create_fullpath(pathstr):
    if os.path.isabs(pathstr):
        return pathstr
    else:
        # create abspath from relpath
        return os.path.abspath(os.path.join(baseDir, pathstr))
    
def create_relpath(pathstr):
    # relative path from baseDir root
    return os.path.relpath(create_fullpath(pathstr), start=baseDir)


class logUpdateConfigIni(object):
    """get list of file path of setting.ini """
    def __init__(self, iniFp:str):
        """ get logger """
        logger = define_logging.getLogger(
            f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

        self.iniFp = iniFp
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.iniFp ):
            self.config.read(self.iniFp) 
        else: 
            logger.error(f"file not found: {self.iniFp }")
            raise FileNotFoundError
        self.settingIniList = []
        for s in self.config['logupdate']:
            self.settingIniList.append(self.config['logupdate'][s])

class SettingIni(object):
    # section: toughConfig
    class _toughConfig(object):
        def __init__(self, config: configparser.ConfigParser):
            try:
                self.GRID_DIR = config.get('toughConfig', 'GRID_DIR')
            except:
                self.GRID_DIR = ""
            self.TOUGH_INPUT_DIR = config.get('toughConfig','TOUGH_INPUT_DIR')


    # section: toughexec
    class _toughexec(object):
        def __init__(self, config: configparser.ConfigParser):
            pass
            """ 2022/06/17 No longer necessary. 
            self.COMM_EXEC = None
            self.BIN_DIR = None
            self.BIN_DIR_T2 = None
            self.BIN_DIR_LOCAL = None
            # discard exception for backward compatibility
            try:
                self.COMM_EXEC = config.get('toughexec', 'COMM_EXEC')
            except:
                pass
            try:
                self.BIN_DIR = config.get('toughexec', 'BIN_DIR')
            except:
                pass
            try:
                self.BIN_DIR_T2 = config.get('toughexec', 'BIN_DIR_T2')
            except:
                pass
            try:
                self.BIN_DIR_LOCAL = config.get('toughexec', 'BIN_DIR_LOCAL')
            except:
                pass
            """
    
    # section: ameshexec
    """
    # these settings are converted to define.py 
    class _ameshexec(object):
        def __init__(self, config: configparser.ConfigParser):
            try:
                self.AMESH_DIR = os.path.join(baseDir, config.get('ameshexec','AMESH_DIR'))
                self.AMESH_PROG = config.get('ameshexec','AMESH_PROG')
                self.INPUT_FILENAME = config.get('ameshexec','INPUT_FILENAME')
                self.SEGMT_FILENAME = config.get('ameshexec','SEGMT_FILENAME')
            except:
                self.AMESH_DIR = None
                self.AMESH_PROG = None
                self.INPUT_FILENAME = None
                self.SEGMT_FILENAME = None
    """

    def __init__(self, settingIniFp:str):
        """ get logger """
        logger = define_logging.getLogger(
            f"{__class__.__name__}.{sys._getframe().f_code.co_name}")
        
        self.iniFp = settingIniFp
        ### reading setting.ini ###
        self.config = configparser.ConfigParser()
        if os.path.isfile(settingIniFp):
            self.config.read(settingIniFp) 
        else:
            logger.error(f"file not found: {settingIniFp}")
            raise FileNotFoundError
        self.toughConfig = self._toughConfig(self.config)
        self.toughexec = self._toughexec(self.config)
        # self.ameshexec = self._ameshexec(self.config)


class InputIni(object):

    def __init__(self):
        self.mesh = self._MeshSec()
        self.solver = self._SolverSec()
        self.plot = self._PlotSec()
        self.boundary = self._Boundary()
        self.atmosphere = self._Atmosphere()
        self.configuration = self._Configuration()

    def read_from_inifile(self, inputIniFp:str):
        """ get logger """
        logger = define_logging.getLogger(
            f"{__class__.__name__}.{sys._getframe().f_code.co_name}")
        
        self.inputIniFp = inputIniFp
        ### read inputIni ###
        self.config = configparser.ConfigParser(defaults=None)
        logger.info(f"PARAM SETTING FILE :{inputIniFp}")
        if os.path.isfile(inputIniFp):
            self.config.read(inputIniFp) 
        else:
            logger.error(f"file not found: {inputIniFp}")
            raise FileNotFoundError
        
        # read sections
        self.mesh = self._MeshSec().read_from_config(self.config)
        if self.mesh.type == AMESH_VORONOI:
            """ amesh voronoi """
            try:
                self.amesh_voronoi = self._AmeshVoronoi().read_from_config(self.config)
            except:
                # すでにグリッド作成済みで設定不要の場合
                pass
        self.solver = self._SolverSec().read_from_config(self.config)
        self.plot = self._PlotSec().read_from_config(self.config)
        self.boundary = self._Boundary().read_from_config(self.config)
        self.atmosphere = self._Atmosphere().read_from_config(self.config)
        self.configuration = self._Configuration().read_from_config(self.config)

        # read section [toughInput]
        # GUIで使うときは[toughInput]セクションが不完全な場合に読み込みが行われるので、
        # エラーを握りつぶすようにする
        # TODO できればtry-catchじゃない実装にしたい
        try:
            self.toughInput = self._readInputIniToughInput()
        except:
            logger.warning("Section [toughInput] is incomplete. Reading is skipped. "
            "InputIni.construct_path() is skipped."" InputIni.validation() is skipped.")
            # 自作の例外クラスをraise
            raise InvalidToughInputException

        # define file path
        try:
            self.construct_path()
        except:
            logger.warning("Fail to construct path in InputIni.construct_path(). Skip.")
    
        self.validation()

        return self
    
    def construct_path(self):
        """ get logger """
        logger = define_logging.getLogger(
            f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

        # define file path
        if hasattr(self, 'mesh') and hasattr(self.mesh, 'mulgridFileFp'):
            # 20220221以降はmeshにmulgridのパスを保持
            self.mulgridFileFp = os.path.join(
                                    baseDir, 
                                    self.mesh.mulgridFileFp)
        else:
            # backward conpatibility
            self.mulgridFileFp = os.path.join(
                                    baseDir, 
                                    self.setting.toughConfig.GRID_DIR, 
                                    self.toughInput['mulgridFileName'])
            self.mesh.mulgridFileFp = os.path.join(
                                    self.setting.toughConfig.GRID_DIR, 
                                    self.toughInput['mulgridFileName'])
            
        # try:
        #     # if TOUGH_INPUT_DIR setting is found in input.ini
        #     TID = config['configuration']['TOUGH_INPUT_DIR']
        #     if os.path.isdir(os.path.join(baseDir, TID)):
        #         # overwrite TOUGH_INPUT_DIR in setting.ini
        #         self.configuration.TOUGH_INPUT_DIR = TID
        #     else:
        #         # if available TOUGH_INPUT_DIR is "not" found in input.ini
        #         TID = self.configuration.TOUGH_INPUT_DIR
        # except:
        #     # if available TOUGH_INPUT_DIR is "not" found in input.ini
        #     TID = self.configuration.TOUGH_INPUT_DIR
        # self.t2FileDirFp = os.path.join(baseDir, TID, 
        #                             self.toughInput['problemName'])

        self.t2FileDirFp = os.path.join(
                                baseDir, 
                                self.configuration.TOUGH_INPUT_DIR, 
                                self.toughInput['problemName'])
        if hasattr(self.plot, 'reads_data_from_current_dir'):
            if self.plot.reads_data_from_current_dir:
                # To read result from current dir, 
                # disguise self.t2FileDirFp with current inputIniFp
                self.t2FileDirFp = os.path.abspath(os.path.dirname(self.inputIniFp))
                logger.info(f"now InputIni.t2FileDirFp is overwritten by directory including"\
                    +" inputIni file for reading result in current place.")

        self.t2FileFp = os.path.join(
                                self.t2FileDirFp, 
                                FILENAME_T2DATA)
        self.t2GridFp = f"{self.t2FileFp}.grid"
        self.tOutFileFp = os.path.join(
                                self.t2FileDirFp, 
                                FILENAME_TOUGH_OUTPUT)
        self.resultVtuFileFp = os.path.join(
                                self.t2FileDirFp,
                                FILENAME_RESULT_VTU)
        self.t3outEscapeFp = os.path.join(
                                self.t2FileDirFp,
                                T3OUT_ESCAPE_DIRNAME)
        self.savefigFp = os.path.join(
                                self.t2FileDirFp,
                                SAVEFIG_DIRNAME)
        self.inconFp = os.path.join(
                                self.t2FileDirFp, 
                                INCON_FILE_NAME)
        self.saveFp = os.path.join(
                                self.t2FileDirFp, 
                                SAVE_FILE_NAME)

    def validation(self):
        """ get logger """
        logger = define_logging.getLogger(
            f"{__class__.__name__}.{sys._getframe().f_code.co_name}")
        logger.debug(repr(self.toughInput))
        if self.mesh.type==AMESH_VORONOI and self.toughInput['seedFlg']:
            for rock in self.rockSecList:
                if rock.formula_permeability is None: raise Exception
    
    def rocktypeDuplicateCheck(self):
        # if rocktype name is duplicated, then exit.
        rocktypenames = []
        for sec in self.rockSecList:
            if sec.rocktype.name in rocktypenames:
                sys.exit(f"!!!ERROR rocktype.name: {sec.rocktype.name} (@[{sec.secName}]) is already used. Exit")
            rocktypenames.append(sec.rocktype.name )

    def _readInputIniToughInput(self):
        """ get logger """
        logger = define_logging.getLogger(
            f"{__class__.__name__}.{sys._getframe().f_code.co_name}")
        
        ret = {}

        ret['module'] = self.config.get('toughInput', 'module').lower()
        
        """
        Read type of simulator (TOUGH3, TOUGH2, TOUGH3_local)
        if 'simulator' is not provided in InputIni, use TOUGH3 as 'simulator' 
        """
        try:    
            ret['simulator'] = self.config.get('toughInput', 'simulator').upper()
        except:
            ret['simulator'] = SIMULATOR_NAME_T3

        """
        Define a path of executable by using 'module' in inputIni and 'BIN_DIR' in define_path.py.
        """
        if ret['simulator']==SIMULATOR_NAME_T3:
            self.configuration.COMM_EXEC = \
                os.path.join(BIN_DIR,f"tough3-{ret['module']}")
        if ret['simulator']==SIMULATOR_NAME_T2:
            self.configuration.COMM_EXEC = \
                os.path.join(BIN_DIR_T2,f"xt2_{ret['module']}")
        if ret['simulator']==SIMULATOR_NAME_T3_LOCAL:
            """
            simulator='TOUGH3_LOCAL' is totally same as simulator='TOUGH3' 
            other than the setting about a path of executable.  
            """
            ret['simulator'] = SIMULATOR_NAME_T3
            if BIN_DIR_LOCAL is None:
                self.configuration.COMM_EXEC = \
                    os.path.join(BIN_DIR,f"tough3-{ret['module']}")
                logger.warning("!! simulator is TOUGH3_LOCAL, but BIN_DIR_LOCAL is not found in define_path.py.")
                logger.warning(f"             use COMM_EXEC: {self.configuration.COMM_EXEC}")
            else:
                self.configuration.COMM_EXEC = \
                    os.path.join(BIN_DIR_LOCAL,f"tough3-{ret['module']}")

        ret['problemName'] = self.config.get('toughInput', 'problemName')
        # ret['mulgridFileName'] = self.config.get('toughInput', 'mulgridFileName')
        try:
            ret['mulgridFileName'] = self.config.get('toughInput', 'mulgridFileName')
        except configparser.NoOptionError:
            ret['mulgridFileName'] = ret['problemName'] + ".dat"
        
        # ret['t2DataFileName'] = self.config.get('toughInput', 't2DataFileName')
        # ret['gridVtkFileName'] = self.config.get('toughInput', 'gridVtkFileName')
        # ret['toughOutputFileName'] = self.config.get('toughInput', 'toughOutputFileName')
        # ret['resultVtuFileName'] = self.config.get('toughInput', 'resultVtuFileName')
        ret['num_components'] = int(self.config.get('toughInput', 'num_components'))
        ret['num_equations'] = int(self.config.get('toughInput', 'num_equations'))
        ret['num_phases'] = int(self.config.get('toughInput', 'num_phases'))
        ret['num_secondary_parameters'] = int(self.config.get('toughInput', 'num_secondary_parameters'))
        # moved to class:_Atmosphere
        # ret['PRIMARY_AIR'] = eval(self.config.get('toughInput', 'PRIMARY_AIR')) 
        ret['PRIMARY_default'] = eval(self.config.get('toughInput', 'PRIMARY_default'))
        # PARAM.1.MOPs
        ret['MOPs01'] = int(self.config.get('toughInput', 'MOPs01'))
        ret['MOPs02'] = int(self.config.get('toughInput', 'MOPs02'))
        ret['MOPs03'] = int(self.config.get('toughInput', 'MOPs03'))
        ret['MOPs04'] = int(self.config.get('toughInput', 'MOPs04'))
        ret['MOPs05'] = int(self.config.get('toughInput', 'MOPs05'))
        ret['MOPs06'] = int(self.config.get('toughInput', 'MOPs06'))
        ret['MOPs07'] = int(self.config.get('toughInput', 'MOPs07'))
        ret['MOPs08'] = int(self.config.get('toughInput', 'MOPs08'))
        ret['MOPs09'] = int(self.config.get('toughInput', 'MOPs09'))
        ret['MOPs10'] = int(self.config.get('toughInput', 'MOPs10'))
        ret['MOPs11'] = int(self.config.get('toughInput', 'MOPs11'))
        ret['MOPs12'] = int(self.config.get('toughInput', 'MOPs12'))
        ret['MOPs13'] = int(self.config.get('toughInput', 'MOPs13'))
        # ret['MOPs14'] = int(self.config.get('toughInput', 'MOPs14'))
        ret['MOPs14'] = 0 # void
        ret['MOPs15'] = int(self.config.get('toughInput', 'MOPs15'))
        ret['MOPs16'] = int(self.config.get('toughInput', 'MOPs16'))
        ret['MOPs17'] = int(self.config.get('toughInput', 'MOPs17'))

        # convergence criterion for relative error (RE1)
        try:
            ret['relative_error'] = float(self.config.get('toughInput', 'relative_error'))
        except:
            ret['relative_error'] = 1e-5

        # if no inconfile given, 
        # hydrostatic pressure is applied as initial condition.
        ret['problemNamePreviousRun'] = \
            self.config.get('toughInput', 'problemNamePreviousRun')
        try:
            ret['water_table_elevation'] = \
                float(self.config['toughInput']['water_table_elevation'])
        except:
            ret['water_table_elevation'] = None
        
        try:
            ret['1d_hydrostatic_sim_result_ini'] = \
                self.config['toughInput']['1d_hydrostatic_sim_result_ini'].strip()
            if len(ret['1d_hydrostatic_sim_result_ini']) > 0:
                ret['use_1d_result_as_incon'] = True
            else:
                ret['use_1d_result_as_incon'] = False
        except:
            ret['use_1d_result_as_incon'] = False
        
        # if both 'problemNamePreviousRun' and '1d_hydrostatic_sim_result_ini' are empty,
        # following temperature gradient is used for creating INCON
        try:
            ret['initial_t_grad'] = float(self.config['toughInput']['initial_t_grad'])
        except:
            ret['initial_t_grad'] = 0            

        ret['rockSecList'] = \
            eval(self.config.get('toughInput', 'rockSecList'))
        self.rockSecList = []
        for rockSec in  ret['rockSecList']:
            self.rockSecList.append(self._RocktypeSec(rockSec, self.config))

        ret['generSecList'] = \
            eval(self.config.get('toughInput', 'generSecList'))
        self.generSecList = []
        for generSec in  ret['generSecList']:
            self.generSecList.append(self._GenerSec(generSec, self.config))

        ret['crustalHeatFlowRate'] = \
            float(self.config.get('toughInput', 'crustalHeatFlowRate'))
        ret['rainfallAnnual_mm'] = \
            float(self.config.get('toughInput', 'rainfallAnnual_mm'))
        ret['T_rain'] = \
            float(self.config.get('toughInput', 'T_rain'))
        ret['history_block'] = \
            eval(self.config.get('toughInput', 'history_block'))
        try:
            ret['history_connection'] = []
            # validation
            for c in eval(self.config.get('toughInput', 'history_connection')):
                if isinstance(c, tuple): 
                    ret['history_connection'].append(c)
                else:
                    logger.info(f' history_connection: {c} is not tuple. skip')
        except configparser.NoOptionError as e:
            logger.info(e)
            logger.info("skip")
        try:
            ret['prints_hc_surface'] = eval(self.config.get('toughInput', 'prints_hc_surface'))
        except:
            ret['prints_hc_surface'] = False
        try:
            ret['prints_hc_inj'] = eval(self.config.get('toughInput', 'prints_hc_inj'))
        except:
            ret['prints_hc_inj'] = False
        if "eco2n_v2" == ret['module'].strip():
            # SELEC
            ret['selection_line1'] = eval(self.config.get('toughInput', 'selection_line1'))
            ret['selection_line2'] = eval(self.config.get('toughInput', 'selection_line2'))

        try:
            ret['max_timestep_TIMES'] = float(self.config.get('toughInput', 'max_timestep_TIMES'))
            ret['num_times_specified'] = int(self.config.get('toughInput', 'num_times_specified'))
            ret['num_times'] = int(self.config.get('toughInput', 'num_times'))
            ret['time'] = eval(self.config.get('toughInput', 'time'))
            ret['time_increment'] = float(self.config.get('toughInput', 'time_increment'))
            if ret['num_times_specified'] > 0:
                ret['setTimes'] = True 
            else:
                ret['setTimes'] = False
        except:
            ret['setTimes'] = False 

        try:
            ret['seedFlg'] = eval(self.config['toughInput']['seedFlg'])
        except:
            ret['seedFlg'] = False
        
        
        # read INCON setting part
        if len(ret['problemNamePreviousRun']) == 0:
            try:
                ret['specifies_variable_INCON'] = eval(self.config.get('toughInput', 'specifies_variable_INCON'))
                logger.info(' specifies_variable_INCON True')
            except:
                ret['specifies_variable_INCON'] = False
                logger.info(' specifies_variable_INCON False')

            if ret['specifies_variable_INCON']:
                primary_sec_list = eval(self.config.get('toughInput', 'primary_sec_list'))
                self.primary_sec_list = []
                for secName in primary_sec_list:
                    self.primary_sec_list.append(self._PrimarySec(secName, self.config))
        

        # PARAM 
        params = {'max_iterations','print_level','max_timesteps','max_duration',
                'print_interval', 'texp','be','tstart','tstop','const_timestep',
                'max_timestep','print_block','gravity','timestep_reduction',
                'scale','relative_error','absolute_error','upstream_weight',
                'newton_weight','derivative_increment','for','amres',}
        found, notfound = [], []
        for param in params:
            try:
                ret[param] = eval(self.config.get('toughInput', param))
                found.append(param)
            except:
                notfound.append(param)
        logger.info(f" PARAM found:{found}")
        logger.info(f" PARAM not found:{notfound}")

        try:
            ret['assignFocusHf'] = eval(self.config.get('toughInput', 'assignFocusHf'))
            ret['focusHfRate'] = float(self.config.get('toughInput', 'focusHfRate'))
            ret['focusHfRange'] = eval(self.config.get('toughInput', 'focusHfRange'))
        except:
            ret['assignFocusHf'] = False
        
        return ret
    
    class _Configuration(object):

        def __init__(self):
            pass 

        def read_from_config(self, config: configparser.ConfigParser):
            """ get logger """
            logger = define_logging.getLogger(
                f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

            try:
                self.TOUGH_INPUT_DIR = config['configuration']['TOUGH_INPUT_DIR']        
            except:
                # for backward compatibility
                logger.warning('no configuration.TOUGH_INPUT_DIR setting. Instead, try to read TOUGH_INPUT_DIR from configuration.configIni' )
                if config.has_option('configuration', 'configIni'):
                    self.configIni = config.get('configuration', 'configIni')
                else:
                    logger.error('no configuration setting. use default config' )
                    self.configIni = 'setting.ini'
                logger.info(f"CONFIG FILE :{self.configIni}")
            
                if not os.path.isfile(os.path.join(baseDir,self.configIni)): 
                    logger.error(f"CONFIG FILE:{os.path.join(baseDir,self.configIni)} not found")
                    raise FileNotFoundError(f"CONFIG FILE:{os.path.join(baseDir,self.configIni)} not found")
                
                ### reading setting.ini ###
                logger.info(f"CONFIG FILE :{self.configIni} ")
                self.setting = SettingIni(os.path.join(baseDir,self.configIni))
                self.TOUGH_INPUT_DIR = self.setting.toughConfig.TOUGH_INPUT_DIR
            
            return self

    class _PlotSec(object):
        def __init__(self):
            # set default values
            self.slice_plot_limits = None
            self.slice_plot_variables_T2 = ['T', 'SG']
            self.slice_plot_variables_T3 = ['TEMP', 'SAT_G']
            self.profile_lines_list = PROFILE_LINES_LIST_DEFAULT
            self.xoft_t_range = None
            self.gif_minimun_print_interval_sec = 1
            self.columns_incon_plot = None
            self.reads_data_from_current_dir = False


        def read_from_config(self, config: configparser.ConfigParser):
            """ get logger """
            logger = define_logging.getLogger(
                f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

            try:
                self.slice_plot_limits = eval(config['plot']['slice_plot_limits'])
            except:
                self.slice_plot_limits = None

            try:
                self.slice_plot_variables_T2 = eval(config['plot']['slice_plot_variables_T2'])
            except:
                self.slice_plot_variables_T2 = ['T', 'SG']
            try:
                self.slice_plot_variables_T3 = eval(config['plot']['slice_plot_variables_T3'])
            except:
                self.slice_plot_variables_T3 = ['RES', 'TEMP', 'SAT_G', 'SAT_S', 'X_WATER_G', 'X_CO2_G', 'X_WATER_L', 'X_NaCl_L', 'X_CO2_L', 'FLOW']
            
            try:
                self.xoft_t_range = eval(config['plot']['xoft_t_range'])
            except:
                self.xoft_t_range = None
            try:
                self.gif_minimun_print_interval_sec = \
                    eval(config['plot']['gif_minimun_print_interval_sec'])
            except:
                self.gif_minimun_print_interval_sec = 1
            finally:
                # this value must larger than 0.001
                if self.gif_minimun_print_interval_sec < 0.001:
                    self.gif_minimun_print_interval_sec = 0.001
            try:
                self.columns_incon_plot = eval(config['plot']['columns_incon_plot'])
            except:
                self.columns_incon_plot = None
            try:
                # if true, reads data from directory where inputIni file put
                self.reads_data_from_current_dir = \
                    eval(config['plot']['reads_data_from_current_dir'])
                logger.info(f"reads_data_from_current_dir: {self.reads_data_from_current_dir}")
            except:
                # reads data from InputIni.t2FileDirFp
                self.reads_data_from_current_dir = False
            try:
                self.profile_lines_list = \
                    eval(config['plot']['profile_lines_list'])
                for i, line in enumerate(self.profile_lines_list):
                    if isinstance(line, list):
                        self.profile_lines_list[i] = np.array(line)
                        
            except:
                self.profile_lines_list = PROFILE_LINES_LIST_DEFAULT
            return self

    class _PrimarySec(object):
        def __init__(self, primarySecName, config: configparser.ConfigParser):
            self.secName = primarySecName
            self.value = eval(config.get(primarySecName, 'value'))
            self.xmin = float(config.get(primarySecName, 'xmin'))
            self.xmax = float(config.get(primarySecName, 'xmax'))
            self.ymin = float(config.get(primarySecName, 'ymin'))
            self.ymax = float(config.get(primarySecName, 'ymax'))
            self.zmin = float(config.get(primarySecName, 'zmin'))
            self.zmax = float(config.get(primarySecName, 'zmax'))

    class _RocktypeSec(object):
        def __init__(self, rocktypeSecName, config: configparser.ConfigParser):
            """ get logger """
            logger = define_logging.getLogger(
                f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

            self.secName = rocktypeSecName
            self.name  = f"{config[rocktypeSecName]['name']:<5}" # 5 characters long
            self.nad  = int(config[rocktypeSecName]['nad'])
            self.density  = float(config[rocktypeSecName]['density'])
            self.porosity  = float(config[rocktypeSecName]['porosity'])
            self.permeability_x  = \
                float(config[rocktypeSecName]['permeability_x'])
            self.permeability_y  = \
                float(config[rocktypeSecName]['permeability_y'])
            self.permeability_z  = \
                float(config[rocktypeSecName]['permeability_z'])
            self.conductivity  = \
                float(config[rocktypeSecName]['conductivity'])
            self.specific_heat  = \
                float(config[rocktypeSecName]['specific_heat'])
            regionSecList  = \
                eval(config[rocktypeSecName]['regionSecList'])
            self.regionSecList = []
            for sec in regionSecList:
                self.regionSecList.append(self._RegionSec(sec, config))
            try:
                self.blockList = eval(config[rocktypeSecName]['blocklist'])
                # check 
                for b in self.blockList:
                    if len(b)!=5: logger.warning(f"incorrect blk name {b} in [{rocktypeSecName}] blocklist")

            except:
                self.blockList = []

            if self.nad >= 2:
                self.IRP = int(config[rocktypeSecName]['IRP'])
                self.RP = eval(config[rocktypeSecName]['RP'])
                self.ICP = int(config[rocktypeSecName]['ICP'])
                self.CP = eval(config[rocktypeSecName]['CP'])
            
            try:
                self.formula_porosity = \
                    config[rocktypeSecName]['formula_porosity']
                self.formula_permeability = \
                    config[rocktypeSecName]['formula_permeability']
            except:
                # for backward compatibility
                try:
                    self.formula_porosity = \
                        config[rocktypeSecName]['formula_resistivity2porosity']
                    self.formula_permeability = \
                        config[rocktypeSecName]['formula_porosity2permeability']
                except:
                    self.formula_porosity = None
                    self.formula_permeability = None

            try:
                self.rock_assign_condition = \
                    config[rocktypeSecName]['rock_assign_condition']
            except:
                self.rock_assign_condition = "True"

            # generate rocktype object
            self.rocktype = rocktype(name = self.name, nad = self.nad, 
                                     density = self.density, 
                                     porosity = self.porosity, 
                                     permeability = [self.permeability_x, 
                                                     self.permeability_y, 
                                                     self.permeability_z], 
                                     conductivity = self.conductivity, 
                                     specific_heat = self.specific_heat)
            if self.nad >= 2:
                self.rocktype.relative_permeability = {'parameters':self.RP, 'type':self.IRP}
                self.rocktype.capillarity = {'parameters':self.CP, 'type':self.ICP}
            
        def isBlkInAssignableRange(self, blk:t2block):
            """[summary]
            Check if the given block is included in any one of the assignable regions, 
                which are defined at regionSecList.

            Returns:
                True or False
            """
            # region
            for reg in self.regionSecList:
                if reg.xmin <= blk.centre[0] < reg.xmax \
                        and reg.ymin <= blk.centre[1] < reg.ymax \
                        and reg.zmin <= blk.centre[2] < reg.zmax :
                    return True
            return False

        def isBlkInBlockList(self, blk:t2block):
            """[summary]
            Check if the given block is included in self.blockList, 
                which are defined at regionSecList.

            Returns:
                True or False
            """
            """ get logger """
            logger = define_logging.getLogger(
                f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

            # block
            if blk.name in self.blockList: 
                logger.debug(f"     blk'{blk.name}': True")
                return True
            return False

        class _RegionSec(object):
            def __init__(self, regionSecName, config: configparser.ConfigParser):
                self.secName = regionSecName
                self.xmin = float(config[regionSecName]['xmin'])
                self.xmax = float(config[regionSecName]['xmax'])
                self.ymin = float(config[regionSecName]['ymin'])
                self.ymax = float(config[regionSecName]['ymax'])
                self.zmin = float(config[regionSecName]['zmin'])
                self.zmax = float(config[regionSecName]['zmax'])

    class _Atmosphere(object):

        def __init__(self):
            pass 

        def read_from_config(self, config: configparser.ConfigParser):
            """ get logger """
            logger = define_logging.getLogger(
                f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

            try:
                self.PRIMARY_AIR = eval(config['atmosphere']['PRIMARY_AIR'])
                self.includesAtmos = eval(config['atmosphere']['includesAtmos'])
                ## rocktype
                if self.includesAtmos:
                    self.atmos = \
                        rocktype(name = "atmos", 
                                 nad = int(config['atmosphere']['nad']), 
                                 density = float(config['atmosphere']['density']), 
                                 porosity = float(config['atmosphere']['porosity']), 
                                 permeability = eval(config['atmosphere']['permeability']), 
                                 conductivity = float(config['atmosphere']['conductivity']), 
                                 specific_heat = float(config['atmosphere']['specific_heat']))
                    if self.atmos.nad >= 1:
                        try: self.atmos.tortuosity = float(config['atmosphere']['tortuosity'])
                        except: pass
                    if self.atmos.nad >= 2:
                        self.atmos.relative_permeability = \
                            {'parameters': eval(config['atmosphere']['RP']), 
                             'type': int(config['atmosphere']['IRP'])}
                        self.atmos.capillarity = \
                            {'parameters':eval(config['atmosphere']['CP']), 
                             'type':int(config['atmosphere']['ICP'])}
            except:
                # for backward compatibility
                self.PRIMARY_AIR = eval(config['toughInput']['PRIMARY_AIR'])
                try:
                    self.includesAtmos = \
                        eval(config['toughInput']['includesAtmos'])
                except:
                    logger.info(f" 'includesAtmos' not found in ini, use 'True'")
                    self.includesAtmos = True
                ## rocktype. set default value
                self.atmos = rocktype(name = "atmos", nad = 2, density = 2650.0, 
                                porosity = 0.9999, permeability = [0, 0, 1e-12], 
                                conductivity = 2.51, specific_heat = 1e20)
                # type=1 -> linear
                # param: [rp1,rp2,rp3,rp4]
                #    krl increases from 0-1 in range rp1 <= Sl <= rp3
                #    krg increases from 0-1 in range rp2 <= Sl <= rp4
                # ex. if you use EOS3, Sl is small in usual atmos. (<0.1), so
                # 'parameters': [0.1, 0.0, 1.0, 0.1] -> always krl=0 and krg=1  
                self.atmos.relative_permeability = \
                    {'parameters': [0.1, 0.0, 1.0, 0.1], 'type': 1}
                # type=1 -> linear
                # param: [cp1,cp2,cp3]
                #    cp1=0 -> P_cap is always 0
                self.atmos.capillarity = {'parameters':[0.0, 0.0, 1.0], 'type':1}
                self.atmos.tortuosity = 1.0
            
            return self

    class _GenerSec(object):
        def __init__(self, generSecName, config: configparser.ConfigParser):
            """ get logger """
            logger = define_logging.getLogger(
                f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

            self.secName = generSecName
            self.name = f"{config.get(generSecName, 'name'):<5}" # 5 chararacters long
            self.block = eval(config.get(generSecName, 'block')) 
            self.type = config.get(generSecName, 'type')
            self.flux = eval(config.get(generSecName, 'flux'))
            self.flux_sum = sum(self.flux) if isinstance(self.flux, list) else self.flux
            try:
                self.injectsIndirectly = \
                    eval(config.get(generSecName, 'injectsIndirectly'))
                logger.info(f" 'injectsIndirectly' found (={self.injectsIndirectly})")
            except:
                logger.info(f" 'injectsIndirectly' not found in ini,'injectsIndirectly' = True is set")
                self.injectsIndirectly = True
            try:
                self.temperature = float(config.get(generSecName, 'temperature'))
            except:
                if self.injectsIndirectly:
                    sys.exit(" ERROR. If 'injectsIndirectly' is True, 'temperature' must be provided.")

            if self.injectsIndirectly:
                self.area = eval(config.get(generSecName, 'area')) 
                self.vol_injblock = float(config.get(generSecName, 'vol_injblock'))
                self.dist_injblock = eval(config.get(generSecName, 'dist_injblock'))
            else:
                self.area = None
                self.vol_injblock = None
                self.dist_injblock = None

            # check
            try:
                if self.injectsIndirectly:
                    # indirect injection
                    if len(self.block) != len(self.area): raise Exception
                if not self.injectsIndirectly:
                    # direct injection
                    if (not isinstance(self.flux,list)) and len(self.block)==1: pass 
                    elif (not isinstance(self.flux,list)) and len(self.block) > 1: 
                        raise Exception 
                    elif isinstance(self.flux,list) and len(self.block) != len(self.flux):
                        raise Exception 
            except Exception as e:
                logger.error(f" in setting gener:{self.secName}")
                raise e

            # LTAB - time dependent generation
            try:
                self.ltab = int(config.get(generSecName, 'ltab')) 
                self.time = eval(config.get(generSecName, 'time')) 
                self.flux_factor = eval(config.get(generSecName, 'flux_factor')) 
            except:
                logger.info(f" fail to read LTAB info in gener:{self.secName}")
                logger.info(f"              use default (LTAB = 0)")
                self.ltab = 0
                self.time = []
                self.flux_factor = []
            # check
            if self.ltab <= 1:
                # time independent injection rate/enthalpy.
                pass 
            elif self.ltab == len(self.time) and self.ltab == len(self.flux_factor):
                # time dependent injection rate & constant injection enthalpy.
                # if injectsIndirectry is true, you cannot assign time dependent injection enthalpy 
                pass
            else:
                    logger.error(f" in setting gener:{self.secName}")
                    logger.error(f"    setting of LTAB, F1, F2 are not consistent")
                    raise Exception
                
            # ITAB - time dependent generation (only valid if injectsIndirecty is False)
            # if injectsIndirectry is False, you can assign time dependent injection enthalpy 
            if not self.injectsIndirectly:
                try:
                    self.itab = int(config.get(generSecName, 'itab')) 
                    self.enthalpy_factor = eval(config.get(generSecName, 'enthalpy_factor')) 
                except:
                    logger.info(f" fail to read LTAB info in gener:{self.secName}")
                    logger.info(f"              use default (ITAB = 0)")
                    self.itab = 0
                    self.enthalpy_factor = []
               
                # check
                if self.itab <= 1 and self.ltab <= 1:
                    pass 
                elif (self.ltab == len(self.time) and self.ltab == len(self.flux_factor) and \
                      self.itab == len(self.enthalpy_factor) and self.ltab == self.itab):
                    pass
                else:
                    logger.error(f" in setting gener:{self.secName}")
                    logger.error(f"    setting of LTAB, F1, F2, ITAB, F3 are not consistent")
                    raise Exception
    
    class _MeshSec(object):

        def __init__(self):
            pass 

        def read_from_config(self, config: configparser.ConfigParser):
            """ get logger """
            logger = define_logging.getLogger(
                f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

            try:
                self.type = config['mesh']['type'].upper()
            except:
                logger.info(" section: mesh, param:type is not found. type=REGULAR is used")
                self.type = REGULAR
            
            try:
                self.convention = int(config['mesh']['convention'])
            except KeyError:
                self.convention = 0

            try:
                self.mulgridFileFp = config['mesh']['mulgridFileFp']
            except KeyError:
                pass

            if self.type == REGULAR:
                """
                ragial or recutangular
                """
                self.isRadial = eval(config['mesh']['isRadial'])

                if self.isRadial:
                    logger.info(f"gridtype: RADIAL")
                    rsec = config['mesh']['rblocksSec']
                    self.rblocks = []
                    for l in config[rsec]:
                        self.rblocks += list(eval(config[rsec][l])) 

                    zsec = config['mesh']['zblocksSec']
                    self.zblocks = []
                    for l in config[zsec]:
                        self.zblocks += list(eval(config[zsec][l])) 
                
                else:
                    logger.info(f"gridtype: RECTANGULAR")
                    
                    def check(val, sec): 
                        if type(val) is int or type(val) is float or type(val) is str:
                            sys.exit(f"section [{sec}], blk length must be specified as list or tuple") 
                        return val
                    
                    xsec = config['mesh']['xblocksSec']
                    self.xblocks = []
                    for l in config[xsec]:
                        self.xblocks += list(check(eval(config[xsec][l]),xsec)) 

                    ysec = config['mesh']['yblocksSec']
                    self.yblocks = []
                    for l in config[ysec]:
                        self.yblocks += list(check(eval(config[ysec][l]),ysec)) 
                    
                    zsec = config['mesh']['zblocksSec']
                    self.zblocks = []
                    for l in config[zsec]:
                        self.zblocks += list(check(eval(config[zsec][l]),zsec)) 
            
            elif self.type == AMESH_VORONOI:
                """
                amesh voronoi
                """
                self.resistivity_structure_fp = \
                    os.path.join(baseDir, config['mesh']['resistivity_structure_fp'])
            
            return self

    class _AmeshVoronoi(object):
        def __init__(self):
            pass

        def read_from_config(self, config: configparser.ConfigParser):
            self.topodata_fp = os.path.join(baseDir, config['amesh_voronoi']['topodata_fp'])
            self.voronoi_seeds_list_fp = \
                os.path.join(baseDir, config['amesh_voronoi']['voronoi_seeds_list_fp'])
            self.elevation_top_layer = float(config['amesh_voronoi']['elevation_top_layer'])
            self.layer_thicknesses = eval(config['amesh_voronoi']['layer_thicknesses'])
            self.tolar = float(config['amesh_voronoi']['tolar'])
            try:
                self.top_layer_min_thickness = float(config['amesh_voronoi']['top_layer_min_thickness'])
            except:
                self.top_layer_min_thickness = TOP_LAYER_MIN_THICKNESS_DEFAULT
            return self

    class _Boundary(object):
        def __init__(self):
            pass 

        def read_from_config(self, config: configparser.ConfigParser):
            try:
                self.boundary_side_permeable = eval(config['boundary']['boundary_side_permeable'])
            except:
                self.boundary_side_permeable = False
            return self


    class _SolverSec(object):
        def __init__(self):
            pass

        def read_from_config(self, config: configparser.ConfigParser):
            try:
                self.matslv = int(config['solver']['matslv'])
            except:
                self.matslv = 3

            if self.matslv == 8:
                try:
                    self.nProc = int(config['solver']['nProc'])
                except:
                    self.nProc = 8
                try:
                    self.ksp_type = str(config['solver']['ksp_type'])
                    if self.ksp_type == "": self.ksp_type = None
                except:
                    self.ksp_type = None
                try:
                    self.pc_type = str(config['solver']['pc_type'])
                    if self.pc_type == "": self.pc_type = None
                except:
                    self.pc_type = None
                try:
                    self.ksp_rtol = float(config['solver']['ksp_rtol'])
                    if self.ksp_rtol == "": self.ksp_rtol = None
                except:
                    self.ksp_rtol = None
            else:
                try:
                    self.z_precond = config['solver']['ZPROCS']
                except:
                    self.z_precond = 'Z0'
                try:
                    self.o_precond = config['solver']['OPROCS']
                except:
                    self.o_precond = 'O0'
                try:
                    self.relative_max_iterations = float(config['solver']['RITMAX'])
                except:
                    self.relative_max_iterations = 0.1
                try:
                    self.closure = float(config['solver']['CLOSUR'])
                except:
                    self.closure = 1.e-6
            return self


    def _readInputIniSettingPlot(self):
        # setting for t2outUtil.plot_param_time
        ret = {}
        ret['blocksPlotTimeseries'] = eval(self.config.get('plot', 'blocksPlotTimeseries'))
        ret['variablesPlotTimeseries'] = eval(self.config.get('plot', 'variablesPlotTimeseries'))
        return ret
    
    def output2inifile(self, outfp):
        """ get logger """
        logger = define_logging.getLogger(
            f"{__class__.__name__}.{sys._getframe().f_code.co_name}")

        config = configparser.ConfigParser()
        config.add_section('configuration')
        config.add_section('toughInput')
        config.add_section('atmosphere')
        config.add_section('boundary')
        config.add_section('amesh_voronoi')
        config.add_section('mesh')
        config.add_section('plot')
        config.add_section('solver')
        config.set('configuration', 'TOUGH_INPUT_DIR', self.configuration.TOUGH_INPUT_DIR)
        
        # toughInput
        if hasattr(self, 'toughInput'):

            config.set('toughInput', 'generSecList', repr([]))
            config.set('toughInput', 'rockseclist', repr([]))
            config.set('toughInput', 'primary_sec_list', repr([]))
        
            def set1(self, config, key):
                if key in self.toughInput:
                    val = self.toughInput[key]
                    config.set('toughInput', key, val if type(val) is str else repr(val))
                else:
                    config.set('toughInput', key, '')
            
            keys = ['simulator','module','problemName','mulgridFileName',
                    'num_components','num_equations','num_phases','num_secondary_parameters',
                    'max_iterations','print_level','max_timesteps','max_duration','print_interval',
                    'MOPs01','MOPs02','MOPs03','MOPs04','MOPs05','MOPs06','MOPs07','MOPs08','MOPs09',
                    'MOPs10','MOPs11','MOPs12','MOPs13','MOPs14','MOPs15','MOPs16','MOPs17',
                    'texp','be','tstart','tstop','const_timestep','max_timestep','print_block',
                    'gravity','timestep_reduction','scale','relative_error','absolute_error',
                    'upstream_weight','newton_weight','derivative_increment','for','amres',
                    'problemNamePreviousRun','water_table_elevation','1d_hydrostatic_sim_result_ini',
                    'PRIMARY_default','PRIMARY_AIR','use_1d_result_as_incon',
                    'specifies_variable_INCON',
                    'seedFlg','crustalHeatFlowRate','rainfallAnnual_mm','T_rain','history_block',
                    'history_connection','prints_hc_surface','prints_hc_inj',
                    'selection_line1','selection_line2',
                    'num_times_specified','num_times','max_timestep_TIMES','time_increment','time',
                    'assignFocusHf','focusHfRate','focusHfRange']

            for key in keys:
                set1(self, config, key)


        # rocktypes
        if hasattr(self, 'rockSecList'):
            keys = ['name','nad','density','porosity','permeability_x','permeability_y',
                    'permeability_z','conductivity','specific_heat','blockList','nad',
                    'IRP','RP','ICP','CP', 'formula_porosity', 'formula_permeability',
                    'rock_assign_condition']

            rocksec_name_list = []
            for rock in self.rockSecList:
                rocksec_name_list.append(rock.name)
                config.add_section(rock.name)
                for key in keys:
                    if hasattr(rock, key):
                        val = eval(f'rock.{key}')
                        config.set(rock.name, key, val if type(val) is str else repr(val))
                    else:
                        config.set(rock.name, key, '')

                regsec_name_list = []
                for reg in rock.regionSecList:
                    regsec_name_list.append(reg.secName)
                    config.add_section(reg.secName)
                    config.set(reg.secName, 'xmin', repr(reg.xmin))
                    config.set(reg.secName, 'xmax', repr(reg.xmax))
                    config.set(reg.secName, 'ymin', repr(reg.ymin))
                    config.set(reg.secName, 'ymax', repr(reg.ymax))
                    config.set(reg.secName, 'zmin', repr(reg.zmin))
                    config.set(reg.secName, 'zmax', repr(reg.zmax))

                config.set(rock.name, 'regionSecList', repr(regsec_name_list))
        
            config.set('toughInput', 'rockSecList', repr(rocksec_name_list))


        # geners
        if hasattr(self, 'generSecList'):
            keys = ['name', 'block', 'type', 'flux', 'injectsIndirectly', 'temperature', 'area', 
                    'vol_injblock', 'dist_injblock', 
                    'ltab', 'time', 'flux_factor', 'itab', 'enthalpy_factor']
            genersec_name_list = []
            for gener in self.generSecList:
                genersec_name_list.append(gener.secName)
                config.add_section(gener.secName)
                for key in keys:
                    if hasattr(gener, key):
                        val = eval(f'gener.{key}')
                        config.set(gener.secName, key, val if type(val) is str else repr(val))
                    else:
                        config.set(gener.secName, key, '')
            config.set('toughInput', 'generSecList', repr(genersec_name_list))

        # primary_sec_list
        if hasattr(self, 'primary_sec_list'):
            primary_sec_list = []
            for psec in self.primary_sec_list:
                primary_sec_list.append(psec.secName)
                config.add_section(psec.secName)
                config.set(psec.secName, 'value', repr(psec.value))
                config.set(psec.secName, 'xmin', repr(psec.xmin))
                config.set(psec.secName, 'xmax', repr(psec.xmax))
                config.set(psec.secName, 'ymin', repr(psec.ymin))
                config.set(psec.secName, 'ymax', repr(psec.ymax))
                config.set(psec.secName, 'zmin', repr(psec.zmin))
                config.set(psec.secName, 'zmax', repr(psec.zmax))
            config.set('toughInput', 'primary_sec_list', repr(primary_sec_list))
                
        if hasattr(self, 'mesh'):
            keys = ['type', 'convention', 'isRadial', 'resistivity_structure_fp', 'mulgridFileFp']
            for key in keys:
                if hasattr(self.mesh, key):
                    val = eval(f'self.mesh.{key}')
                    config.set('mesh', key, val if type(val) is str else repr(val))
                else:
                    config.set('mesh', key, '')

            if hasattr(self.mesh, 'rblocks'):
                config.add_section('r')
                config.set('r', 'elem1', repr(self.mesh.rblocks))
                config.set('mesh', 'rblocksSec', 'r')
            if hasattr(self.mesh, 'xblocks'):
                config.add_section('x')
                config.set('x', 'elem1', repr(self.mesh.xblocks))
                config.set('mesh', 'xblocksSec', 'x')
            if hasattr(self.mesh, 'yblocks'):
                config.add_section('y')
                config.set('y', 'elem1', repr(self.mesh.yblocks))
                config.set('mesh', 'yblocksSec', 'y')
            if hasattr(self.mesh, 'zblocks'):
                config.add_section('z')
                config.set('z', 'elem1', repr(self.mesh.zblocks))
                config.set('mesh', 'zblocksSec', 'z')
            
            if hasattr(self.mesh, 'resistivity_structure_fp'):
                config.set('mesh', 'resistivity_structure_fp', create_relpath(self.mesh.resistivity_structure_fp))
            else:
                config.set('mesh', 'resistivity_structure_fp', '')


        if hasattr(self, 'amesh_voronoi'):
            keys = ['elevation_top_layer', 'layer_thicknesses', 'tolar', 'top_layer_min_thickness']
            for key in keys:
                if hasattr(self.amesh_voronoi, key):
                    val = eval(f'self.amesh_voronoi.{key}')
                    config.set('amesh_voronoi', key, val if type(val) is str else repr(val))
                else:
                    config.set('amesh_voronoi', key, '')
            
            if hasattr(self.amesh_voronoi, 'topodata_fp'):
                config.set('amesh_voronoi', 'topodata_fp', create_relpath(self.amesh_voronoi.topodata_fp))
            else:
                config.set('amesh_voronoi', 'topodata_fp', '')

            if hasattr(self.amesh_voronoi, 'voronoi_seeds_list_fp'):
                config.set('amesh_voronoi', 'voronoi_seeds_list_fp', create_relpath(self.amesh_voronoi.voronoi_seeds_list_fp))
            else:
                config.set('amesh_voronoi', 'voronoi_seeds_list_fp', '')


        if hasattr(self, 'plot'):
            keys = ['slice_plot_limits', 'slice_plot_variables_T2', 'slice_plot_variables_T3', 'xoft_t_range',
                    'gif_minimun_print_interval_sec', 'columns_incon_plot', 'reads_data_from_current_dir']
            for key in keys:
                if hasattr(self.plot, key):
                    val = eval(f'self.plot.{key}')
                    config.set('plot', key, val if type(val) is str else repr(val))
                else:
                    config.set('plot', key, '')
            
            if hasattr(self.plot, 'profile_lines_list'):
                tmp = []
                for i, line in enumerate(self.plot.profile_lines_list):
                    if isinstance(line, np.ndarray): 
                        # np.ndarrayを文字列に変換するとおかしくなるのでlistに戻す
                        tmp.append([list(line[0]), list(line[1])])
                    else: 
                        tmp.append(line)
                config.set('plot', 'profile_lines_list', repr(tmp))

        if hasattr(self, 'boundary'):
            keys = ['boundary_side_permeable']
            for key in keys:
                if hasattr(self.boundary, key):
                    val = eval(f'self.boundary.{key}')
                    config.set('boundary', key, val if type(val) is str else repr(val))
                else:
                    config.set('boundary', key, '')
        

        if hasattr(self, 'atmosphere'):
            keys = ['PRIMARY_AIR','includesAtmos']
            for key in keys:
                if hasattr(self.atmosphere, key):
                    val = eval(f'self.atmosphere.{key}')
                    config.set('atmosphere', key, val if type(val) is str else repr(val))
                else:
                    config.set('atmosphere', key, '')

            if hasattr(self.atmosphere, 'atmos'):
                config.set('atmosphere', 'name', self.atmosphere.atmos.name)
                config.set('atmosphere', 'nad', str(self.atmosphere.atmos.nad))
                config.set('atmosphere', 'density', str(self.atmosphere.atmos.density))
                config.set('atmosphere', 'porosity', str(self.atmosphere.atmos.porosity))
                config.set('atmosphere', 'permeability', repr(list(self.atmosphere.atmos.permeability)))
                config.set('atmosphere', 'conductivity', str(self.atmosphere.atmos.conductivity))
                config.set('atmosphere', 'specific_heat', str(self.atmosphere.atmos.specific_heat))
                config.set('atmosphere', 'tortuosity', str(self.atmosphere.atmos.tortuosity))
                if 'type' in self.atmosphere.atmos.relative_permeability:
                    config.set('atmosphere', 'IRP', str(self.atmosphere.atmos.relative_permeability['type']))
                if 'parameters' in self.atmosphere.atmos.relative_permeability:
                    config.set('atmosphere', 'RP', repr(self.atmosphere.atmos.relative_permeability['parameters']))
                if 'type' in self.atmosphere.atmos.capillarity:
                    config.set('atmosphere', 'ICP', str(self.atmosphere.atmos.capillarity['type']))
                if 'parameters' in self.atmosphere.atmos.capillarity:
                    config.set('atmosphere', 'CP', repr(self.atmosphere.atmos.capillarity['parameters']))
        
        if hasattr(self, 'solver'):
            keys = ['matslv', 'nProc', 'ksp_type', 'pc_type', 'ksp_rtol', 'ZPROCS', 'OPROCS', 'RITMAX', 'CLOSUR']
            for key in keys:
                if hasattr(self.solver, key):
                    val = eval(f'self.solver.{key}')
                    config.set('solver', key, val if type(val) is str else repr(val))
                else:
                    config.set('solver', key, '')
    
        with open(outfp, 'w') as f:
            config.write(f)

        

if __name__ == '__main__':
    pass