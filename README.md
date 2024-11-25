# 概要
TOUGH2/TOUGH3の入力ファイル作成支援
* 比抵抗構造に基づくシステマチックな浸透率構造作成
* 地形を含むメッシュの作成
* GUI的にシミュレーションのパラメータを設定
* 結果の整理・描画

# 実行環境
* __linux__ か __mac__ を推奨。

  注) windowsでの動作確認はしていません。 (いくつかのシェルスクリプトを除けば動くかもしれない。)

# 環境整備

install_memo.md 参照

# 構成
主要なプログラムのみ
```
WEAK3/ <--プロジェクトルート 
    |
    |-- makeGrid.py:            (1)浸透率構造メッシュ作成プログラム
    |
    |-- tough3exec_ws.py:       (2)TOUGH3/TOUGH2 input file作成プログラム
    |
    |-- run.py:                 (3)TOUGH3/TOUGH2の実行用プログラム
    |
    |-- update_log.py:          (4)結果を読み込みデータベース(log.db)に登録するプログラム  (TOUGH3専用)
    |
    |-- makeVtu.py:             (5)結果を描画するプログラム (いくつかのオプションはTOUGH3専用)
    |
    |-- run.sh:                 (1)-(5)をまとめて実行するシェルスクリプト
    |
    |-- log.db:                 結果整理用のデータベースファイル(SQLite3)
    |
    |-- install_db.sh:          データベース作成用シェルスクリプト
    |
    |-- testdata/ <-- 動作テスト用サンプル
    |
    |-- lib/ <-- ライブラリ置き場
    |
    |-- gui/ <--htmlベースの浸透率構造メッシュ・入力ファイル作成支援ツール
         |
         |-- static/
         |      |
         |      |-- output/　<-- 作成された入力ファイルはここに書き出される
         |
         |-- templates/:    htmlテンプレート
         |
         |-- controller.py: 支援ツール本体プログラム
```

# 基本的な使い方

install_memo.mdの「テスト実行」に従って一通りやってみるのがおすすめ。

1. __input.iniの作成__
    
    TOUGH3の入力ファイル。メッシュ、TOUGH3の設定パラメータなど、シミュレーションに必要な情報のほとんどをここに書く。

    サンプル (3-D)
    * iniSample/input_voronoi_no_pmx.ini 
    * testdata/ksv/input.ini
    * testdata/shirane_vicinity/input.ini

    サンプル (2-D radial)
    * testdata/2d_radial/input_2d.ini
    * testdata/2d_radial_sea/input_ewasg.ini
    * testdata/fixed_p_injection/input_fixed_p.ini

    
    手動で頑張っても良いが、htmlによる支援ツールを使うのがおすすめ。（__GUIによるinput.ini作成__ 参照）

2. __プログラム (1)-(5)について__

    __以下のプログラムはいずれも引数にinput.iniをとる。__

    * (1)(2) -> TOUGH3入力ファイルの作成
    * (3) -> 実行
    * (4)(5) -> 結果の整理・描画
    
    * -xxxの形でいくつかのオプションが利用可能。各プログラムで利用可能なオプションは、引数に-hを与えることで見ることができる。

    * __ファイルが作成される場所はinput.iniの設定値(TOUGH_INPUT_DIR)により決定される。__ 従って、プログラム(1)-(5)はプロジェクト内のどこで動かしても同じ結果になる。
    
    * プロジェクトルートで実行するのがいろいろと楽

     ```bash
     # 実行コマンドの例
     python makeGrid.py input.ini -f   # create mesh
     python tough3exec_ws.py input.ini -f   # create TOUGH3 inputs
     python run.py input.ini   # run TOUGH3
     python update_log.py -ini input.ini   # register the results to database 
     python makeVtu.py input.ini -pl -coft -foft -suf  # creating figures from the results
     ```

    * 以下のスクリプトで上記コマンドを一括で実行できる
    ```
    ./run.sh input.ini
    ``` 

4. __ログの確認__

    log.db登録されたログはプロジェクトルートにて以下のコマンドにより確認できる

    ```
    # mac/linuxの場合
    ./log
    ```
    ```
    # windowsの場合
    ./log.bat
    ```

