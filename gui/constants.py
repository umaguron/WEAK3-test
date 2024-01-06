import os 
import sys
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
sys.path.append(baseDir)
sys.path.append(os.path.join(baseDir,".."))
projRoot = os.path.abspath(os.path.join(baseDir,".."))
import define

class Const(object):
    """テンプレートで利用する定数を定義する"""
    # constant 
    ROCKTYPE_LEN = 6

    
    # validation and message
    PATTERN = {}
    TITLE = {}

    PATTERN['int'] = "[\+\-]?\d+"
    TITLE['int'] = "[0-9]+"

    PATTERN['float'] = "([\+\-]?\d*\.?\d*|[\+\-]?\d*\.?\d*[eE][\+\-]?\d+)"
    PATTERN['float_in_js'] = "([\\\-]?\\\d*\\\.?\\\d*|[\\\-]?\\\d*\\\.?\\\d*[eE][\\\+\\\-]?\\\d+)"
    TITLE['float'] = "数値を入力(e.g., 1.0, 1.5e+04)"

    PATTERN['float_none_ok'] = "([\+\-]?\d*\.?\d*|[\+\-]?\d*\.?\d*[eE][\+\-]?\d+|None *)"
    TITLE['float_none_ok'] = "数値を入力(e.g., 1.0, 1.5e+04)"

    PATTERN['float_extended'] = "([\+\-]?\d*\.?\d*|[\+\-]?\d*\.?\d*[eE][\+\-]?\d+|((\d*\.?\d*|\d*\.?\d*[eE][\+\-]?\d+)\*)+(\d*\.?\d*|\d*\.?\d*[eE][\+\-]?\d+))"
    TITLE['float_extended'] = "数値を入力(e.g., 1.0, 1.5e+04)"
    
    PATTERN['list'] = "\[ *((\S*) *, *)*(\S*) *,? *\]"
    PATTERN['list_in_js'] = "\\\[ *((\\\S*) *, *)*(\\\S*) *,? *\\\]"
    TITLE['list'] = "リスト形式(e.g., [XX, XX, ... ])"

    PATTERN['numlist'] = "\[ *((([\+\-]?\d*\.?\d*|[\+\-]?\d*\.?\d*[eE][\+\-]?\d+)) *, *)*(([\+\-]?\d*\.?\d*|[\+\-]?\d*\.?\d*[eE][\+\-]?\d+)) *,? *\]"
    PATTERN['numlist_in_js'] = "\\\[ *((([\\\+\\\-]?\\\d*\\\.?\\\d*|[\\\+\\\-]?\\\d*\\\.?\\\d*[eE][\\\+\\\-]?\\\d+)) *, *)*(([\\\+\\\-]?\\\d*\\\.?\\\d*|[\\\+\\\-]?\\\d*\\\.?\\\d*[eE][\\\+\\\-]?\\\d+)) *,? *\\\]"
    TITLE['numlist'] = "数値のリスト(e.g., [1.013e+5, 0.001, ... ])"
    
    PATTERN['blklist'] = "\[( *['\"][ A-z0-9]{5}['\"] *,)* *['\"][ A-z0-9]{5}['\"] *,? *\]"
    PATTERN['blklist_in_js'] = "\\\[( *['\\\"][ A-z0-9]{5}['\\\"] *,)* *['\\\"][ A-z0-9]{5}['\\\"] *,? *\\\]"
    TITLE['blklist'] = "ブロック名(5文字)のリスト(e.g., ['  a 1', 'bcd23', ... ])"
    
    PATTERN['blklist_len0_ok'] = "\[( *['\"][ A-z0-9]{5}['\"] *,? *)*\]"
    TITLE['blklist_len0_ok'] = "ブロック名(5文字)のリスト(e.g., ['  a 1', 'bcd23', ... ])"

    PATTERN['tuplelist'] = "\[([\[\(] *(['\"][ A-z0-9]{5}['\"]) *, *(['\"][ A-z0-9]{5}['\"]) *[\]\)] *,? *)*\]"
    TITLE['tuplelist'] = "ブロック名(5文字)の組 のリスト(e.g., [('  a 1', '  b 1'), (... ])"
    
    PATTERN['blkname'] = "[ A-z0-9]{1,5}"
    TITLE['blkname'] = "ブロック名(5文字以内)"
    
    PATTERN['plot_line'] = ".*"
    TITLE['plot_line'] = ""

    PATTERN['simple_list'] = " *\[.*\] *"
    TITLE['simple_list'] = ""

    # define.pyの中身をそのまま使いたい
    DEFINE = define

    # if True, a link of 'topodata_fp' (cmesh2, Create new mulgrid file) is created in base directory (TOUGH_INPUT_DIR)
    DUPLICATES_ORG_TOPO = False
    # if True, a copy of 'voronoi_seeds_list_fp' (cmesh2, Create new mulgrid file) is created in base directory (TOUGH_INPUT_DIR)
    DUPLICATES_ORG_SEEDS = True
    # if True, a link of 'Resistivity structure data' (cmesh3) is created in base directory (TOUGH_INPUT_DIR)
    DUPLICATES_ORG_RESMODEL = False
    # if True, a copy of 'existing mulgrid file' (cmesh2, Use existing mulgrid file) is created in base directory (TOUGH_INPUT_DIR)
    DUPLICATES_ORG_MULGRID = True

    

