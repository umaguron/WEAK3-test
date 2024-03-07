# 環境整備
## gitの導入

ソースコードにはちょくちょく修正が入ると思うので、gitで管理しておくとあとあと楽です。

使い方は適当に調べれば出てきます。

コマンドラインで操作できるつよい人以外は以下をオススメします。

__Github Desktop__ https://desktop.github.com/



## anacondaの導入
pythonに色々なライブラリを導入することになるので、anacondaで管理するのがよい。
+ 各自PC

    https://www.anaconda.com/


+ ワークステーションなど

    以下を参考に各自のhomeディレクトリにanacondaをインストール<br>
    https://www.python.jp/install/anaconda/unix/install.html

+ pythonのバージョンは3.9にするのが無難。(最新のものだとPyTOUGHが動かないことがある)
```conda install python=3.9```



## プロキシ設定が必要な場合

+ conda

    参考->https://qiita.com/teruroom/items/7d8c26dc07ddeae90be8

    anacondaのルートディレクトリに.condarcというファイルを作成。以下のようにプロキシを設定する。
    ```
    proxy_servers:
        http: http://proxy.aaa.bbb.ac.jp:[port]
        https: http://proxy.aaa.bbb.ac.jp:[port]
    ```
    ※ https:の設定値は"https"でなく"http"であることに注意

+ git
    ```
    git config --global http.proxy http://proxy.aaa.bbb.ac.jp:[port]
    git config --global https.proxy https://proxy.aaa.bbb.ac.jp:[port]
    ```
    プロキシ設定を削除する
    ```
    git config --global --unset http.proxy
    ```

<br><br>



## 必要なライブラリの導入
## 1. pyTOUGH
1. https://github.com/acroucher/PyTOUGH
からダウンロードもしくはgit cloneしてくる。
2. 任意の場所に展開する。
3. define_path.pyの`PYTOUGH_ROOT_PATH`に展開後のディレクトリのパスを設定する。
4. gitが使用可能な場合、以下のようにしてもOK
```
# @project root
mkdir lib
cd lib
git clone https://github.com/acroucher/PyTOUGH
```
<br><br>

## 2. その他ライブラリ

### conda(or pip?)で入れる
+ matplotlib
+ pandas
+ numpy
+ scipy

コマンド

```
conda install matplotlib pandas numpy scipy
```
<br><br>


### pipで入れる
+ Pillow
(https://pillow.readthedocs.io/en/stable/index.html)
+ vtk (python3.9以上である必要)
+ flask
+ iapws
+ dill
+ pyproj

コマンド

```
python -m pip install --upgrade pip
python -m pip install --upgrade Pillow
pip install vtk
pip install flask
pip install iapws
pip install dill
pip install pyproj
```

注) ライブラリを入れる前にpythonのインタープリタがanacondaのものと同一か確認したほうがよい
```
which pip3
# -> anacondaが含まれるパスが表示されればたぶん大丈夫
```
<br><br>
### ワークステーションなどの場合
condaはプロキシ設定が正しければ動くはず。

pipについては
```pip3 install --user --proxy="http://(プロキシ:ポート)" (ライブラリ名)```　のようにするのが確実。
<br>

うまく行かないとき-->オフラインで頑張ってインストールする

+ https://qiita.com/saten/items/d2ac85947583723246bf
+ https://watlab-blog.com/2020/03/16/pip-proxy-error/
+ https://tech-diary.net/python-library-offline-install/

iapwsについては以下でもOK
1. ```git clone https://github.com/jjgomera/iapws.git```
2. 任意の場所に展開する。
3. define_path.pyの`IAPWS_ROOT_PATH`に展開後のディレクトリのパスを設定する。

<br>
<br>
<br>


## 3.  pyTOUGHの修正
そのままだと実装が古くて動かない部分がある。

#### **mulgrid.py内部**
すべての```if line == 'x':```
を
```if isinstance(line, str) and line == 'x':```
に、<br>
すべての```if line == 'y':```
を
```if isinstance(line, str) and line == 'y':```
に、変更する


#### **mulgrid.py: 2647行目付近**
`from matplotlib.mlab import griddata`
<br>
を以下に変更
<br>
`from scipy.interpolate import griddata`

#### **mulgrid.py: 2652行目付近**
`valgrid = griddata(xc, yc, valc, xgrid, ygrid, interp = 'linear')`
<br>
を以下に変更
<br>
`valgrid = griddata((xc, yc), valc, (xgrid[None,:], ygrid[:,None]), method = 'linear')`