# 各プログラムのオプションについて
### makeGrid.py
浸透率構造メッシュ作成
|type|option name|(短縮形)|説明|
|-|-|-|-|
|str|(inputIni)||設定ファイル(ini-format)のパス|
|flag|--force_overwrite_all|-fa|はじめからすべて再作成し上書き(AMESHプログラムから動かす)|
|flag|--open_viewer|-view|作成された図を保存せずに画面表示する|
|flag|--force_overwrite_t2data|-f|(mesh.typeが'A_VORO'の場合のみ) グリッドについては既存のもの(*.geo)を利用し浸透率構造(.dat.grid)のみ再作成する。(AMESHプログラムを動かさない)|
|flag|--plot_all_layers|-all|(mesh.typeが'A_VORO'の場合のみ) すべてのレイヤーについて浸透率構造の水平断面図を作成する|
|flag+value|--layer [str]|-layer [str]|(mesh.typeが'A_VORO'の場合のみ) 指定されたインデックスのレイヤーについて浸透率構造の水平断面図を作成する|
|flag|--help|-h|オプションの説明を表示|

### tough3exec.py
TOUGH3/TOUGH2 input file作成
|type|option name|(短縮形)|説明|
|-|-|-|-|
|str|(inputIni)||設定ファイル(ini-format)のパス|
|flag|--force_overwrite|-f|t2dataファイルを再作成し上書き|
|flag|--help|-h|オプションの説明を表示|



### run.py
TOUGH3/TOUGH2を実行
|type|option name|(短縮形)|説明|
|-|-|-|-|
|str|(inputIni)||設定ファイル(ini-format)のパス|
|flag+value|--parallel [int]|-p [int]|並列計算を実施する。並列化の数を指定。(inputIni)に設定があっても無視される。|
|flag|--help|-h|オプションの説明を表示|


### update_log.py (TOUGH3専用)
結果を読み込みデータベース(log.db)に登録する
|type|option name|(短縮形)|説明|
|-|-|-|-|
|flag+value|--inputIni|-ini [str]|計算結果のDB登録を実施する。設定ファイル(ini-format)パスを指定。|
|flag|--updateAll|-all|(非推奨)|
|flag|--help|-h|オプションの説明を表示|

