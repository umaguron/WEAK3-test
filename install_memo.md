# 環境整備
## gitの導入

ソースコードにはちょくちょく修正が入ると思うので、gitで管理しておくとあとあと楽です。

使い方は適当に調べれば出てきます。

コマンドラインで操作できるつよい人以外は以下をオススメします。
__Github for Desktop__ https://desktop.github.com/



## anacondaの導入
pythonに色々なライブラリを導入することになるので、anacondaで管理するのがよい。
+ 各自PC

    https://www.anaconda.com/


+ ワークステーション

    以下を参考に各自のhomeディレクトリにanacondaをインストール<br>
    https://www.python.jp/install/anaconda/unix/install.html




## プロキシ設定(研究室で使う場合)

+ conda

    参考->https://qiita.com/teruroom/items/7d8c26dc07ddeae90be8

    anacondaのルートディレクトリに.condarcというファイルを作成。以下のようにプロキシを設定する。
    ```
    proxy_servers:
        http: http://proxy.aaa.bbb.ac.jp:8080
        https: http://proxy.aaa.bbb.ac.jp:8080
    ```
    ※ https:の設定値は"https"でなく"http"であることに注意

+ git
    ```
    git config --global http.proxy http://proxy.aaa.bbb.ac.jp:8080
    git config --global https.proxy https://proxy.aaa.bbb.ac.jp:8080
    ```
    プロキシ設定を削除する
    ```
    git config --global --unset http.proxy
    ```

<br><br>



# 必要なライブラリの導入
## 1. pyTOUGH
1. https://github.com/acroucher/PyTOUGH
からダウンロードもしくはgit cloneしてくる。
2. 任意の場所に展開する。
3. define_path.pyの`PYTOUGH_ROOT_PATH`に展開後のディレクトリのパスを設定する。
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

コマンド

```
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade Pillow
pip install vtk
pip install flask
pip install iapws
```

注) ライブラリを入れる前にpython3のインタープリタがanacondaのものと同一か確認したほうがよい
```
which pip3
# -> anacondaが含まれるパスが表示されればたぶん大丈夫
```
<br><br>
### ワークステーション(faraday)の場合
condaはプロキシ設定が正しければ動くはず。

pipについては
```pip3 install --user (ライブラリ名)```で導入する。
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

##  4.  AMESHの導入
1. ダウンロードする。https://tough.lbl.gov/licensing-download/free-software-download/
2. windowsの場合 -> executableをダウンロードする
3. mac, linuxの場合 -> Source codeをダウンロードする
    1. 解凍する
    2. コンパイルする(Sourceフォルダに移動してmakeとタイプ->リターン)
4. __!! 実行ファイルのパーミッションの変更を忘れずに !!__
5. define_path.pyのAMESH_DIRに実行ファイルの場所の相対パス、AMESH_PROGに実行ファイルの名前を書く

<br>
<br>

## 5. 各種パスの設定

