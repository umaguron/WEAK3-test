# logging
実装例
```python
# loggingモジュールのimport, ファイルハンドラ/ストリームハンドラのルートロガーへの紐付けがdefine_logging内部で予め行われる
import define_logging

# ロガーの取得
logger = logging.getLogger($(logger_name))

# メッセージの出力
logger.info("hogehoge")
logger.warning("hogehoge")
logger.error("hogehoge")
...
```
## (logger_name)の例
|code|出力|
|-|-| 
|__class__.__name__ | クラス名|
|f"{__class__.__name__}.{sys._getframe().f_code.co_name}" | クラス名.メソッド名 ※メソッドの内側からメソッド名を取得するとき|

## define.pyに定義する値
|定数名|説明|
|-|-|
|FILEPATH_LOG|書き出されるログファイルのパス|
|LOG_LEVEL_STREAM|ストリームへ出力されるログレベル|
|LOG_LEVEL_FILE|ログファイルに出力されるログレベル|
|FORMAT_LOG_STREAM|ストリームに出力されるログのフォーマット|
|FORMAT_LOG_FILE|ログファイルに出力されるログのフォーマット|


# GUI
- Bootstrap https://getbootstrap.com/
    - cheat sheet  https://getbootstrap.com/docs/5.2/examples/cheatsheet/
- flask https://flask.palletsprojects.com/en/2.1.x/
- jinja2 https://jinja.palletsprojects.com/en/3.1.x/
- jQuery https://jquery.com/

# VSCodeの設定
* pyTOUGHのインテリセンスを有効にする
```python.analysis.extraPaths = (pyTOUGHがあるディレクトリのパス)```