<br>

##  4.  AMESHの導入 (optional)
1. ダウンロードする。https://tough.lbl.gov/licensing-download/free-software-download/
2. windowsの場合 -> executableをダウンロードする
3. mac, linuxの場合 -> Source codeをダウンロードする
    1. 解凍する
    2. コンパイルする(Sourceフォルダに移動してmakeとタイプ->リターン)
4. __!! 実行ファイルのパーミッションの変更を忘れずに !!__
5. define_path.pyのAMESH_DIRに実行ファイルの場所の相対パス、AMESH_PROGに実行ファイルの名前を書く

<br>
<br>

## 各種パスの設定

* define_path.pyの以下の項目を自分の環境に合わせて修正

  |変数名|設定値|説明|
  |-|-|-|
  |PYTOUGH_ROOT_PATH|(location of PyTOUGH)|PyTOUGHのプログラム(t2data.pyなど)の場所を指定|
  |BIN_DIR|(location of TOUGH3 executable)|TOUGH3の各モジュールの実行ファイル(User's Guideに従い、コンパイルしたもの。tough3-eco2n_v2など。)が含まれるディレクトリ(フルパス)<br>おそらく、(...)/TOUGH3v1.x/TOUGH3-Code/esd-tough3/tough3-install/bin になる|
  |BIN_DIR_T2|(location of TOUGH2 executable)|(TOUGH2も使いたい場合のみ設定。)TOUGH2の各モジュールの実行ファイルが含まれるディレクトリ(フルパス)|
  |BIN_DIR_LOCAL|(location of TOUGH3 executable)|上2つとは別にTOUGH3実行ファイルの場所を指定できる。WSに持っていく前に自分の端末でテストしたいときなどに便利。|
  |AMESH_DIR|(location of AMESH_PROG)||
  |AMESH_PROG|AMESH(Haukwa, 1998)実行ファイルの名前||
  |MPIEXEC|(full path of openMPI 'mpiexec' commands)|openMPIのmpiexecコマンドをフルパスで書く。TOUGH3並列計算に使用。<br>.../TOUGH3v1.0/TOUGH3-Code/esd-tough3/Readme_Linux.pdf 参照|

<br>
<br>

## データベースの新規作成　など

* 結果管理用データベースの新規作成
    
    プロジェクトルートで以下のコマンドを実行すればOK

    ```
    ./install_db.sh
    ```

* テーブルの表示を見やすくする
    
  * linux/mac
    
    ~/.sqlitercを作っておく。
    ファイルの中身は以下のようにする。
    ```
    .mode csv
    .width 0
    .headers on
    .nullvalue NULL
    ```
  * windows
    
    不明 


<br>
* ECO2N V2.0用データ
  CO2TAB(TOUGH3のパッケージに入っている？)は フォルダtables/ を作成しその中に配置する。

* define.py　設定値の説明
  
  |変数名|設定値|説明|
  |-|-|-|
  |T3OUT_ESCAPE_DIRNAME|任意|TOUGH3シミュレーションで出力される大量のファイルを退避するディレクトリ名。何でも良い|
  |SAVEFIG_DIRNAME|任意|作成した画像を書き出すディレクトリの名前。何でも良い|
  |INCON_FILE_NAME|'INCON'|TOUGH3初期条件ファイルの名前|
  |SAVE_FILE_NAME|'SAVE'|TOUGH3シミュレーション終了時の条件を記録したファイルの名前|
  |OUTPUT_ELEME_CSV_FILE_NAME|OUTPUT_ELEME.csv|TOUGH3出力ファイルの名前|
  |OUTPUT_CONNE_CSV_FILE_NAME|OUTPUT_CONNE.csv|TOUGH3出力ファイルの名前|

<br>
<br>

# TOUGH3/TOUGH2の準備
購入する or 同組織内で使っている人からもらう。コンパイル後のExecutableは以下のような名前に変更しておく。
- TOUGH3の場合、'tough3-[module name (小文字)]'
- TOUGH2の場合、'xt2_[module name (小文字)]'


### TOUGH3本体のbug fix
TOUGH3本体にもいくつかバグが見つかっている。以下のURLを参照しfixする。変更後はコンパイルを忘れずに。

https://tough.lbl.gov/user-support/tough-bugs-fixes/


<br>
<br>

# (参考) anacondaコマンド
### 新規環境作成
```conda create -n (環境名)```
### activate
```conda activate (環境名)```
### pythonの更新
```conda install python=3.9``` (or 任意のバージョン)

<br>
<br>

# 大きすぎてgitにupできないデータ
data/sowat_read.txt: sowat出力の塩水の熱力学データ

以下からダウンロードする。
https://drive.google.com/file/d/15HadRCdfGIZC_kKjQVaU1tYeTGnMXK5k/view?usp=sharing

ダウンロードしたものをdata/以下に配置する
<br>
<br>

# マニュアル
TOUGH3
https://tough.lbl.gov/software/new-release-tough3/

TOUGH3 各モジュール
https://tough.lbl.gov/software/tough3/


<br>
<br>

# テスト実行
### 概要

testdata/に２つのテスト用データがおいてある。
1.  testdata/ksv :  草津白根山の熱水系モデル (Matsunaga and Kanda, 2022)
2.  testdata/shirane_vicinity :  白根山近傍 325*25セル

ここでは1のほうを使ってみる。

|ファイル|説明|
|-|-|
|<b>testdata/ksv/input_ksv.ini</b>|浸透率構造・TOUGH3インプットファイル作成のためのすべての設定が含まれるファイル|
|testdata/ksv/seed.txt|voronoiメッシュの"seed"となる点データ[x,y]|
|testdata/topo_coarse.dat|地形データ[x,y,elevation] (本白根山が中心)|
|testdata/cellCenterResistivity.txt|浸透率構造作成のもととなる比抵抗構造データ[x,y,z,resistivity] (Matsunaga et al., 2022)|
|testdata/ksv/initial_1d.ini|シミュレーション初期条件作成に使用|
|testdata/result/initial_1d/SAVE|シミュレーション初期条件作成に使用|

<br>

### インプットファイルの作成

シミュレーションの実行ディレクトリ(すべてのinput/outputが書き出される場所)は設定ファイル(input_ksv.ini)の場所によらず以下になる。
    
```.../WEAK3/(input_ksv.iniのTOUGH_INPUT_DIR)/(input_ksv.iniのproblemName)```

ここでは以下になる。

```.../WEAK3/testdata/ksv/result/ksv``` 

実行方法

```
# 以下、すべてのプログラムはプロジェクトのrootで実行すること
cd ..../WEAK3
```

```
# メッシュ、浸透率構造の作成
python makeGrid.py testdata/ksv/input_ksv.ini
```
作成されるファイル
|||
|-|-|
|testdata/ksv/result/ksv/input_ksv.ini|testdata/ksv/input_ksv.iniのコピー|
|testdata/ksv/result/ksv/t2data.dat.grid|浸透率構造のファイル|
|testdata/ksv/result/ksv/layer_surface.pdf|作成したメッシュのplan view|
|testdata/ksv/result/ksv/permeability_layer-XX.pdf|作成された浸透率構造の断面(index=XX - input_ksv.iniの[plot] profile_lines_listで指定する)|
|testdata/ksv/result/ksv/resistivity_slice-lineXX.pdf|比抵抗構造の断面(index=XX - input_ksv.iniの[plot] profile_lines_listで指定する)|
|testdata/ksv/result/ksv/topo.pdf|作成されたメッシュから書いた地形図|
|testdata/ksv/grid.geo|メッシュ定義ファイル(input_ksv.iniの[mesh]mulgridFileFpに指定されたもの)|
```
# TOUGH3 インプットファイルの作成
python tough3exec_ws.py testdata/ksv/input_ksv.ini
```

作成されるファイル
|||
|-|-|
|testdata/ksv/result/ksv/t2data.dat|TOUGH3のインプットファイル|
|testdata/ksv/result/ksv/INCON|TOUGH3の初期条件の設定ファイル|
|testdata/ksv/result/ksv/CO2TAB|EOSモジュールがECO2N_v2のとき必要なファイル。プロジェクトルートからコピーされる|

### 本体の実行

```
# 実行dirに移動
cd testdata/ksv/result/ksv

# mpiexecの実行に必要な準備。(実行環境による)
module purge
export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH

# TOUGH3本体実行 
mpiexec -n 8 (tough3-eco2n_v2のフルパス) t2data.dat (outputファイル名)
``` 

以下でも同じように実行可能

```
python run.py testdata/ksv/input_ksv.ini
```

出力ファイルについてはTOUGH3マニュアル参照

