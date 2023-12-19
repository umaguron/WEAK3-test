import copy
import math
import shutil
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
import numpy as np
from import_pytough_modules import *
import mulgrids
import _readConfig
import makeGridAmeshVoro
import t2data
import define

MARGIN_LENGTH = 400 # edge length of outermost elements

# column/vertex name に変換する関数
def naming(convention, n):
    # vertexの名前もcolumnのconventionに従う
    return makeGridAmeshVoro.col_name(n+1, convention) # indexを一つずらして渡すとちょうどよい
    
    # ALPHBT = "abcdefghijklmnopqrstuvwxyz"
    # base = len(ALPHBT)
    # ret = None
    # if convention==0:
    #     if n/base < 1:
    #         ret = ALPHBT[n%base]
    #     elif n/(base**2+base) < 1:
    #         ret = ALPHBT[n//base-1]
    #         ret += ALPHBT[n%base]
    #     elif n/(base**3+base**2+base) < 1:
    #         n = n - (base**2+base)
    #         ret = ALPHBT[(n//base**2)]
    #         ret += ALPHBT[(n%base**2)//base]
    #         ret += ALPHBT[(n%base**2)%base]
    # if ret is None:
    #     raise
    # return ret

def layer_name(convention, layer_id, id_offset=0):
    ln = ""
    if convention==0:
        ln = makeGridAmeshVoro.layer_name(layer_id=layer_id+id_offset, convention=convention)
    elif convention==1:
        ln = makeGridAmeshVoro.layer_name(layer_id=layer_id+1+id_offset, convention=convention)
    elif convention==2:
        ln = makeGridAmeshVoro.layer_name(layer_id=layer_id+1+id_offset, convention=convention)
    
    # atmosphere layerの名前被り防止処理
    # check duplication
    if ln.strip().lower() == atm_blk_name(convention)['layer'].strip().lower():
        # If duplicated, add 1 to offset and then get layer name again.
        id_offset += 1  
        ln, id_offset = layer_name(convention, layer_id, id_offset)

    return ln, id_offset 
    


def atm_blk_name(convention)->dict:
    if convention==0:
        return {"col": define.ATM_BLK_NAME(convention)[0:3], 
                "layer": define.ATM_BLK_NAME(convention)[3:5]}
    elif convention==1:
        return {"col": define.ATM_BLK_NAME(convention)[3:5], 
                "layer": define.ATM_BLK_NAME(convention)[0:3]}
    elif convention==2:
        return {"col": define.ATM_BLK_NAME(convention)[2:5], 
                "layer": define.ATM_BLK_NAME(convention)[0:2]}

