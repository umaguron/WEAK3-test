"""
All constants should be defined in this file 
to avoid messing up the codes with magic numbers or magic constants.
"""

"""user-defined exception"""
class InvalidToughInputException(Exception):
    pass
# class Convention_ga_0_de_seeds_ga_945_yori_ooi_kara_amesh_de_error_ni_naruyo(Exception):
#     pass
class SurfaceElevationLowerThanBottomLayerException(Exception):
    pass


"""file name"""
FILENAME_T2DATA = 't2data.dat'
FILENAME_TOUGH_OUTPUT = 'output.listing'
FILENAME_RESULT_VTU = 'result.vtu'
FILENAME_GRIDVTK = 'grid.vtu'

INCON_FILE_NAME = 'INCON'
SAVE_FILE_NAME = 'SAVE'
OUTPUT_ELEME_CSV_FILE_NAME = 'OUTPUT_ELEME.csv'
OUTPUT_CONNE_CSV_FILE_NAME = 'OUTPUT_CONNE.csv'

FILENAME_TMP_MULGRAPH_NO_TOPO = 'mesh_no_topography.geo'

# for visualization of permeability and original resistivity structures
PICKLED_MULGRID_RES = 'mulgrid_resistivity.npy'
PICKLED_MULGRID_PERM = 'mulgrid_permeability.npy'
PICKLED_INPUTINI = 'InputIni.pickle'

"""dir names """
# dir. path from TOUGH_INPUT_DIR
T3OUT_ESCAPE_DIRNAME = '0t3out'
# dir. path from TOUGH_INPUT_DIR
SAVEFIG_DIRNAME = '0fig'


"""name of image files"""
IMG_LAYER_SURFACE = 'layer_surface'
IMG_PERM_SLICE_X = 'permeability_slice-x'
IMG_PERM_SLICE_Y = 'permeability_slice-y'
IMG_PERM_SLICE_Z = 'permeability_slice-z'
IMG_PERM_SLICE_LINE = 'permeability_slice-line'
IMG_PERM_LAYER = 'permeability_layer-'
IMG_RESIS_SLICE_X = 'resistivity_slice-x'
IMG_RESIS_SLICE_Y = 'resistivity_slice-y'
IMG_RESIS_SLICE_Z = 'resistivity_slice-z'
IMG_RESIS_SLICE_LINE = 'resistivity_slice-line'
IMG_RESIS_LAYER = 'resistivity_layer-'
IMG_TOPO = 'topo'
IMG_INCON = lambda index: f'incon{index}_slice-line'

"""PyTOUGH"""
ATM_BLK_NAME = lambda convention: ['ATM 0', 'atm 0', 'at  0'][convention]
REGEX_FIXED_P_ADDED_CELL_NAME = lambda convention: [
        '[zZ][A-z][A-z][ 0-9][ 0-9]',
        '[zZ][A-z][A-z][ 0-9][ 0-9]',
        '[ A-z][ A-z]999',
    ][convention]

"""log"""
FILEPATH_LOG = "log.log"
import logging
LOG_LEVEL_STREAM = logging.WARNING  
LOG_LEVEL_FILE = logging.WARNING
FORMAT_LOG_STREAM = '[%(levelname)s] %(name)s - %(message)s'
FORMAT_LOG_FILE = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


"""[toughInput]"""
SIMULATOR_NAME_T3 = "TOUGH3"
SIMULATOR_NAME_T3_LOCAL = "TOUGH3_LOCAL"
SIMULATOR_NAME_T2 = "TOUGH2"
FIXED_P_REGION_TYPE_SINGLE_P_CELL = 'SINGLE_P_CELL'
FIXED_P_REGION_TYPE_MULTI_P_CELL  = 'MULTI_P_CELL'
FIXED_P_REGION_PRESS_TYPE_XSTATIC  = 'DENS'
FIXED_P_REGION_PRESS_TYPE_OVER_P_RATIO  = 'OVER_P'
FIXED_P_REGION_PRESS_TYPE_NUM  = 'NUM'

"""[amesh_voronoi]"""
TOP_LAYER_MIN_THICKNESS_DEFAULT = 5
"""[mesh]"""
# type
REGULAR = "REGULAR"
AMESH_VORONOI = "A_VORO"
"""[sea]"""
SEA_PRIMARY_XCOM_DEFAULT = 0
"""[plot]"""
PROFILE_LINES_LIST_DEFAULT = ['x']
FONT_SIZE = 15

""" Miscellaneous keywords or values"""
KW_LITHOS = "lithos"
KW_HYDRST = "hydrst"

# resistivity of host rock used in the calculation of HS bounds
HOSTROCK_RESISTIVITY = 100

# String used to determine whether or not to output the section view.
FLAG_NAME_RES = 'RES'
FLAG_NAME_FLOW = 'FLOW'
FLAG_NAME_HEAT = 'HEAT'

# The appropriate cbar is selected in the t2outUtil.get_cbar_limit method based on the FLAG NAME.
CBAR_LIM_NaCl_CONTENT = [0, 0.02]
CBAR_LIM_LOG10RES = [-0.5,3.5]
CBAR_LIM_LOG10PERM = [-10,-20]
CBAR_LIM = {
    'TEMP': [0,300],
    'SAT_G': [0, 0.5],
    'SAT_L': [0, 1],
    'PRES': None,
    'SAT_S': None,
    'X_WATER_G': None,
    'X_NaCl_G': None,
    'X_CO2_G': None,
    'X_WATER_L': None,
    'X_NaCl_L': [0, 0.04],
    'X_CO2_L': None,
    'REL_G': None,
    'REL_L': None,
    'PCAP_GL': None,
    'DEN_G': None,
    'DEN_L': None,
    'POR': None,
}

