import math
import xml.etree.ElementTree as ET
import glob
import os
import io
from math import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Geod
g = Geod(ellps='clrk66')


"""
### できること
国土地理院数値標高モデル(xmlファイル形式)を読み取り、緯度経度をxyz座標(単位:km)に変換する。

### 準備
以下のURLにアクセスし、数値標高モデルをダウンロードする。

基本地図情報ダウンロードサービス（国土地理院）
https://fgd.gsi.go.jp/download/menu.php
(数値標高モデル-->(領域選択)-->ダウンロードファイル確認-->ダウンロード)

ダウンロードした標高データのxmlファイル(FG-GML*.xml)をXMLDIRに設定したディレクトリに配置する。
"""



def main():
    ############### setting ###############
    # このディレクトリ内に置かれた地理院数値標高モデル 5mメッシュ or 10mメッシュ のxmlファイルをすべて読み込む。
    XMLDIR = ""
    # x y z を書き出すファイルのフルパス
    OUTPUT_XY = ""
    # longitude latitude z を書き出すファイルのフルパス
    OUTPUT_LONLAT = "/Users/matsunagakousei/Downloads/PackDLMap (5)/FG-GML-5339-01-DEM5B/topo_fine_lon_lat.dat"
    # x y z の原点となる緯度経度
    CENTER = {'lat':34.082082, 'lon':139.52219} # Miyake

    # 値を間引く。例えば、10なら緯度経度方向ともに10飛ばしでxmlから値を取得する(元が10mメッシュなら100mメッシュとして出力)
    SKIP_INTERBAL = 1
    ## 確認用プロット
    Z_MAX = 2
    Z_MIN = 0
    CONT_INTBL = 0.1
    #######################################

    ## get xml file list
    xmls:list = glob.glob(os.path.join(XMLDIR, "*.xml"))
    
    ## read xmls
    with open(OUTPUT_XY, 'w') as f1, open(OUTPUT_LONLAT, 'w') as f2 :
        # read each xml and write xyz to file object
        for xml in xmls:
            X,Y,Z, LAT, LON = read_xml(xml, CENTER, skip_interbal=SKIP_INTERBAL, handler_xy=f1, handler_lonlat=f2)
            plt.plot(X, Y, 'o', ms=1, label=os.path.basename(xml))

        plt.legend()
        plt.savefig(os.path.join(XMLDIR,"range.pdf"))
        plt.close()
    
    ## plot 
    df = pd.read_csv(OUTPUT_XY, delim_whitespace=True, names=['x', 'y', 'z'])
    fig, ax = plt.subplots(1,1,sharex=True, sharey=True)
    ax.tricontour(df['y'], df['x'], df['z'], levels=np.arange(Z_MIN,Z_MAX,CONT_INTBL), 
                  linewidths=0.1, colors='white')
    c = ax.tricontourf(df['y'], df['x'], df['z'], levels=np.arange(Z_MIN,Z_MAX,0.01), 
                       cmap='terrain')
    ax.set_xlabel('Easting (m)')
    ax.set_ylabel('Northing (m)')
    ax.set_aspect('equal')
    fig.colorbar(c, ax=ax)
    plt.show()