def seed_to_mulgraph_no_topo(ini:_readConfig.InputIni, output_fp:str, showVoronoi=False):
    print("*** creating 2-D Voronoi grid")
    
    # output file path
    # clean
    try:
        os.remove(output_fp) 
    except FileNotFoundError:
        pass
    
    """
    create voronoi diagram from seed points list
    """
    vor = creates_2d_voronoi_grid(ini.amesh_voronoi.voronoi_seeds_list_fp, 
            min_edge_length=ini.amesh_voronoi.tolar,
            preview_save_fp=os.path.join(os.path.dirname(ini.mulgridFileFp),"voronoi_check.png"), 
            show_preview=False)

    # 補足
    # ボロノイ点（上図のオレンジ点）の座標はvertices属性で取得する。
    # print(vor.vertices)
    # ボロノイ領域を構成するボロノイ点の組み合わせはregions属性で取得する。
    # print(vor.regions)

    """
    Convert generated voronoi diagram into a MULgraph file
    """
    convention = ini.mesh.convention
    atmos_type = 0 if ini.atmosphere.includesAtmos else 2
    atmos_volume = 1e25
    atmos_connection_dist = 1e-6
    length_unit = ""
    x_direction_cos = 0
    y_direction_cos = 0
    connection_type = 0
    perm_angle = 0
    block_ordering = 0

    header = f"GENER{convention:1}{atmos_type:1}{atmos_volume:>10.2g}{atmos_connection_dist:>10.2g}{length_unit:>5}{x_direction_cos:>10.2f}{y_direction_cos:>10.2f}{connection_type:1}{perm_angle:10.2f}{block_ordering:2}\n"

    # section: CONNECTION
    connections = "\nCONNECTIONS\n"
    ## 以下は scipy.spatial.voronoi_plot_2dを 参考に書いた ##
    center = vor.points.mean(axis=0) # Compute the arithmetic mean along the specified axis.
    ptp_bound = vor.points.ptp(axis=0) # Range of values (maximum - minimum) along an axis.
    # 書き出し用に別のvertexのリストにする
    vertices_modified = list(vor.vertices)
    # 各母点ペアについてのループ
    for pointidx, simplex in zip(vor.ridge_points, vor.ridge_vertices):
        # pointidx: ２つの母点のindexのリスト
        # simplex: pointidxの２つの母点間を隔てるridgeを構成する２つのvertexのindexリスト
        simplex = np.asarray(simplex) 
        connections += f"{naming(convention, pointidx[0]):>3}{naming(convention, pointidx[1]):>3}\n"
        if np.all(simplex >= 0):
            # 領域内部の場合
            pass
        else:
            # 最外部のセルだと無限遠の点(vertex idx=-1)を含むのでこれを適当な座標のvertexに置き換える必要がある。
            # このセクションでは関係ないが、さらに後ろの処理に影響するのでここできれいにしておく。

            i = simplex[simplex >= 0][0]  # finite end Voronoi vertex idx

            t = vor.points[pointidx[1]] - vor.points[pointidx[0]]  # tangent # vector of point(0) to point(1) 
            t /= np.linalg.norm(t) # normalize to unit vector
            n = np.array([-t[1], t[0]])  # normal direction

            midpoint = vor.points[pointidx].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            if (vor.furthest_site):
                direction = -direction
            far_point = vor.vertices[i] + direction * MARGIN_LENGTH
            
            # add far_point to vertices list
            vertices_modified.append(far_point)

            for pid in pointidx:
                # 母点に対応するregion
                reg_id = vor.point_region[pid]
                # 無限遠の点(-1)がvertices listに残っている場合は除去する
                if -1 in vor.regions[reg_id]:
                    vor.regions[reg_id].remove(-1)
                # 当該regionのvertices listに新たに計算されたfar_pointのindexを追加する
                vor.regions[reg_id].append(len(vertices_modified)-1)

                # 各regionごとにvertexを並び替えのために使用するvertexの位置を表す角度のリスト
                angles = []
                for vid in vor.regions[reg_id]:
                    # 母点からvertexに向かうベクトルを計算
                    coor = vertices_modified[vid] - vor.points[pid]
                    # このベクトルのx軸に対する角度を計算しリストに追加
                    angles.append(math.atan2(coor[1], coor[0])/math.pi*180)
                
                # 母点に対して当該regionのverticesを反時計回りに並び替える
                tmp = []
                for sorted_id in np.argsort(angles):
                    tmp.append(vor.regions[reg_id][sorted_id])
                vor.regions[reg_id] = tmp                
            
    # section VERTICES
    vertices = "VERTICES\n"
    for i, v in enumerate(vertices_modified):
        vertices += f"{naming(convention, i):>3}{v[0]:>10.2f}{v[1]:>10.2f}\n"

    # section GRID
    grid = "\nGRID\n"
    for poi_id, reg_id in enumerate(vor.point_region):
        colname = naming(convention, poi_id)
        centre_specified = 1
        reg = vor.regions[reg_id]
        poi = vor.points[poi_id]
        num_vertices = len(reg)
        grid += f"{colname:>3}{centre_specified:1}{num_vertices:>2n}{poi[0]:10.2f}{poi[1]:10.2f}\n"
        for ver_id in reg:
            grid += f"{naming(convention, ver_id):>3}\n"

    # section: LAYER
    layerstr = "\nLAYER\n"
    laythicks = ini.amesh_voronoi.layer_thicknesses
    # atmosphere
    # layer_id: 0 はatmosphere用。不要な場合はt2dataへの変換時に無視されるので機械的に追加でok
    atm_layer_name = atm_blk_name(convention)["layer"]
    # 厚さ0にして最上位レイヤー上面に張り付いていることにする
    layerstr += f"{atm_layer_name:>3}{ini.amesh_voronoi.elevation_top_layer+laythicks[0]/2:>10.2f}"\
               +f"{ini.amesh_voronoi.elevation_top_layer+laythicks[0]/2:>10.2f}\n"
    # land
    layer_id_offset = 0
    for i, l in enumerate(laythicks):
        if i==0:
            # 1st layer
            elev_lay_center = ini.amesh_voronoi.elevation_top_layer
            elev_lay_bottom = ini.amesh_voronoi.elevation_top_layer - l/2
        else :
            # subsequent layers
            elev_lay_center = elev_lay_center - laythicks[i-1]/2 - laythicks[i]/2
            elev_lay_bottom = elev_lay_bottom - laythicks[i]
        ln, layer_id_offset = layer_name(convention, i, layer_id_offset)
        layerstr += f"{ln:>3}{elev_lay_bottom:>10.2f}{elev_lay_center:>10.2f}\n"
            

    # output as MULgraph file format
    with open(output_fp, "w") as f:
        f.write(header)
        f.write(vertices)
        f.write(grid)
        f.write(connections)
        f.write(layerstr)
        f.write("\n\n") # end of file (空行２つ)