# The appropriate unit name is selected in the t2outUtil.get_unit method based on the FLAG NAME.
UNIT = {
    FLAG_NAME_RES: 'ohm-m',
    'TEMP': 'C',
    'SAT_G': None,
    'SAT_L': None,
    'PRES': 'Pa',
    'SAT_S': None,
    'X_WATER_G': None,
    'X_NaCl_G': None,
    'X_CO2_G': None,
    'X_WATER_L': None,
    'X_NaCl_L': None,
    'X_CO2_L': None,
    'REL_G': None,
    'REL_L': None,
    'PCAP_GL': None,
    'DEN_G': None,
    'DEN_L': None,
    'POR': None,
}

# The appropriate contour interbals is selected in the t2outUtil.get_contour_intbal method based on the FLAG NAME.
CONTOUR_POS = {
    FLAG_NAME_RES: False, # log10
    'TEMP': [25,50,100,150,200,250,290,300],
    'SAT_G': [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
    'SAT_L': False,
    'PRES': False,
    'SAT_S': False,
    'X_WATER_G': False,
    'X_NaCl_G': False,
    'X_CO2_G': False,
    'X_WATER_L': False,
    'X_NaCl_L': False,
    'X_CO2_L': False,
    'REL_G': False,
    'REL_L': False,
    'PCAP_GL': False,
    'DEN_G': False,
    'DEN_L': False,
    'POR': False,
}

"""figure"""
CMAP_PERMEABILITY = "gist_rainbow"
CMAP_RESISTIVITY = "gist_rainbow"

# CBARLIMIT_DEFAULT_HEAT = [-0.5, 1]
# CBARLIMIT_DEFAULT_HEAT = [-0.69, 7.21]
CBARLIMIT_DEFAULT_HEAT = None
# CBARLIMIT_DEFAULT_FLOW = [-1e-5, 1e-5]
#CBARLIMIT_DEFAULT_FLOW = [-0.515e-5, 1.825e-5]
# CBARLIMIT_DEFAULT_FLOW = [-0.515e-5, 2.2e-5]
CBARLIMIT_DEFAULT_FLOW = None

TOPO_MAP_SYMBOL = {'Yugama':(2286,-62),
                   'sessho': (459, 2255),
                   'jofu': (2317, 2775),
                   'manza': (2136, -2340),
                   'oku-manza': (1234, -1498),
                   'bandaiko': (-111, 3464)}

"""module name"""
EOS2 = "eos2"
EOS3 = "eos3"
ECO2N = "eco2n"
ECO2N_V2 = "eco2n_v2"
EWASG = "ewasg"

"""incon variable index"""
INCON_ID_EOS2_PRES = 0
INCON_ID_EOS2_TEMP = 1
INCON_ID_EOS2_XCO2 = 2
INCON_ID_EOS3_PRES = 0
INCON_ID_EOS3_XAIR = 1
INCON_ID_EOS3_TEMP = 2
INCON_ID_ECO2N_PRES = 0
INCON_ID_ECO2N_XSAL = 1
INCON_ID_ECO2N_XCO2 = 2
INCON_ID_ECO2N_TEMP = 3
INCON_ID_EWASG_PRES = 0
INCON_ID_EWASG_XSAL = 1
INCON_ID_EWASG_XNCG = 2
INCON_ID_EWASG_TEMP = 3


"""CONST"""
HUGE_VOLUME = 1e40
HUGE_SPECIFIC_HEAT = 1e20
BOUND_BLK_CONN_DISTANCE = 100
M_OVER_KM = 1000
WATER_DENSITY = 998.
OVERBURDEN_DENSITY = 2500.
GRAV_ACCEL = 9.80665
ATMOS_PRESSURE = 1.013e5


"""Database"""
LOG_DB_PATH = 'log.db'


"""surface area list for plotting surface flow timeseries"""
"""[centre_x, centre_y, radius]"""
# COFT_TS_AREAS ={
#     'ALL':[0,0,99999],  
#     'Yugama+1000':[2286,-62,1000], 
#     'Yugama+2000':[2286,-62,2000],
#     'Yugama+3000':[2286,-62,3000],
#     'Manza+1000':[2136,-2340,1000], 
#     'Manza+1500':[2136,-2340,1500], 
#     'East+5000':[1000,5000,5000], 
#     'West+5000':[1000,-5000,5000], 
# }
COFT_TS_AREAS ={
    'ALL':[0,0,99999],
}

"""matplotlib"""
INCH_OVER_CM = 1/2.54


"""tough3 ending message"""
CONSECUTIVE_10 = "FOR 10 CONSECUTIVE TIME STEPS HAVE CONVERGENCE ON ITER = 1"
FOLLOWING_TWO = "FOLLOWING TWO STEPS THAT CONVERGED ON ITER = 1"
NO_CONVERGENCE = "NO CONVERGENCE AFTER"
PETSC_FAIL = "PETSC Solver failed to converged"
SIM_END = "END OF TOUGH3 SIMULATION RUN"


"""file path"""
DIR_SURFACE_FLOW_AREA_TABLE = "surflow_table"


"""suffix of surflow_table csv file """
SUF_SURFLOW_NET = "_net"
SUF_SURFLOW_DIRC1 = "_dirc1"
SUF_SURFLOW_DIRC2 = "_dirc2"


"""Command to be executed immediately before the TOUGH execution in run.py"""
COMM_BF_EXEC = """
module purge
export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH"""