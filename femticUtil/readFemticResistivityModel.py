# -*- coding: utf-8 -*-
"""
Created on Feb 8 2023
@author: y. matsunaga
"""
import os, sqlite3
import subprocess
import argparse
import pathlib
baseDir = pathlib.Path(__file__).parent.resolve()
FP_DATABASE = os.path.join(baseDir, 'tmpfileData.db')

def main():

    ## get argument
    parser = argparse.ArgumentParser()
    parser.add_argument("ResistivityBlockIterDat", 
            help="filepath of resistivity_block_iter[Iter#].dat", type=str)
    parser.add_argument("MeshDat", 
            help="filepath of mesh.dat", type=str)
    parser.add_argument("-r","--resistivity_threshold", 
            help="if given, cells with resistivity greater than this value will not be written to the output file", type=float)
    args = parser.parse_args()

    db = DB_CellElementNodeRelation(args.MeshDat, args.ResistivityBlockIterDat, FP_DATABASE)
    db.restore()
    db.outputAsXYZRho('femticUtil/cellCenterResistivity.txt', 
                      resistivity_threshold=args.resistivity_threshold)


class DB_CellElementNodeRelation(object):
    """
    
    Attributes
    ----------
    fpResistivityBlockIter str
        complete file path of resistivity_block_iter[#].dat
    fpMeshDat str
        complete file path of mesh.dat
    fpBb str
        complete file path of db
    fp3rdBlockTemp str
        complete path where 3rd block of mesh.dat is saved
    nElem
        number of elements read from resistivit_block_iter[#].dat
    nCell
        number of elements read from resistivit_block_iter[#].dat        
    """
     
    
    def __init__(self, fpMeshDat, fpResistivityBlockIter, fpDb):

        # fixed value        
        # specified in baseDir/outputResistivityBlockIter.sql
        self.baseDir = os.path.dirname(__file__)
        self.fpDdl1 = os.path.join(self.baseDir, 'ddl.sql')
        self.fpDdl2 = os.path.join(self.baseDir, 'createViewCellRange.sql')
        self.fpDdl3 = os.path.join(self.baseDir, 'InsertIntoCellRange.sql')
        self.fpTmpCellGroupResistivity = os.path.join(self.baseDir, 'temporary/cellGroupResistivity.txt')
        self.fpTmpelementCellGroup = os.path.join(self.baseDir, 'temporary/elementCellGroup.txt')
        self.fpOutputShellScript = os.path.join(self.baseDir, 'outputResistivityBlockIter.sh')

        # file path to be read
        self.fpMeshDat = fpMeshDat
        self.fpResistivityBlockIter = fpResistivityBlockIter
        self.fpDb = fpDb
        #self.fp3rdBlockTemp = fpMeshDat + ".3rd"
        
        # read number of element & cell 
        with open(fpResistivityBlockIter, 'r') as f:
            tmp=f.readline().split()
            self.nElem = int(tmp[0])
            self.nCell = int(tmp[1])
    

    def restore(self):
        """
        read mesh.dat & resistivity_block_iter[#].dat
        and restore to DB (sqlite3)

        Returns
        -------
        None.

        """
    
        # new db file create 
        # remove old db
        try :
             os.remove(self.fpDb)
             print("old db deleted")
        except:
            pass
        
        # create new db
        # create tables
        subprocess.Popen(
            f"sqlite3 {self.fpDb} < {self.fpDdl1} 1>> log 2>> log", 
            shell=True, 
            stdin  = subprocess.PIPE, 
            stdout = subprocess.PIPE, 
            stderr = subprocess.PIPE)
            
        # restore files of femtic to db
        self._restoreResistivityBlockIter(self.fpResistivityBlockIter)
        self._restoreMeshDat(self.fpMeshDat) 
        
        
        # 要素を構成する4つのノードの座標と比抵抗をまとめたtableを作成する
        # insert data into table elementNodePosWithResistivity
        print("inserting data into table elementNodePosWithResistivity ...")
        conn = sqlite3.connect(self.fpDb)
        c = conn.cursor()

        c.executescript("""
INSERT INTO elementNodePosWithResistivity
SELECT en.elementId, B.cellId, B.resistivity, 
    (SELECT 
      posx
     FROM nodePos 
     WHERE nodeId IN (SELECT node0Id FROM elementNode WHERE elementid = en.elementId) 
    ) node0posx,
    (SELECT 
      posy
     FROM nodePos 
     WHERE nodeId IN (SELECT node0Id FROM elementNode WHERE elementid = en.elementId) 
    ) node0posy,
    (SELECT 
      posz
     FROM nodePos 
     WHERE nodeId IN (SELECT node0Id FROM elementNode WHERE elementid = en.elementId) 
    ) node0posz,
    (SELECT 
      posx
     FROM nodePos 
     WHERE nodeId IN (SELECT node1Id FROM elementNode WHERE elementid = en.elementId) 
    ) node1posx,
    (SELECT 
      posy
     FROM nodePos 
     WHERE nodeId IN (SELECT node1Id FROM elementNode WHERE elementid = en.elementId) 
    ) node1posy,
    (SELECT 
      posz
     FROM nodePos 
     WHERE nodeId IN (SELECT node1Id FROM elementNode WHERE elementid = en.elementId) 
    ) node1posz,
    (SELECT 
      posx
     FROM nodePos 
     WHERE nodeId IN (SELECT node2Id FROM elementNode WHERE elementid = en.elementId) 
    ) node2posx,
    (SELECT 
      posy
     FROM nodePos 
     WHERE nodeId IN (SELECT node2Id FROM elementNode WHERE elementid = en.elementId) 
    ) node2posy,
    (SELECT 
      posz
     FROM nodePos 
     WHERE nodeId IN (SELECT node2Id FROM elementNode WHERE elementid = en.elementId) 
    ) node2posz,
    (SELECT 
      posx
     FROM nodePos 
     WHERE nodeId IN (SELECT node3Id FROM elementNode WHERE elementid = en.elementId) 
    ) node3posx,
    (SELECT 
      posy
     FROM nodePos 
     WHERE nodeId IN (SELECT node3Id FROM elementNode WHERE elementid = en.elementId) 
    ) node3posy,
    (SELECT 
      posz
     FROM nodePos 
     WHERE nodeId IN (SELECT node3Id FROM elementNode WHERE elementid = en.elementId) 
    ) node3posz
FROM elementNode en 
JOIN (SELECT c.elementid, c.cellId, r.resistivity FROM elementCellGroup c 
      JOIN cellGroupResistivity r ON r.cellId=c.cellId) B
ON en.elementId=B.elementId;
        """)

        conn.commit()
        conn.close()
        print("finished")


    def _restoreResistivityBlockIter(self, fp):
        """
        
        Parameters
        ----------
        fp : Str
            complete file path of resistivity_block_iter[#].dat
        """
    
        with open(fp, 'r') as f:
            tmp=f.readline().split()
            self.nElem = int(tmp[0])
            self.nCell = int(tmp[1])
            
            print(f'file: {fp}')
            
            # (0)element no. (1)cell no. 
            print(f'   ELEMENT: reading {self.nElem} lines ...')
            elemCellGroupLines = [None]*self.nElem
            for i in range(self.nElem):
                elemCellGroupLines[i] = f.readline().split()
            print(f'   finished')
            
            # (0)cell no. (1)Resistivity (2)- (3)- (4)- (5)resistivity fix flag
            print(f'   CELL: reading {self.nCell} lines ...')
            CellGroupResistivityLines = [None]*self.nCell
            for j in range(self.nCell):
                CellGroupResistivityLines[j] = f.readline().split()
            print(f'   finished')
            
        
                
        print(f'   writing to DB ...')
        conn = sqlite3.connect(self.fpDb)
        c = conn.cursor()
        
        # reset table
        #c.execute("DELETE from elementCellGroup")
        #c.execute("DELETE from cellGroupResistivity")
        
        for i in range(self.nElem):
            sql = "INSERT into elementCellGroup VALUES({}, {})"\
                    .format(elemCellGroupLines[i][0], elemCellGroupLines[i][1])    
            c.execute(sql)
            
        for j in range(self.nCell):
            sql = "INSERT into CellGroupResistivity VALUES({},{},{},{},{},{})"\
                    .format(CellGroupResistivityLines[j][0], 
                            CellGroupResistivityLines[j][1], 
                            CellGroupResistivityLines[j][2], 
                            CellGroupResistivityLines[j][3], 
                            CellGroupResistivityLines[j][4], 
                            CellGroupResistivityLines[j][5])    
            c.execute(sql)

        conn.commit()
        print(f'   finished')


    def _restoreMeshDat(self, fp):
        """
        Parameters
        ----------
        fp : Str
            complete file path of mesh.dat
        """
        #with open(fp, 'r') as f, open(self.fp3rdBlockTemp, 'w') as ft:
        with open(fp, 'r') as f:
            
            print(f'file: {fp}')            
            
            # 1st block - node position
            # (0)node id (1)node pos X (1)node pos Y (1)node pos Z
            f.readline() # TETRA
            tmp=f.readline().split() # number of node
            nNode = int(tmp[0])
            print(f'   NODE: reading {nNode} lines ...')
            nodePosLines = [None]*nNode
            for i in range(nNode):
                nodePosLines[i] = f.readline().split()
            print(f'   finished')
            
            
            # 2nd block - element-node relation 
            # (0)element id 
            # (1)adj0ElemId (2)adj1ElemId (3)adj2ElemId (4)adj3ElemId
            # (5)node0Id (6)node1Id (7)node2Id (8)node3Id
            tmp=f.readline().split() # number of element
            nElem = int(tmp[0])
            print(f'   ELEMENT DETAIL: reading {nElem} lines ...')
            elementNodeLines = [None]*nElem
            for i in range(nElem):
                elementNodeLines[i] = f.readline().split()
            print(f'   finished')

        print(f'   writing to DB ...')
        conn = sqlite3.connect(self.fpDb)
        c = conn.cursor()
        
        for i in range(nNode):
            sql = "INSERT into nodePos VALUES({},{},{},{})"\
                    .format(nodePosLines[i][0], nodePosLines[i][1],
                            nodePosLines[i][2], nodePosLines[i][3])    
            c.execute(sql)
            
        for j in range(nElem):
            sql = "INSERT into elementNode VALUES({},{},{},{},{},{},{},{},{})"\
                    .format(elementNodeLines[j][0], elementNodeLines[j][1],
                            elementNodeLines[j][2], elementNodeLines[j][3],
                            elementNodeLines[j][4], elementNodeLines[j][5],
                            elementNodeLines[j][6], elementNodeLines[j][7],    
                            elementNodeLines[j][8])    
            c.execute(sql)
            
        conn.commit()
        print(f'   finished')
        
    
    def outputAsXYZRho(self, output_fp, resistivity_threshold=None):
        """
        For each element, write resistivity and coordinates of the center of element to file.
        output file format is as follows:
        ---------------
        res x y z    <-- header
        33.123 1202.323 5820.345 2099.453  <-- [ohm-m] [m] [m] [m] 
        ....
        ---------------


        Args:
            output_fp (str): fullpath of output file 
        """
        conn = sqlite3.connect(self.fpDb)
        c = conn.cursor()
        sql = (
            "SELECT resistivity,"
            " (node0posx+node1posx+node2posx+node3posx)/4 x,"
            " (node0posy+node1posy+node2posy+node3posy)/4 y,"
            " (node0posz+node1posz+node2posz+node3posz)/4 z "
            "FROM elementNodePosWithResistivity"
        )
        if resistivity_threshold is not None:
            sql += f" WHERE resistivity < {resistivity_threshold}"
        result = c.execute(sql)

        with open(output_fp, 'w') as f:
            f.write("                 res               x               y               z\n")
            for rec in result:
                f.write(f"{rec[0]:>20.3f} {rec[1]:>15.3f} {rec[2]:>15.3f} {rec[3]:>15.3f}\n")
     
if __name__ == '__main__':
    main()
    