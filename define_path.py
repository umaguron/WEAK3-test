"""
All environment dependent path should be defined here.
"""

"""library location"""
PYTOUGH_ROOT_PATH = "lib/PyTOUGH-master"
IAPWS_ROOT_PATH = "lib/iapws"

"""AMESH"""
# location of AMESH_PROG
AMESH_DIR = "amesh/Source/"
# name of executable
AMESH_PROG = "amesh"
# Do not change
AMESH_INPUT_FILENAME = "in"
# Do not change
AMESH_SEGMT_FILENAME = "segmt"

"""TOUGH3 executable location"""
# TOUGH3 
BIN_DIR = "/home/matsunaga/Tough3/bin/"
# TOUGH2
BIN_DIR_T2 = "/home/matsunaga/Tough2/Source_Core/"
# another TOUGH3 
BIN_DIR_LOCAL = "/Users/matsunagakousei/sourceCodes/TOUGH3_source/TOUGH3v1.0/Mac_executables/bin"

"""executable name"""
# filename of executable in BIN_DIR
EXEC_FILENAME = {
    'eco2n_v2': "tough3-eco2n_v2",
    'eos2': "tough3-eos2",
    "eos3": "tough3-eos3",
    "eco2n": "tough3-eco2n",
    "ewasg": "tough3-ewasg",
}
# filename of executable in BIN_DIR_T2
EXEC_FILENAME_T2 = {
    'eos2': "xt2_eos2"
}
# filename of executable in BIN_DIR_LOCAL
EXEC_FILENAME_LOCAL = EXEC_FILENAME

"""MPICH for parallel execution"""
MPIEXEC = "/usr/local/bin/mpiexec"

