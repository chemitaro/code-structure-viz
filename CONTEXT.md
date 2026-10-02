# CodeStructureViz

ソースを実行せずにコード構造を観測し、検証した構造と観測範囲を利用者へ伝える文脈です。

## Language

**取得inventory（Acquired inventory）**:
一回の観測で取得を完了したProjectとFileの完全な一覧です。構造解析の成功範囲を意味しません。
_Avoid_: 公開model、safe subset

**safe semantic subset**:
解析失敗の影響から独立して安全と確認でき、公開できる構造の集合です。取得inventoryの完全性とは別の概念です。
_Avoid_: 全取得一覧、欠落を成功扱いしたmodel

**proof-only record**:
観測範囲や除外理由の検証に必要で、公開する構造の集合には属さないrecordです。
_Avoid_: 未観測record、公開record

**partial-safe snapshot**:
解析失敗を明示したうえで、影響範囲を切り分けて公開する安全な構造snapshotです。完全な解析成功ではありません。
_Avoid_: complete-empty、取得途中のprefix
