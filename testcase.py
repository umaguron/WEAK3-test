import unittest
import _readConfig
import os 
from define_path import *
import tough3exec_ws
from t2incons import *
from define import *
import makeGridFunc

class TestInputIniVariableINCON(unittest.TestCase):

    def setUp(self):
        self.ini = _readConfig.InputIni().read_from_inifile('for_testcase/shirane_vic_N325_test_primSec.ini')
        self.ini_no_vprm = _readConfig.InputIni().read_from_inifile('for_testcase/shirane_vic_N325.ini')
        
    def test_variable_INCON(self):
        self.assertEqual(self.ini.primary_sec_list[0].secName, "prm_sec1")
        self.assertEqual(self.ini.primary_sec_list[1].secName, "prm_sec2")
        self.assertEqual(self.ini.primary_sec_list[2].secName, "prm_sec3")
        self.assertEqual(self.ini.primary_sec_list[0].variables, [None, 0.11, 0.01, 200])
        self.assertEqual(self.ini.primary_sec_list[1].variables, ['lithos', 0.22, 0.02, None])
        self.assertEqual(self.ini.primary_sec_list[2].variables, [3e7, 0.33, 0.03, 40])
        self.assertEqual(self.ini.primary_sec_list[0].assigning_condition, "z >3000")
        self.assertEqual(self.ini.primary_sec_list[2].assigning_condition, "z < 1100")
        self.assertEqual(self.ini.primary_sec_list[0].blockList, ['  a 9', ' aa25'])
        self.assertEqual(self.ini.primary_sec_list[1].blockList, [])

        # tough3exec_ws.makeToughInput(self.ini)
        # tough3exec_ws.makeToughInput(self.ini_no_vprm)

        inc = t2incon(self.ini.inconFp)
        inc_no_vprm = t2incon(self.ini_no_vprm.inconFp)
        self.assertEqual(inc['  a 9'].variable[0],inc_no_vprm['  a 9'].variable[0])
        self.assertEqual(inc['  a 9'].variable[1],0.11)
        self.assertEqual(inc['  a 9'].variable[2],0.01)
        self.assertEqual(inc['  a 9'].variable[3],200)
        self.assertNotEqual(inc['  a 9'].variable[1],inc_no_vprm['  a 9'].variable[1])
        self.assertNotEqual(inc['  a23'].variable[0],inc_no_vprm['  a23'].variable[0])
        self.assertGreater(inc['  a23'].variable[0],inc_no_vprm['  a23'].variable[0])
        self.assertEqual(inc['  a23'].variable[3],inc_no_vprm['  a23'].variable[3])
        self.assertNotEqual(inc['  a25'].variable[3],inc_no_vprm['  a25'].variable[3])
        self.assertEqual(inc['  a25'].variable[3],40)
        self.assertEqual(inc['  a25'].variable[0],3e7)
        self.assertEqual(inc['  a25'].variable[1],0.33)
        self.assertEqual(inc['  a25'].variable[2],0.03)

    def tearDown(self):
        pass

