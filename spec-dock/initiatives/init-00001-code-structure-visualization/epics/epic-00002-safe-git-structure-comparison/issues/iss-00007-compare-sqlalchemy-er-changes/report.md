---
種別: レポート（Issue）
ID: "iss-00007"
タイトル: "Compare SQLAlchemy ER Changes"
関連GitHub: ["#7"]
最終更新: "2026-08-31"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00002", "init-00001"]
---

# Result Summary

詳細: [Report Guide](../../../../../../docs/authoring/report.md)

## Outcome

- SQLAlchemy diffを既存Git comparison lifecycleへ接続し、table・row・relation deltaとimpact
  contextをsemantic JSON / PlantUMLで公開する実装を完了した。
- diff PlantUMLはfieldを可視表示し、changed rowをadded=`DarkGreen`、removed=`DarkRed`、
  modified=`DarkGoldenRod`の文字色とmarkerで区別する。
- 通常のSQLAlchemy schema/table名に含まれる`_`をsnapshot/diffで可読表示し、`.`および
  literal escape tokenとのinjectivityを維持した。semantic JSON、ID、aliasは変更していない。
- added背景をSQLAlchemy tableとPython class/noteで`#E8F5E9`へ統一した。Python member行、
  removed/modified/context/movedの既存配色は変更していない。
- writerはSQLAlchemy table markerと背景色、およびrow markerと文字色の閉じた対応だけを受理する。

## Verification

- focused: 145 passed
- repository-wide: `uv run pytest -q` — 963 passed, 1 skipped
- `uv run ruff format --check .` — 146 files formatted
- `uv run ruff check .` — passed
- `uv run mypy src tests` — 134 source files、issueなし
- `uv build --offline` — sdist / wheel生成成功
- `./spec-dock/scripts/spec-dock validate` — nodes=10、passed
- 退職費用project由来のcompatibility preview 2例を新rendererで再生成し、生成直後の
  `sqlalchemy.diff.puml` SHA-256がmanifestと一致することを確認した。PlantUML 1.2025.10へ
  未加工のまま入力し、PNG/SVGでunderscore、淡緑背景、行文字色、impact contextを目視確認した。
- 対象projectは検査前後とも`develop`、`origin/develop`と同期、cleanである。

## Residual Risks / Follow-ups

- 退職費用projectの実commit range直接比較は、ER対象外を含むchanged-pathのUnicode正規化衝突に
  より`CSV-DIFF-003`でfail-closedとなる。今回の目視確認は、前回と同じく実テーブル名・field・
  relationを保持して未対応宣言だけを単純化したcompatibility previewであり、完全解析の代替ではない。
- literal `_Uxxxx_`を名前そのものに含む特殊識別子は、renderer-owned escapeとの衝突を避けるため
  token先頭の`_`を保護表現にする。
- Python member行のPlantUML色suffixは既存挙動のまま残し、今回の背景色修正には含めていない。
