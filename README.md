# 概要
TOUGH2/TOUGH3の入力ファイル作成支援
* 比抵抗構造に基づくシステマチックな浸透率構造作成
* 地形を含むメッシュの作成
* GUI的にシミュレーションのパラメータを設定
* 結果の整理・描画

WEAK3は、ワークステーション(WS)とローカル(各自のマシン)の2箇所に同じ環境を構築することを想定しています。
ローカル環境でもWSでも同じ動作が期待できるので、入力ファイルの作成や結果の可視化を手元で試せたり、まったく同じ処理をWSにジョブとして投げることもできます。

# 実行環境
* __linux__ か __mac__

  windowsでの動作確認は基本的にしていません。macが使えるならそっちを使ってください。環境構築の手間を考えても、macのほうが圧倒的に楽です

  どうしてもwindowsで、という方は、WSLなどでlinux環境を用意してください。pythonプログラムを動かすだけならcmdやpowershellでも問題ないですが、いくつかのシェルスクリプトが使えないのでやや不便です。

# 環境整備

install_memo.md 参照

# 構成
主要なプログラムのみ
```
WEAK3/ <--プロジェクトルート 
    |
    |-- makeGrid.py:            (1)浸透率構造メッシュ作成プログラム
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

1. __input.iniの作成__
    
    TOUGH3の入力ファイル。メッシュ、TOUGH3の設定パラメータなど、シミュレーションに必要な情報のほとんどをここに書く。

    サンプル
    
    * iniSample/input_voronoi_no_pmx.ini
    * testdata/ksv/input.ini
    * testdata/shirane_vicinity/input.ini
    
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
     python3 makeGrid.py input.ini -f   # create mesh
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

基本的に各自のマシン上で動かす。(XSS対策などを全くしていないため、web上に公開してはいけない)

1. 仮想サーバの起動
   ```
   python3 gui/controller.py
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
ローカルからWSにファイルをコピーするには、ファイル __util__ に定義したコマンドを使うのが便利。

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