class TestInputIniMesh2dCone(unittest.TestCase):

    def setUp(self):
        self.ini_ConeFlexible = _readConfig.InputIni().read_from_inifile('for_testcase/TestInputIniMesh2dCone_ConeFlexible.ini')
        self.ini_ConeSimple = _readConfig.InputIni().read_from_inifile('for_testcase/TestInputIniMesh2dCone_ConeSimple.ini')
        self.ini_noCone = _readConfig.InputIni().read_from_inifile('for_testcase/TestInputIniMesh2dCone_noCone.ini')
        self.ini_SeaDefault = _readConfig.InputIni().read_from_inifile('for_testcase/TestInputIniMesh2dCone_SeaDefault.ini')
        self.ini_SeaDefault1 = _readConfig.InputIni().read_from_inifile('for_testcase/TestInputIniMesh2dCone_SeaDefault1.ini')
        
    def test_variable_INCON(self):
        self.assertRaises(InvalidToughInputException, _readConfig.InputIni().read_from_inifile, 'for_testcase/TestInputIniMesh2dCone_ConeInvalid.ini')
        self.assertRaises(InvalidToughInputException, _readConfig.InputIni().read_from_inifile, 'for_testcase/TestInputIniMesh2dCone_ConeInvalid1.ini')
        self.assertRaises(InvalidToughInputException, _readConfig.InputIni().read_from_inifile, 'for_testcase/TestInputIniMesh2dCone_ConeInvalid2.ini')
        self.assertRaises(Exception, _readConfig.InputIni().read_from_inifile, 'for_testcase/TestInputIniMesh2dCone_SeaInvalid1.ini')
        self.assertFalse(self.ini_ConeFlexible.mesh.isSimpleCone)
        self.assertTrue(self.ini_ConeSimple.mesh.isSimpleCone)
        self.assertFalse(self.ini_ConeFlexible.mesh.isSimpleCone)
        self.assertFalse(hasattr(self.ini_noCone, 'isSimpleCone'))
        self.assertEqual(self.ini_ConeSimple.mesh.cone_top_elevation, 1000)
        self.assertFalse(hasattr(self.ini_noCone.mesh, 'cone_top_elevation'))
        self.assertFalse(hasattr(self.ini_noCone.mesh, 'cone_base_radius'))
        self.assertFalse(hasattr(self.ini_noCone.mesh, 'cone_height_above_base'))
        self.assertFalse(hasattr(self.ini_noCone.mesh, 'cone_shape_elev'))
        self.assertFalse(hasattr(self.ini_noCone.mesh, 'cone_shape_r'))
        self.assertEqual(self.ini_ConeSimple.mesh.cone_top_elevation, 1000)
        self.assertEqual(self.ini_ConeSimple.mesh.cone_base_radius, 5000)
        self.assertEqual(self.ini_ConeSimple.mesh.cone_height_above_base, 1000)
        self.assertFalse(hasattr(self.ini_ConeSimple.mesh, 'cone_shape_elev'))
        self.assertFalse(hasattr(self.ini_ConeSimple.mesh, 'cone_shape_r'))
        self.assertEqual(self.ini_ConeFlexible.mesh.cone_shape_elev, [1000, 0])
        self.assertEqual(self.ini_ConeFlexible.mesh.cone_shape_r, [0, 5000])
        self.assertFalse(hasattr(self.ini_ConeFlexible.mesh, 'cone_base_radius'))
        self.assertFalse(hasattr(self.ini_ConeFlexible.mesh, 'cone_top_elevation'))
        self.assertFalse(hasattr(self.ini_ConeFlexible.mesh, 'cone_height_above_base'))
        self.assertEqual(self.ini_SeaDefault1.sea.primary_xcom, 0.1)
        self.assertEqual(self.ini_SeaDefault.sea.primary_xcom, SEA_PRIMARY_XCOM_DEFAULT)
        
        self.ini_ConeFlexible.output2inifile('for_testcase/tmp/ConeFlexible.ini')
        ini2_ConeFlexible = _readConfig.InputIni().read_from_inifile('for_testcase/tmp/ConeFlexible.ini')
        self.assertEqual(ini2_ConeFlexible.mesh.cone_shape_elev, [1000, 0])
        self.assertEqual(ini2_ConeFlexible.mesh.cone_shape_r, [0, 5000])
        makeGridFunc.makeGrid(ini2_ConeFlexible, overWrites=True)
        tough3exec_ws.makeToughInput(ini2_ConeFlexible)

        self.ini_ConeSimple.output2inifile('for_testcase/tmp/ConeSimple.ini')
        ini2_ConeSimple = _readConfig.InputIni().read_from_inifile('for_testcase/tmp/ConeSimple.ini')
        self.assertEqual(ini2_ConeSimple.mesh.cone_top_elevation, 1000)
        self.assertEqual(ini2_ConeSimple.mesh.cone_base_radius, 5000)
        self.assertEqual(ini2_ConeSimple.mesh.cone_height_above_base, 1000)
        makeGridFunc.makeGrid(ini2_ConeSimple, overWrites=True)
        tough3exec_ws.makeToughInput(ini2_ConeSimple)

        self.ini_noCone.output2inifile('for_testcase/tmp/noCone.ini')
        ini2_noCone = _readConfig.InputIni().read_from_inifile('for_testcase/tmp/noCone.ini')
        makeGridFunc.makeGrid(ini2_noCone, overWrites=True)
        tough3exec_ws.makeToughInput(ini2_noCone)

        self.ini_SeaDefault.output2inifile('for_testcase/tmp/SeaDefault.ini')
        ini2_SeaDefault = _readConfig.InputIni().read_from_inifile('for_testcase/tmp/SeaDefault.ini')
        self.assertEqual(ini2_SeaDefault.sea.closeness_to_seawater_blk, 0.01)
        self.assertEqual(ini2_SeaDefault.sea.sea_level, 0)
        self.assertEqual(ini2_SeaDefault.sea.primary_xcom, SEA_PRIMARY_XCOM_DEFAULT)
        makeGridFunc.makeGrid(ini2_SeaDefault, overWrites=True)
        tough3exec_ws.makeToughInput(ini2_SeaDefault)

        self.ini_SeaDefault1.output2inifile('for_testcase/tmp/SeaDefault1.ini')
        ini2_SeaDefault1 = _readConfig.InputIni().read_from_inifile('for_testcase/tmp/SeaDefault1.ini')
        self.assertEqual(ini2_SeaDefault1.sea.closeness_to_seawater_blk, 0.01)
        self.assertEqual(ini2_SeaDefault1.sea.sea_level, 0)
        self.assertEqual(ini2_SeaDefault1.sea.primary_xcom, 0.1)
        makeGridFunc.makeGrid(ini2_SeaDefault1, overWrites=True)
        tough3exec_ws.makeToughInput(ini2_SeaDefault1)

    def tearDown(self):
        pass

class TestInputUsesAmesh(unittest.TestCase):
    def setUp(self):
        self.ini_T = _readConfig.InputIni().read_from_inifile('for_testcase/shirane_vic_N325_uses_amesh_T.ini')
        self.ini_F = _readConfig.InputIni().read_from_inifile('for_testcase/shirane_vic_N325_uses_amesh_F.ini')

    def test_variable_INCON(self):
        self.ini_T.output2inifile('for_testcase/tmp/shirane_vic_N325_uses_amesh_T.ini')
        ini2_T = _readConfig.InputIni().read_from_inifile('for_testcase/tmp/shirane_vic_N325_uses_amesh_T.ini')
        self.assertTrue(ini2_T.amesh_voronoi.uses_amesh)
        os.makedirs(ini2_T.t2FileDirFp, exist_ok=True)
        makeGridFunc.makeGrid(ini2_T, overWrites=True)
        tough3exec_ws.makeToughInput(ini2_T)

        self.ini_F.output2inifile('for_testcase/tmp/shirane_vic_N325_uses_amesh_F.ini')
        ini2_F = _readConfig.InputIni().read_from_inifile('for_testcase/tmp/shirane_vic_N325_uses_amesh_F.ini')
        self.assertFalse(ini2_F.amesh_voronoi.uses_amesh)
        os.makedirs(ini2_F.t2FileDirFp, exist_ok=True)
        makeGridFunc.makeGrid(ini2_F, overWrites=True)
        tough3exec_ws.makeToughInput(ini2_F)


    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()