def read_xml(xml_fp, origin:dict, skip_interbal:int,
             handler_xy:io.TextIOWrapper, handler_lonlat:io.TextIOWrapper=None,
             dist_lim:dict=None):
    """
    Args:
        xml_fp (str): GSI xmlのファイルパス
        origin (dict): 中心座標。keyは'lon', 'lat'
        skip_interbal (int): NS, EW各方向の読み取りの際の読み飛ばし間隔
        dist_lim (dict): 出力範囲。keyは'ns', 'ew'。単位はkm
        handler_xy (io.TextIOWrapper): 下の説明をみよ
        handler_lonlat (io.TextIOWrapper): 下の説明をみよ

    read a GSI's xml file (Digital Elevation Model)
    国土地理院10m(5m)メッシュを読み、渡されたファイルオブジェクトに書き込む
    書き出されるファイルのフォーマットは以下の通り。
    
    handler_xy:
    ---------------------------
    x          y         z
    緯度方向[m] 経度方向[m] 標高[m]
    緯度方向[m] 経度方向[m] 標高[m]
    ...
    ---------------------------

    handler_lonlat:
    ---------------------------
    lon      lat      z
    経度(deg) 緯度(deg) 標高[m]
    経度(deg) 緯度(deg) 標高[m]
    ...
    ---------------------------


    (参考) 名前空間のある XML の解析
    https://docs.python.org/ja/3/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
    (参考) XPath サポート
    https://docs.python.org/ja/3/library/xml.etree.elementtree.html#xpath-support
    """
    tree = ET.parse(xml_fp)
    root = tree.getroot()


    # dictionary of namespace
    ns = {'gml':'http://www.opengis.net/gml/3.2',
            'xsi':'http://www.w3.org/2001/XMLSchema-instance',
            'xlink':'http://www.w3.org/1999/xlink'}

    # extract info
    tupleList = [float(_.split(',')[1]) for _ in root.find('.//gml:tupleList', ns).text.strip().split('\n')]
    lowerCorner = [float(_) for _ in root.find('.//gml:lowerCorner', ns).text.split(' ')]
    upperCorner = [float(_) for _ in root.find('.//gml:upperCorner', ns).text.split(' ')]
    lowerCorner_dict = {'lat':lowerCorner[0],'lon':lowerCorner[1]}
    upperCorner_dict = {'lat':upperCorner[0],'lon':upperCorner[1]}
    low = [int(_) for _ in root.find('.//gml:low', ns).text.split(' ')]
    high = [int(_) for _ in root.find('.//gml:high', ns).text.split(' ')]
    axisLabels = root.find('.//gml:axisLabels', ns).text.split(' ')
    sequenceRule = root.find('.//gml:sequenceRule', ns).attrib['order']
    startPoint = [int(_) for _ in root.find('.//gml:startPoint', ns).text.split(' ')]

    print(f"""### file {xml_fp}
    tupleList: {len(tupleList)}
    lowerCorner: {lowerCorner}
    upperCorner: {upperCorner}
    low: {low}
    high: {high}
    axisLabels: {axisLabels}
    sequenceRule: {sequenceRule}
    startPoint: {startPoint}
    """)

    # calc grid spaceing in the current DEM domain
    dlat = (upperCorner[0]-lowerCorner[0])/(high[1]+1)
    dlon = (upperCorner[1]-lowerCorner[1])/(high[0]+1)

    # to confirm
    xarr, yarr, zarr = [], [], []
    latarr, lonarr = [], []

    counter = 0
    for ilat in range(low[1], high[1]+1):
        # In the area where elevation values are omitted.
        if ilat<startPoint[1]:
            ilat = ilat + 1
            continue

        for ilon in range(low[0], high[0]+1):
            ## Skip or not skip
            # In the area where elevation values are omitted.
            if ilat==startPoint[1] and ilon<startPoint[0]:
                ilon = ilon + 1
                continue
            # Thinning out elevation points
            if (ilon % skip_interbal)!=0 or (ilat % skip_interbal)!=0:    
                ilon = ilon + 1
                counter = counter + 1
                continue
            # tupleList ran out
            if counter >= len(tupleList):
                continue
            # ignore sea (z=-9999)
            if tupleList[counter] < -9000:
                ilon = ilon + 1
                counter = counter + 1
                continue
            
            ## longitude and latitude of current point
            pos = {'lat': upperCorner[0] - (ilat + 0.5) * dlat,
                   'lon': lowerCorner[1] + (ilon + 0.5) * dlon}

            # use pyprj
            forw_azim, back_azim, dist = g.inv(lats1=pos['lat'], lons1=pos['lon'], lats2=origin['lat'], lons2=origin['lon'],)
            x = dist * np.cos(np.array(back_azim)/180*math.pi)/1000 # in [km]
            y = dist * np.sin(np.array(back_azim)/180*math.pi)/1000 # in [km]
            z = tupleList[counter] / 1000

            # to confirm
            if dist_lim is not None and \
                    not (-dist_lim['ew']/2 <= y <= +dist_lim['ew']/2 and \
                         -dist_lim['ns']/2 <= x <= +dist_lim['ns']/2):
                pass
            else:
                xarr.append(x)
                yarr.append(y)
                zarr.append(z)
                latarr.append(pos['lat'])
                lonarr.append(pos['lon'])

                ## write to file
                handler_xy.write(f"{x:>15.6f}{y:>15.6f}{z:>12.6f}\n")
                if handler_lonlat is not None:
                    handler_lonlat.write(f"{pos['lon']:>15.6f}{pos['lat']:>15.6f}{z*1000:>12.6f}\n")

            ## increment
            counter = counter + 1
            ilon = ilon + 1

        ilat = ilat + 1
    
    return xarr, yarr, zarr, latarr, lonarr