def creates_2d_voronoi_grid(seeds_list_fp:str, min_edge_length:float, preview_save_fp:str=None, show_preview=False)->Voronoi:
    """_summary_

    Args:
        seeds_list_fp (str): File path of seed points list
        min_edge_length (float): Minimum edge length [m] in 2D voronoi diagram 
        preview_save_fp (str, optional): _description_. Defaults to None.
        show_preview (bool, optional): _description_. Defaults to False.

    Returns:
        scipy.spatial.Voronoi: _description_
    """

    """
    read seed points list 
    """
    with open(seeds_list_fp, "r") as f:
        f.readline()
        pts = []
        for line in f:
            pts.append([float(i) for i in line.split()])

    """
    読み込んだ母点リストからボロノイ図を作成(scipy.spatial.Voronoi使用)
    """
    # 引数のqhull_optionsにはqhullのオプションが指定される。
    # 参考) qvoronoiのオプション(補: voronoi用にオプションを制限されたqhullのエイリアス。qhull v Qccと同じ) 
    # http://www.qhull.org/html/qvoronoi.htm#options
    # ここではデフォルトの"Qbb Qc Qz"に加えて"Cn"を追加
    #     Cn   - radius of centrum (roundoff added).  Merge facets if non-convex
    #            ボロノイ領域の中心を示す点（centrum）の半径を指定します。デフォルト値は0で、
    #            非ゼロの値を設定すると、その値がcentrumの半径となります。
    #            要は精度を犠牲する代わりに短いエッジの生成を防ぐことができるオプション
    # --> 試してみたら極端に短いエッジの生成を防ぐことができた
    

    c = 2 # initial Cn value
    dc = 0.1 # decriment of Cn value
    decreases_c = True

    # min_edge_length以下のエッジが生成されない限界のCn値を探す
    while decreases_c:
        c -= dc
        print(f"c={c:.2f}")

        ### convert seed points list to voronoi diagram with current Cn value ###
        vor = Voronoi(pts, furthest_site=False, qhull_options=f"Qbb Qc Qz C{c:.2f}")
        
        # min_edge_length以下のエッジのリストを作成
        filtered_ridges = [ridge for ridge in vor.ridge_vertices 
                        if ridge[0] != -1 and ridge[1] != -1 
                        and 0 < np.linalg.norm(vor.vertices[ridge[0]] - vor.vertices[ridge[1]]) < min_edge_length]
        
        # min_edge_length以下のエッジがいくつあるか判定
        if len(filtered_ridges) == 0 and c > -1*dc:
            decreases_c = True
        elif c <= -1*dc:
            decreases_c = False
            c += dc # 一つまえのcの値にもどす
            print(f"\nBest qhull option Cn value found: C{c:.2f}")
            break
        else:
            decreases_c = False
            print(f"\nEdges smaller than minimum_edge_length:{min_edge_length}m were generated at Cn={c:.2f}:")
            c += dc # 一つまえのcの値にもどす
            for v in filtered_ridges:
                print(f"vertex1: {vor.vertices[v[0]]}, vertex2: {vor.vertices[v[1]]}")
                print("    edge length:", np.linalg.norm(vor.vertices[v[0]]-vor.vertices[v[1]]), "m")
            print(f"\nBest qhull option Cn value found: C{c:.2f}")
            break
    
    ### 改めてvoronoi図を作成 ###
    vor = Voronoi(pts, furthest_site=False, qhull_options=f"Qbb Qc Qz C{c}")

    # 確認用
    fig, ax = plt.subplots(figsize=(10,10))
    fig = voronoi_plot_2d(vor, ax, show_vertices=False, point_size=1)
    ax.set_aspect('equal')
    ax.set_xlabel("Northing [m]")
    ax.set_ylabel("Easting [m]")
    ax.invert_yaxis()
    if preview_save_fp is not None:
        fig.savefig(preview_save_fp, dpi=150)
    if show_preview:
        plt.show()
    
    return vor



if __name__ == '__main__':
    # test
    ini = _readConfig.InputIni().read_from_inifile("testdata/ksv/input_ksv.ini")
    output_fp = ini.mulgridFileFp+".test"
    seed_to_mulgraph_no_topo(ini, output_fp)
    geo = mulgrids.mulgrid(output_fp)
    dat = t2data.t2data()
    dat.grid.fromgeo(geo)
    geo.write(f"seed2voroTest_conv{ini.mesh.convention}.geo")
    dat.write(f"seed2voroTest_conv{ini.mesh.convention}.dat.grid")
    geo.write_vtk(f"seed2voroTest_conv{ini.mesh.convention}.vtk")