# VOICEVOX ENGINE

[![build](https://github.com/VOICEVOX/voicevox_engine/actions/workflows/build.yml/badge.svg)](https://github.com/VOICEVOX/voicevox_engine/actions/workflows/build.yml)
[![releases](https://img.shields.io/github/v/release/VOICEVOX/voicevox_engine)](https://github.com/VOICEVOX/voicevox_engine/releases)

[![test](https://github.com/VOICEVOX/voicevox_engine/actions/workflows/test.yml/badge.svg)](https://github.com/VOICEVOX/voicevox_engine/actions/workflows/test.yml)
[![Coverage Status](https://coveralls.io/repos/github/VOICEVOX/voicevox_engine/badge.svg)](https://coveralls.io/github/VOICEVOX/voicevox_engine)

[![build-docker](https://github.com/VOICEVOX/voicevox_engine/actions/workflows/build-docker.yml/badge.svg)](https://github.com/VOICEVOX/voicevox_engine/actions/workflows/build-docker.yml)
[![docker](https://img.shields.io/docker/pulls/voicevox/voicevox_engine)](https://hub.docker.com/r/voicevox/voicevox_engine)

[VOICEVOX](https://voicevox.hiroshiba.jp/) のエンジンです。  
実態は HTTP サーバーなので、リクエストを送信すればテキスト音声合成できます。

（エディターは [VOICEVOX](https://github.com/VOICEVOX/voicevox/) 、
コアは [VOICEVOX CORE](https://github.com/VOICEVOX/voicevox_core/) 、
全体構成は [こちら](https://github.com/VOICEVOX/voicevox/blob/main/docs/%E5%85%A8%E4%BD%93%E6%A7%8B%E6%88%90.md) に詳細があります。）

## ダウンロード

[こちら](https://github.com/VOICEVOX/voicevox_engine/releases/latest)から対応するエンジンをダウンロードしてください。

## API ドキュメント

[API ドキュメント](https://voicevox.github.io/voicevox_engine/api/)をご参照ください。

VOICEVOX エンジンもしくはエディタを起動した状態で http://localhost:50021/docs にアクセスすると、起動中のエンジンのドキュメントも確認できます。  
今後の方針などについては [VOICEVOX 音声合成エンジンとの連携](./docs/VOICEVOX音声合成エンジンとの連携.md) も参考になるかもしれません。

リクエスト・レスポンスの文字コードはすべて UTF-8 です。

### HTTP リクエストで音声合成するサンプルコード

```bash
echo -n "こんにちは、音声合成の世界へようこそ" >text.txt

curl -s \
    -X POST \
    "localhost:50021/audio_query?speaker=1"\
    --get --data-urlencode text@text.txt \
    > query.json

curl -s \
    -H "Content-Type: application/json" \
    -X POST \
    -d @query.json \
    "localhost:50021/synthesis?speaker=1" \
    > audio.wav
```

生成される音声はサンプリングレートが 24000Hz と少し特殊なため、音声プレーヤーによっては再生できない場合があります。

`speaker` に指定する値は `/speakers` エンドポイントで得られる `styleId` です。互換性のために `speaker` という名前になっています。

### 読み方を AquesTalk 記法で取得・修正するサンプルコード

`/audio_query`のレスポンスにはエンジンが判断した読み方が AquesTalk ライクな記法([本家の記法](https://www.a-quest.com/archive/manual/siyo_onseikigou.pdf)とは一部異なります)で記録されています。
記法は次のルールに従います。

- 全てのカナはカタカナで記述される
- アクセント句は`/`または`、`で区切る。`、`で区切った場合に限り無音区間が挿入される。
- カナの手前に`_`を入れるとそのカナは無声化される
- アクセント位置を`'`で指定する。全てのアクセント句にはアクセント位置を 1 つ指定する必要がある。
- アクセント句末に`？`(全角)を入れることにより疑問文の発音ができる

```bash
# 読ませたい文章をutf-8でtext.txtに書き出す
echo -n "ディープラーニングは万能薬ではありません" >text.txt

curl -s \
    -X POST \
    "localhost:50021/audio_query?speaker=1" \
    --get --data-urlencode text@text.txt \
    > query.json

cat query.json | grep -o -E "\"kana\":\".*\""
# 結果... "kana":"ディ'イプ/ラ'アニングワ/バンノオヤクデワアリマセ'ン"

# "ディイプラ'アニングワ/バンノ'オヤクデワ/アリマセ'ン"と読ませたいので、
# is_kana=trueをつけてイントネーションを取得しnewphrases.jsonに保存
echo -n "ディイプラ'アニングワ/バンノ'オヤクデワ/アリマセ'ン" > kana.txt
curl -s \
    -X POST \
    "localhost:50021/accent_phrases?speaker=1&is_kana=true" \
    --get --data-urlencode text@kana.txt \
    > newphrases.json

# query.jsonの"accent_phrases"の内容をnewphrases.jsonの内容に置き換える
cat query.json | sed -e "s/\[{.*}\]/$(cat newphrases.json)/g" > newquery.json

curl -s \
    -H "Content-Type: application/json" \
    -X POST \
    -d @newquery.json \
    "localhost:50021/synthesis?speaker=1" \
    > audio.wav
```

### ユーザー辞書機能について

APIからユーザー辞書の参照、単語の追加、編集、削除を行うことができます。

#### 参照

`/user_dict`にGETリクエストを投げることでユーザー辞書の一覧を取得することができます。

```bash
curl -s -X GET "localhost:50021/user_dict"
```

#### 単語追加

`/user_dict_word`にPOSTリクエストを投げる事でユーザー辞書に単語を追加することができます。  
URLパラメータとして、以下が必要です。
- surface （辞書に登録する単語）
- pronunciation （カタカナでの読み方）
- accent_type （アクセント核位置、整数）

アクセント核位置については、こちらの文章が参考になるかと思います。  
〇型となっている数字の部分がアクセント核位置になります。  
https://tdmelodic.readthedocs.io/ja/latest/pages/introduction.html  

成功した場合の返り値は単語に割り当てられるUUIDの文字列になります。

```bash
surface="test"
pronunciation="テスト"
accent_type="1"

curl -s -X POST "localhost:50021/user_dict_word" \
    --get \
    --data-urlencode "surface=$surface" \
    --data-urlencode "pronunciation=$pronunciation" \
    --data-urlencode "accent_type=$accent_type"
```

#### 単語修正

`/user_dict_word/{word_uuid}`にPUTリクエストを投げる事でユーザー辞書の単語を修正することができます。  
URLパラメータとして、以下が必要です。
- surface （辞書に登録するワード）
- pronunciation （カタカナでの読み方）
- accent_type （アクセント核位置、整数）

word_uuidは単語追加時に確認できるほか、ユーザー辞書を参照することでも確認できます。  
成功した場合の返り値は`204 No Content`になります。

```bash
surface="test2"
pronunciation="テストツー"
accent_type="2"
# 環境によってword_uuidは適宜書き換えてください
word_uuid="cce59b5f-86ab-42b9-bb75-9fd3407f1e2d"

curl -s -X PUT "localhost:50021/user_dict_word/$word_uuid" \
    --get \
    --data-urlencode "surface=$surface" \
    --data-urlencode "pronunciation=$pronunciation" \
    --data-urlencode "accent_type=$accent_type"
```

#### 単語削除

`/user_dict_word/{word_uuid}`にDELETEリクエストを投げる事でユーザー辞書の単語を削除することができます。  

word_uuidは単語追加時に確認できるほか、ユーザー辞書を参照することでも確認できます。  
成功した場合の返り値は`204 No Content`になります。

```bash
# 環境によってword_uuidは適宜書き換えてください
word_uuid="cce59b5f-86ab-42b9-bb75-9fd3407f1e2d"

curl -s -X DELETE "localhost:50021/user_dict_word/$word_uuid"
```

### プリセット機能について

`presets.yaml`を編集することで話者や話速などのプリセットを使うことができます。

```bash
echo -n "プリセットをうまく活用すれば、サードパーティ間で同じ設定を使うことができます" >text.txt

# プリセット情報を取得
curl -s -X GET "localhost:50021/presets" > presets.json

preset_id=$(cat presets.json | sed -r 's/^.+"id"\:\s?([0-9]+?).+$/\1/g')
style_id=$(cat presets.json | sed -r 's/^.+"style_id"\:\s?([0-9]+?).+$/\1/g')

# AudioQueryの取得
curl -s \
    -X POST \
    "localhost:50021/audio_query_from_preset?preset_id=$preset_id"\
    --get --data-urlencode text@text.txt \
    > query.json

# 音声合成
curl -s \
    -H "Content-Type: application/json" \
    -X POST \
    -d @query.json \
    "localhost:50021/synthesis?speaker=$style_id" \
    > audio.wav
```

- `speaker_uuid`は、`/speakers`で確認できます
- `id`は重複してはいけません
- エンジン起動後にファイルを書き換えるとエンジンに反映されます

### 2 人の話者でモーフィングするサンプルコード

`/synthesis_morphing`では、2 人の話者でそれぞれ合成された音声を元に、モーフィングした音声を生成します。

```bash
echo -n "モーフィングを利用することで、２つの声を混ぜることができます。" > text.txt

curl -s \
    -X POST \
    "localhost:50021/audio_query?speaker=0"\
    --get --data-urlencode text@text.txt \
    > query.json

# 元の話者での合成結果
curl -s \
    -H "Content-Type: application/json" \
    -X POST \
    -d @query.json \
    "localhost:50021/synthesis?speaker=0" \
    > audio.wav

export MORPH_RATE=0.5

# 話者2人分の音声合成+WORLDによる音声分析が入るため時間が掛かるので注意
curl -s \
    -H "Content-Type: application/json" \
    -X POST \
    -d @query.json \
    "localhost:50021/synthesis_morphing?base_speaker=0&target_speaker=1&morph_rate=$MORPH_RATE" \
    > audio.wav

export MORPH_RATE=0.9

# query、base_speaker、target_speakerが同じ場合はキャッシュが使用されるため比較的高速に生成される
curl -s \
    -H "Content-Type: application/json" \
    -X POST \
    -d @query.json \
    "localhost:50021/synthesis_morphing?base_speaker=0&target_speaker=1&morph_rate=$MORPH_RATE" \
    > audio.wav
```

### 話者の追加情報を取得するサンプルコード

追加情報の中の portrait.png を取得するコードです。  
（[jq](https://stedolan.github.io/jq/)を使用して json をパースしています。）

```bash
curl -s -X GET "localhost:50021/speaker_info?speaker_uuid=7ffcb7ce-00ec-4bdc-82cd-45a8889e43ff" \
    | jq  -r ".portrait" \
    | base64 -d \
    > portrait.png
```

### キャンセル可能な音声合成

`/cancellable_synthesis`では通信を切断した場合に即座に計算リソースが開放されます。  
(`/synthesis`では通信を切断しても最後まで音声合成の計算が行われます)  
この API は実験的機能であり、エンジン起動時に引数で`--enable_cancellable_synthesis`を指定しないと有効化されません。  
音声合成に必要なパラメータは`/synthesis`と同様です。

## アップデート

エンジンディレクトリ内にあるファイルを全て消去し、新しいものに置き換えてください。

## Docker イメージ

### CPU

```bash
docker pull voicevox/voicevox_engine:cpu-ubuntu20.04-latest
docker run --rm -it -p '127.0.0.1:50021:50021' voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```

### GPU

```bash
docker pull voicevox/voicevox_engine:nvidia-ubuntu20.04-latest
docker run --rm --gpus all -p '127.0.0.1:50021:50021' voicevox/voicevox_engine:nvidia-ubuntu20.04-latest
```

## 貢献者の方へ

Issue を解決するプルリクエストを作成される際は、別の方と同じ Issue に取り組むことを避けるため、
Issue 側で取り組み始めたことを伝えるか、最初に Draft プルリクエストを作成してください。

## 環境構築

`Python 3.8.10` を用いて開発されています。
インストールするには、各 OS ごとの C/C++ コンパイラ、CMake が必要になります。

```bash
# 開発に必要なライブラリのインストール
python -m pip install -r requirements-test.txt

# とりあえず実行したいだけなら代わりにこちら
python -m pip install -r requirements.txt
```

## 実行

コマンドライン引数の詳細は以下のコマンドで確認してください。

```bash
python run.py --help
```

```bash
# 製品版 VOICEVOX でサーバーを起動
VOICEVOX_DIR="C:/path/to/voicevox" # 製品版 VOICEVOX ディレクトリのパス
python run.py --voicevox_dir=$VOICEVOX_DIR
```

<!-- 差し替え可能な音声ライブラリまたはその仕様が公開されたらコメントを外す
```bash
# 音声ライブラリを差し替える
VOICELIB_DIR="C:/path/to/your/tts-model"
python run.py --voicevox_dir=$VOICEVOX_DIR --voicelib_dir=$VOICELIB_DIR
```
-->

```bash
# モックでサーバー起動
python run.py --enable_mock
```

```bash
# ログをUTF8に変更
python run.py --output_log_utf8
# もしくは VV_OUTPUT_LOG_UTF8=1 python run.py
```

### CPU スレッド数を指定する

CPU スレッド数が未指定の場合は、論理コア数の半分か物理コア数が使われます。（殆どの CPU で、これは全体の処理能力の半分です）  
もし IaaS 上で実行していたり、専用サーバーで実行している場合など、  
VOICEVOX ENGINE が使う処理能力を調節したい場合は、CPU スレッド数を指定することで実現できます。

- 実行時引数で指定する

  ```bash
  python run.py --voicevox_dir=$VOICEVOX_DIR --cpu_num_threads=4
  ```

- 環境変数で指定する
  ```bash
  export VV_CPU_NUM_THREADS=4
  python run.py --voicevox_dir=$VOICEVOX_DIR
  ```

### 過去のバージョンのコアを使う
VOICEVOX Core 0.5.4以降のコアを使用する事が可能です。  
Macでのlibtorch版コアのサポートはしていません。

#### 過去のバイナリを指定する
製品版VOICEVOXもしくはコンパイル済みエンジンのディレクトリを`--voicevox_dir`引数で指定すると、そのバージョンのコアが使用されます。
```bash
python run.py --voicevox_dir="/path/to/voicevox"
```
Macでは、`DYLD_LIBRARY_PATH`の指定が必要です。
```bash
DYLD_LIBRARY_PATH="/path/to/voicevox" python run.py --voicevox_dir="/path/to/voicevox"
```

#### 音声ライブラリを直接指定する
[VOICEVOX Coreのzipファイル](https://github.com/VOICEVOX/voicevox_core/releases)を解凍したディレクトリを`--voicelib_dir`引数で指定します。  
また、コアのバージョンに合わせて、[libtorch](https://pytorch.org/)や[onnxruntime](https://github.com/microsoft/onnxruntime)のディレクトリを`--runtime_dir`引数で指定します。  
ただし、システムの探索パス上にlibtorch、onnxruntimeがある場合、`--runtime_dir`引数の指定は不要です。  
`--voicelib_dir`引数、`--runtime_dir`引数は複数回使用可能です。   
APIエンドポイントでコアのバージョンを指定する場合は`core_version`引数を指定してください。（未指定の場合は最新のコアが使用されます）
```bash
python run.py --voicelib_dir="/path/to/voicevox_core" --runtime_dir="/path/to/libtorch_or_onnx"
```
Macでは、`--runtime_dir`引数の代わりに`DYLD_LIBRARY_PATH`の指定が必要です。
```bash
DYLD_LIBRARY_PATH="/path/to/onnx" python run.py --voicelib_dir="/path/to/voicevox_core"
```

## コードフォーマット

このソフトウェアでは、リモートにプッシュする前にコードフォーマットを確認する仕組み(静的解析ツール)を利用できます。
利用するには、開発に必要なライブラリのインストールに加えて、以下のコマンドを実行してください。
プルリクエストを作成する際は、利用することを推奨します。

```bash
pre-commit install -t pre-push
```

エラーが出た際は、以下のコマンドで修正することが可能です。なお、完全に修正できるわけではないので注意してください。

```bash
pysen run format lint
```

## API ドキュメントの更新

[API ドキュメント](https://voicevox.github.io/voicevox_engine/api/)（実体は`docs/api/index.html`）の内容を更新します。

```bash
python make_docs.py
```

## ビルド

この方法でビルドしたものは、リリースで公開されているものとは異なります。
また、GPUで利用するにはcuDNNやCUDA、DirectMLなどのライブラリが追加で必要となります。

```bash
python -m pip install -r requirements-dev.txt

python generate_licenses.py > licenses.json

# ビルド自体はLIBCORE_PATH及びLIBONNXRUNTIME_PATHの指定がなくても可能です
LIBCORE_PATH="/path/to/libcore" \
    LIBONNXRUNTIME_PATH="/path/to/libonnxruntime" \
    pyinstaller --noconfirm run.spec
```

## 依存関係

### 更新

pip-tools を用いて依存ライブラリのバージョンを固定しています。
`requirements*.in`ファイルを修正後、以下のコマンドで更新できます。

```bash
# pip>=22 の場合 pip-tools がエラーになります
pip-compile requirements.in  # こちらを更新する場合は下２つも更新する必要があります。
pip-compile requirements-dev.in
pip-compile requirements-test.in
```

### ライセンス

依存ライブラリは「コアビルド時にリンクして一体化しても、コア部のコード非公開 OK」なライセンスを持つ必要があります。  
主要ライセンスの可否は以下の通りです。

- MIT/Apache/BSD-3: OK
- LGPL: OK （コアと動的分離されているため）
- GPL: NG （全関連コードの公開が必要なため）

## ユーザー辞書の更新について

以下のコマンドで openjtalk のユーザー辞書をコンパイルできます。

```bash
python -c "import pyopenjtalk; pyopenjtalk.create_user_dict('default.csv','user.dic')"
```

## GitHub Actions

### Secrets

| name               | description                                                             |
| :----------------- | :---------------------------------------------------------------------- |
| DOCKERHUB_USERNAME | Docker Hub ユーザ名                                                     |
| DOCKERHUB_TOKEN    | [Docker Hub アクセストークン](https://hub.docker.com/settings/security) |

## ライセンス

LGPL v3 と、ソースコードの公開が不要な別ライセンスのデュアルライセンスです。
別ライセンスを取得したい場合は、ヒホ（twitter: @hiho_karuta）に求めてください。