### makeVtu.py
結果を可視化する。図の保存場所はproblemディレクトリ直下の場合もあれば、新たに作成したサブディレクトリの場合もある。
|type|option name|(短縮形)|説明|
|-|-|-|-|
|str|(inputIni)||設定ファイル(ini-format)のパス|
|flag|--writesVtu|-v|paraview用の*.vtuファイルを作成|
|flag|--plotsTimeSeries|-t|(非推奨)|
|flag|--plotsTimeSeriesSurface|-ts|(非推奨)|
|flag|--plotsTimeSeriesSurfaceAreaCoft|-coft|__(TOUGH3専用)__ COFT*.csvファイルを読み込み、define.COFT_TS_AREASに定義された各領域内について地表面における熱・物質収支の時系列をプロットする。設定ファイルのtoughInput.prints_hc_surfaceがTrueでなければならない|
|flag|--plotsTimeSeriesSurfaceSumAllCoft|-cofts|__(TOUGH3専用)__ COFT*.csvファイルを読み込み、地表面全体における熱・物質収支の時系列をプロットする。設定ファイルのtoughInput.prints_hc_surfaceがTrueでなければならない|
|flag|--plotsTimeSeriesFoft|-foft|__(TOUGH3専用)__ 設定ファイルのtoughInput.history_blockに指定された要素について、各状態変数の時系列をプロットする。FOFT*.csvファイルから読み込み。|
|flag|--plotsProfileLast|-pl|シミュレーション終了時の状態で断面図を作成する。プロファイルの位置をplot.profile_lines_list, 出力したいパラメータをplot.slice_plot_variables_t[23]、断面の範囲をtoughInput.slice_plot_limitsに指定する。|
|flag|--plotsProfileAll|-pa|設定ファイルのtoughInput.print_intervalに指定されたステップごとに断面図を作成する。プロファイルの位置をplot.profile_lines_list, 出力したいパラメータをplot.slice_plot_variables_t[23]、断面の範囲をtoughInpu*t.slice_plot_limitsに指定する。 |
|flag|--createGif|-gif|設定ファイルのtoughInput.print_intervalに指定されたステップごとに断面図を作成し、gif形式のアニメーションを作成する。プロファイルの位置をplot.profile_lines_list, 出力したいパラメータをplot.slice_plot_variables_t[23]、断面の範囲をtoughInput.slice_plot_limitsに指定する。|
|flag|--plotsProfileLastCsv|-plc|__(TOUGH3専用)__ -plと同じ。output.listingではなくOUTPUT_ELEM.csvから結果を読み込む。FLOWのプロットはできない。|
|flag|--plotsProfileAllCsv|-pac|__(TOUGH3専用)__ -paと同じ。output.listingではなくOUTPUT_ELEM.csvから結果を読み込む。FLOWのプロットはできない。|
|flag|--plotsProfileCsvDiff|-pcdiff|__(TOUGH3専用)__ ini-format file のplot.diff_timesに指定された２つの時刻にそれぞれ最も近いスナップショット同士の差分を取り、その分布を任意の断面についてプロットする。プロファイルの位置、出力したいパラメータ、断面の範囲の設定は-plと同様。(2024/11/25追加)|
|flag|--createGifCsv|-gifc|__(TOUGH3専用)__ -gifと同じ。output.listingではなくOUTPUT_ELEM.csvから結果を読み込む。FLOWのプロットはできない。|
|flag|--inconColumn|-incon|INCONとSAVEを読み込み、初期状態および計算終了時におけるprimary variable (P,T,X)の鉛直一次元プロファイルをプロットする。設定ファイルのplot.columns_incon_plotにプロットしたいカラムのインデックスを指定する。|
|flag|--surfaceFlowMap|-suf|__(TOUGH3専用)__ シミュレーション終了時の状態について地表面での熱/流体の流量マップを作成する。設定ファイルのtoughInput.prints_hc_surfaceがTrueでなければならない。|
|flag+value|--interval [int]|-sufall [int]|__(TOUGH3専用)__ [int]で指定されたステップごとに地表面での熱/流体の流量マップを作成する。設定ファイルのtoughInput.prints_hc_surfaceがTrueでなければならない。|
|flag|--help|-h|オプションの説明を表示|

<br>

# GUIによるinput.ini作成

基本的に各自のマシン上で動かす。(XSS対策などを全くしていないため、web上に公開してはいけない)

1. 仮想サーバの起動
   ```
   python gui/controller.py
   # 開発用サーバがデバッグモードで起動される
   ```