def get_center_loc_xmls(xml_fp_list:list):
    """
    Args:
        xml_fp_list (list): list of GSI xml files

    Returns:
        tuple: Average position (longitude, latitude) of the center coordinates of each xml
    """
    # dictionary of namespace
    ns = {'gml':'http://www.opengis.net/gml/3.2',
            'xsi':'http://www.w3.org/2001/XMLSchema-instance',
            'xlink':'http://www.w3.org/1999/xlink'}
    
    center_lat = []
    center_lon = []

    for xml_fp in xml_fp_list:
        tree = ET.parse(xml_fp)
        root = tree.getroot()
        # extract info 
        lowerCorner = [float(_) for _ in root.find('.//gml:lowerCorner', ns).text.split(' ')]
        upperCorner = [float(_) for _ in root.find('.//gml:upperCorner', ns).text.split(' ')]
        center_lat.append((upperCorner[0]+lowerCorner[0])/2)
        center_lon.append((upperCorner[1]+lowerCorner[1])/2)
        
    return sum(center_lon)/len(center_lon), sum(center_lat)/len(center_lat)

def read_jodc_bathy(file:str, center:dict, handler_xy:io.TextIOWrapper, 
                    Z0:float, dist_lim:dict=None):
    """_summary_

    Args:
        file (str): _description_
        center (dict): 中心座標。keyは'lon', 'lat'
        handler_xy (io.TextIOWrapper): _description_
        Z0 (float): (平均水面)-(最低水面)
            https://www1.kaiho.mlit.go.jp/TIDE/datum/
        dist_lim (dict, optional): 出力範囲。keyは'ns', 'ew'。単位はkm. Defaults to None.

    Returns:
        _type_: _description_
    """
    
    df_jodc = pd.read_csv(file, delim_whitespace=True, names=['flg', 'lat', 'lon', 'depth'])
    forw_azim, back_azim, dist = g.inv(lats1=list(df_jodc.lat), 
                                    lons1=list(df_jodc.lon), 
                                    lats2=[center['lat']]*df_jodc.lat.size, 
                                    lons2=[center['lon']]*df_jodc.lon.size)
    # 中心からの距離も新たなcolumnとしてdfに追加
    df_jodc['dist'] = dist
    # x,y in [km]も新たなcolumnとしてdf_jodcに追加
    # back_azim: point2-->point1 in degree, from N90, CCW
    # dist: distance in [m]
    df_jodc['x'] = dist * np.cos(np.array(back_azim)/180*math.pi)/1000 # in [km]
    df_jodc['y'] = dist * np.sin(np.array(back_azim)/180*math.pi)/1000 # in [km]

    if dist_lim is not None:
        df_out = df_jodc[(-dist_lim['ns']/2 <= df_jodc['x'])&\
                         (df_jodc['x'] <= dist_lim['ns']/2)&\
                         (-dist_lim['ew']/2 <= df_jodc['y'])&\
                         (df_jodc['y'] <= dist_lim['ew']/2)]
    else:
        df_out = df_jodc
    
    for j, (flg, lat, lon, depth, x, y) in enumerate(zip(df_out.flg, df_out.lat, df_out.lon, df_out.depth, df_out.x, df_out.y)):
        # 水深zにZ0を足して標高(asl)に変換する
        handler_xy.write(f"{x:10.5f} {y:10.5f} {-(depth+Z0)/1000:10.5f}\n")
        if j%1000==0:
            print(f"[points added from {file} to handler_xy] points finished: {j}")
    
    return np.array(df_out.lat), np.array(df_out.lon)


if __name__ == "__main__":
    main()
