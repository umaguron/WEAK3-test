# 概要
TOUGH2/TOUGH3の入力ファイル作成支援
* 地形を含むメッシュの作成
* 比抵抗構造に基づく浸透率構造作成
* GUI的にシミュレーションのパラメータを設定
* 結果の整理・描画

# 環境整備
install_memo.md 参照

# 構成
主要なプログラムのみ
```
WEAK3/ <--プロジェクトルート 
    |
    |-- makeGrid.py:            (1a)浸透率構造メッシュ(直交格子, 地形なし)作成プログラム
    |
    |-- makeGridAmeshVoro.py:   (1b)浸透率構造メッシュ(voronoi grid, 地形あり)作成プログラム
    |
    |-- tough3exec_ws.py:       (2)TOUGH3 input file作成プログラム
    |
    |-- run.py:                 (3)TOUGH3の実行用プログラム
    |
    |-- update_log.py:          (4)結果を読み込みデータベース(log.db)に登録するプログラム
    |
    |-- makeVtu.py:             (5)結果を描画するプログラム
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

1. __用意するファイルは以下の2種類。名前は任意に決めて良い__
    
    * setting.ini 
    
        TOUGH3の実行ファイルや、入力ファイル・結果ファイルが書き出される場所を設定
    
    * input.ini 
    
        TOUGH3の入力ファイル。メッシュ、TOUGH3の設定パラメータなど、シミュレーションに必要な情報のほとんどをここに書く。
    
        <-- input.iniの[configuration]configIniにsetting.iniのパスを指定することで両者は紐付けられる

2. __input.iniの作成__
    
    サンプル
    
    * iniSample/input_voronoi_no_pmx.ini
    * testdata/input.ini
    
    手動で頑張っても良いが、htmlによる支援ツールを使うのがおすすめ。（__GUIによるinput.ini作成__ 参照）

3. __プログラム (1)-(5)について__

    * (1)(2) -> TOUGH3入力ファイルの作成
    * (3) -> 実行
    * (4)(5) -> 結果の整理・描画
    
    * (1)-(5)はいずれも引数にinput.iniをとる。
    
    * -xxxの形でいくつかのオプションが利用可能。各プログラムで利用可能なオプションは、引数に-hを与えることで見ることができる。

    * __ファイルが作成される場所はsetting.iniとinput.iniの設定により決定される。__ 従って、プログラム(1)-(5)はプロジェクト内のどこで動かしても同じ結果になる。
    
    * プロジェクトルートで実行するのがいろいろと楽

     ```
     実行コマンドの例
     python3 makeGridAmeshVoro.py input.ini -f   # create mesh
     python3 tough3exec_ws.py input.ini -f   # create TOUGH3 inputs
     python3 run.py input.ini   # run TOUGH3
     python3 update_log.py -ini input.ini   # register the results to database 
     python3 makeVtu.py input.ini -pl -coft -foft -suf  # creating figures from the results
     ```

    * 以下のスクリプトで上記コマンドを一括で実行できる
    ```
    ./run.sh input.ini
    ``` 

4. __ログの確認__

    log.db登録されたログはプロジェクトルートにて以下のコマンドにより確認できる

    ```
    ./log
    ```


# GUIによるinput.ini作成

基本的に各自のマシン上で動かす。(WS上で実行する方法はあるはず。詳しい人教えてください。)

1. 仮想サーバの起動
   ```
   python3 gui/controller.py
   ```

2. 起動できたら <http:/localhost:8000> にブラウザでアクセスする。

   * [usage](http://localhost:8000/usage)に操作方法が書いてある。
   * 新規作成は[cmesh1](http://localhost:8000/cmesh1)から
   * 作成済みinput.iniを読み込み、浸透率構造を編集するには[cmesh3_readFromIni]()のテキストボックスにinput.iniのパスを入力してEnter
   * 作成済みinput.iniを読み込み、TOUGH3シミュレーションの設定パラメータを編集するには[cmesh3_readFromIni]()のテキストボックスにinput.iniのパスを入力してEnter

3. 最後まで行くと作成されたinput.iniをダウンロードすることができる。

4. 別環境(たとえばWS)で実行するには、作成されたinput.iniだけでなく、以下も必要であることに注意
   * setting.ini
   * voronoiグリッドの母点データ
   * 地形データ
   * 比抵抗構造データ
   
     これらをプロジェクトルート基準で同じ階層に配置する。