2. 起動できたら <http:/localhost:8000> にブラウザでアクセスする。

   * [usage](http://localhost:8000/usage)に操作方法が書いてある。
   * 新規作成は[cmesh2](http://localhost:8000/cmesh2)から
   * 作成済みinput.iniを読み込み、浸透率構造を編集するには __Recreate permeability structure__ (cmesh3_readFromIni)のテキストボックスにinput.iniのパスを入力してEnter
   * 作成済みinput.iniを読み込み、TOUGH3シミュレーションの設定パラメータを編集するには __TOUGH3 simulation setting__ のテキストボックスにinput.iniのパスを入力してEnter
   * __しょっちゅうエラーになると思うが、多くの場合はブラウザバックで再入力が可能。__
   * __複数のinput.ini作成を同時に行わないこと__

3. 最後まで行くと作成されたinput.iniをダウンロードすることができる。

4. 別環境(たとえばWS)で実行するには、作成されたinput.iniだけでなく、以下も必要であることに注意
   * voronoiグリッドの母点データ
   * 地形データ
   * 比抵抗構造データ
   
     これらをプロジェクトルート基準で同じ階層に配置する。(#便利コマンド 参照)

# 便利コマンド
プロジェクト内のどこに各種ファイルが書き出されるかは、入力ファイル*.iniの設定値によってのみ決定され、プログラムの実行場所に依存しない。つまり入力ファイル*.iniが同一である限り、どの環境でWEAK3を動かしても(プロジェクトルート基準で)同一の階層にファイルが出力される。計算の実行はワークステーション(WS)で、入力ファイルの作成や結果の確認はローカル(各自のマシン)で、というような2つの環境を使い分けるうえで便利な仕様となっている。
<br>
<br>
ローカルからWSにファイルをコピーするには、ファイル __util__ に定義したコマンドを使うのが便利。
<br>

__util__ の中に以下を書いておく必要がある。
* WSのアドレス(ユーザー名@IPアドレス)
* WSのプロジェクトディレクトリのパス(\~を含めず、~/以降を書く)
* ローカル環境のプロジェクトディレクトリの絶対パス

__使い方__
```bash
# コマンドの読み込み
. util

# local --> WS
send (コピーしたいファイルorディレクトリのプロジェクトルート基準の相対パス)

# WS --> local
get (コピーしたいファイルorディレクトリのプロジェクトルート基準の相対パス)

```

<br>

# 引用
### TOUGH3
Yoojin Jung et al., “TOUGH3: A New Efficient Version of the TOUGH Suite of Multiphase Flow and Transport Simulators,” Computers & Geosciences 108 (November 2017): 2–7, https://doi.org/10.1016/j.cageo.2016.09.009.

### TOUGH2・EOS2・EOS3
K Pruess, C Oldenburg, and G Moridis, “TOUGH2 User’s Guide, Version 2.0, Report LBNL-43134, Lawrence Berkeley National Laboratory, Berkeley, Calif,” Superseded by Pruess et Al, 2012.

### ECO2N V2.0
Lehua Pan et al., “ECO2N V2.0: A TOUGH2 Fluid Property Module for Modeling CO2-H2O-NaCl Systems to Elevated Temperatures of up to 300°C,” Greenhouse Gases: Science and Technology 7, no. 2 (April 2017): 313–27, https://doi.org/10.1002/ghg.1617.

### EWASG
Alfredo Battistelli, Claudio Calore, and Karsten Pruess, “The Simulator TOUGH2/EWASG for Modelling Geothermal Reservoirs with Brines and Non-Condensible Gas,” Geothermics 26, no. 4 (August 1, 1997): 437–64, https://doi.org/10.1016/S0375-6505(97)00007-2.

### AMESH
Charles Haukwa, “AMESH A Mesh Creating Program for the Integral Finite Differencemethod: A User’s Manual,” August 31, 1998, https://doi.org/10.2172/892927.

### PyTOUGH
Adrian E. Croucher, “PyTOUGH: A Python Scripting Library for Automating TOUGH2 Simulations.,” Proceedings of the New Zealand Geothermal Workshop (2011).

### 塩水の比抵抗計算に使用
Ryosuke Sinmyo and Hans Keppler, “Electrical Conductivity of NaCl-Bearing Aqueous Fluids to 600 °C and 1 GPa,” Contributions to Mineralogy and Petrology 172, no. 1 (January 2017): 4, https://doi.org/10.1007/s00410-016-1323-z.

Arvin S. Quist and William L. Marshall, “Electrical Conductances of Aqueous Sodium Chloride Solutions from 0 to 800.Degree. and at Pressures to 4000 Bars,” The Journal of Physical Chemistry 72, no. 2 (February 1968): 684–703, https://doi.org/10.1021/j100848a050.

### 塩水の比抵抗計算に必要な塩水密度の算出に使用
Thomas Driesner, “The System H2O–NaCl. Part II: Correlations for Molar Volume, Enthalpy, and Isobaric Heat Capacity from 0 to 1000°C, 1 to 5000bar, and 0 to 1 XNaCl,” Geochimica et Cosmochimica Acta 71, no. 20 (October 15, 2007): 4902–19, https://doi.org/10.1016/j.gca.2007.05.026.

### 塩水の比抵抗計算に必要なH<sub>2</sub>O密度の算出に使用
IAPWS, “Revised Release on the IAPWS Industrial Formulation 1997 for the Thermodynamic Properties of Water and Steam” (The International Association for the Properties of Water and Steam, 2007).