* define_path.pyの以下の項目を自分の環境に合わせて修正

  |変数名|設定値|説明|
  |-|-|-|
  |PYTOUGH_ROOT_PATH|PyTOUGH location|PyTOUGHのプログラム(t2data.pyなど)の場所を指定|
  |BIN_DIR|TOUGH3 executable location|TOUGH3の各モジュールの実行ファイル(User's Guideに従い、コンパイルしたもの。tough3-eco2n_v2など。)が含まれるディレクトリ(フルパス)<br>おそらく、(...)/TOUGH3v1.x/TOUGH3-Code/esd-tough3/tough3-install/bin になる|
  |BIN_DIR_T2|TOUGH2 executable location|(TOUGH2も使いたい場合のみ設定。)TOUGH2の各モジュールの実行ファイルが含まれるディレクトリ(フルパス)|
  |BIN_DIR_LOCAL|TOUGH2 executable location|上2つとは別にTOUGH3実行ファイルの場所を指定できる。WSに持っていく前に自分の端末でテストしたいときなどに便利。|
  |AMESH_DIR|AMESH_PROGがおいてあるディレクトリ（プロジェクトルートからのパス||
  |AMESH_PROG|AMESH(Haukwa, 1998)実行ファイルの名前||

<br>
<br>

# その他

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
    .mode column
    .width 0
    .headers on
    .nullvalue NULL
    ```
  * windows
    
    不明 


<br>
* ECO2N V2.0用データ
  CO2TAB(TOUGH3のパッケージに入っている？)は /tables 直下に配置する。

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
購入する or 同組織内で使っている人からもらう

### TOUGH3本体のbug fix
TOUGH3本体にもいくつかバグが見つかっている。以下のURLに従いfixする。

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

matsunagaに聞いてください。

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

testdata/にテスト用データがおいてある。
(草津白根山の熱水系モデル; Matsunaga and Kanda, 2022)

浸透率構造作成に比抵抗構造モデル(Matsunaga et al., 2022)を使用

|ファイル|説明|
|-|-|
|testdata/setting.ini|TOUGH3プログラム本体のパスなど実行環境についての設定|
|<b>testdata/input.ini</b>|浸透率構造・TOUGH3インプットファイル作成のためのすべての設定が含まれるファイル|
|testdata/seed.txt|voronoiメッシュの"seed"となる点データ[x,y]|
|testdata/topo_coarse.dat|地形データ[x,y,elevation] (本白根山が中心)|
|testdata/cellCenterResistivity.txt|比抵抗構造データ[x,y,z,resistivity] (Matsunaga et al., 2022)|
|testdata/initial_1d.ini|シミュレーション初期条件作成に使用|
|testdata/input/initial_1d/SAVE|シミュレーション初期条件作成に使用|

<br>

### インプットファイルの作成

シミュレーションの実行ディレクトリ(すべてのinput/outputが書き出される場所)は設定ファイル(input.ini)の場所によらず以下になる。
    
```.../WEAK3/(setting.iniのTOUGH_INPUT_DIR)/(input.iniのproblemName)```

input.ini の configini= に、setting.ini のパスを設定することで両者は紐付けられる。

ここでは以下になる。

```.../WEAK3/testdata/1_reference_case``` 

実行方法

```
# 以下、すべてのプログラムはプロジェクトのrootで実行すること
cd ..../WEAK3
```

```
# メッシュ、浸透率構造の作成
python3 makeGridAmeshVoro.py testdata/input.ini
```
作成されるファイル
|||
|-|-|
|input.ini|testdata/input.iniのコピー|
|testdata/grid.geo|メッシュ定義ファイル(パスはinput.iniの[mesh]mulgridFileFpに指定されたもの)|
|t2data.dat.grid|浸透率構造のファイル|
|layer_surface.pdf|作成したメッシュのplan view|
|permeability_layer-XX.pdf|作成された浸透率構造の断面(index=XX - input.iniの[plot] profile_lines_listで指定する)|
|resistivity_slice-lineXX.pdf|比抵抗構造の断面(index=XX - input.iniの[plot] profile_lines_listで指定する)|
|topo.pdf|作成されたメッシュから書いた地形図|
```
# TOUGH3 インプットファイルの作成
python3 tough3exec_ws.py testdata/input.ini
```

作成されるファイル
|||
|-|-|
|testdata/input/1_reference_case/t2data.dat|TOUGH3のインプットファイル|
|testdata/input/1_reference_case/INCON|TOUGH3の初期条件の設定ファイル|
|testdata/input/1_reference_case/CO2TAB|EOSモジュールがECO2N_v2のとき必要なファイル。プロジェクトルートからコピーされる|

### 本体の実行

```
# 実行dirに移動
cd testdata/1_reference_case

# 以下は実行環境による(faradayの場合)
module purge
export LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH

# TOUGH3本体実行 
mpiexec -n 8 (tough3-eco2n_v2のフルパス) t2data.dat (outputファイル名)
``` 

以下でも同じように実行可能

```
python3 run.py testdata/input.ini
```

出力ファイルについてははTOUGH3マニュアル参照

