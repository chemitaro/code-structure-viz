# Next Unicode NFC profile v1

Issue #8 のパスと文字列を、実行環境の Unicode database に依存せず正規化する契約です。
production helper は `src/code_structure_viz/core/unicode_15_0_nfc.py`、独立したreference oracle は
`tests/contracts/unicode_15_0_nfc.py` に置き、両者のtable digestとfull-scalar known-answerを検証します。

## 固定する意味

Unicode は **15.0.0**、正規化形式は **NFC**、profile ID は
`unicode-15.0.0-nfc-v1`、algorithm version は `unicode-nfc-15.0.0` です。
NFC は文字を canonical decomposition へ展開し、結合クラス順に並べ、
遮られていない組だけを canonical composition で合成します。
互換文字まで置き換える NFKC は使用しません。

たとえば `か + U+3099` は `が` になります。Hangul の L/V/T 結合も行います。
ただし `U+1100 U+0301 U+1161` の中央の結合文字を飛び越して L/V を合成してはいけません。
単独コードポイントのテストだけでは、この誤りを検出できません。

## データと出典

production implementation は [unicode_15_0_nfc.py](../../src/code_structure_viz/core/unicode_15_0_nfc.py)、
独立reference implementation は [unicode_15_0_nfc.py](../../tests/contracts/unicode_15_0_nfc.py) です。
二つの実装は同じtable bytesからimportせず、契約テストがdigest・scalar KAT・path edgeを照合します。
圧縮JSONには非ゼロの canonical combining class 922件、canonical decomposition
2,061件、Hangulを除く composition pair 941件を含みます。Hangul は規定のアルゴリズムで処理します。

2026-09-08 JST に次の公式ファイルを取得し、表の全項目を独立に照合しました。

| 入力 | SHA-256 |
| --- | --- |
| [UnicodeData.txt](https://www.unicode.org/Public/15.0.0/ucd/UnicodeData.txt) | `806e9aed65037197f1ec85e12be6e8cd870fc5608b4de0fffd990f689f376a73` |
| [DerivedNormalizationProps.txt](https://www.unicode.org/Public/15.0.0/ucd/DerivedNormalizationProps.txt) | `d5687a48c95c7d6e1ec59cb29c0f2e8b052018eb069a4371b7368d0561e12a29` |
| [NormalizationTest.txt](https://www.unicode.org/Public/15.0.0/ucd/NormalizationTest.txt) | `fb9ac8cc154a80cad6caac9897af55a4e75176af6f4e2bb6edc2bf8b1d57f326` |

元データの表記は「© 2022 Unicode®, Inc.」です。Unicode License V3の完全な通知はproduction module、
[third-party inventory](../../THIRD_PARTY_LICENSES.md)、および
[unicode-license.txt](../../tests/fixtures/unicode-license.txt) に保存します。

表を再生成・照合する規則は次のとおりです。

1. UnicodeData のコードポイントを整数へ変換し、第4フィールドの非ゼロ値を `ccc` に格納します。
2. 第6フィールドが空でも `<...>` 付きでもない行を canonical decomposition として `decomp` に格納します。
3. DerivedNormalizationProps の `Full_Composition_Exclusion` 集合を展開します。
4. decomposition が2コードポイントで、対象が除外集合にない場合だけ、元のコードポイントを `compose` に格納します。
5. `ccc`/`decomp` のキーはコードポイントの10進文字列、`compose` のキーは2コードポイントの16進表記をカンマで連結した値です。表の照合はキー表記を正規化した後の全項目比較で行います。

production helperは実行時に `unicodedata`、追加ライブラリ、ネットワークを参照しません。

## 完全性を確かめる二つの証拠

| 証拠 | 意味 |
| --- | --- |
| 展開済み表のSHA-256 `877b34f03bc09c193fb9014c381b3d3d980dea0676b942b4d54f56c1e11a6eb2` | チェックイン済み canonical data のバイト同一性 |
| 全scalar KAT `61f9ea3772b20f223112b3709361f387cde38bf0c5b7c329aeae49fd0d7de3d5` | surrogate を除く各scalarについて、コードポイント4 byte・UTF-8出力長4 byte・出力bytesをbig-endian長付きで連結した結果 |
| 公式NormalizationTest 19,074行 | 複数scalarの並べ替え、結合阻止、composition exclusion、Hangulを含む NFC の5等式 |

公式行は [unicode_15_0_nfc_normalization.json](../../tests/fixtures/unicode_15_0_nfc_normalization.json)
にオフライン保存しています。source file の各行から `#` 以降のコメントを取り除き、
空行と `@` セクション行を除外し、最初の5列をセミコロンで連結します。
行間と末尾はLFとし、UTF-8 bytesをzlib圧縮・Base64化します。
展開した行列のSHA-256は `03401aff398e9a872eea23a1ab43a2fbd9abbf6ef521fbaff2d399db4bfabed5` です。

各行の `c1;c2;c3;c4;c5` に対して
`NFC(c1)=NFC(c2)=NFC(c3)=c2` と `NFC(c4)=NFC(c5)=c4` を検査します。
期待値は公式データであり、参照実装から生成しません。
テスト中はhostの `normalize`/`combining`/`decomposition` を呼ぶと失敗させます。

```sh
uv run pytest tests/contracts/test_unicode_15_0_nfc.py -q
uv run pytest tests/contracts/test_next_contracts.py -k round24_unicode -q
```

## 変更と引き継ぎ

NFC table/profile/algorithm の変更はsemantic compatibilityに影響するため、
[compatibility契約](next-compatibility-v1.md) と既知の期待値を同時に更新します。
Nodeの実行場所、FD番号などの実行ごとの値は、このprofileに混入させません。
Python production helperと独立reference oracleは同じ固定profileを検証します。将来Nodeへ正規化を実装する場合は、
このprofileとNode側の実装を別途照合し、Python同士の一致をNode適合の証拠として流用しません。
