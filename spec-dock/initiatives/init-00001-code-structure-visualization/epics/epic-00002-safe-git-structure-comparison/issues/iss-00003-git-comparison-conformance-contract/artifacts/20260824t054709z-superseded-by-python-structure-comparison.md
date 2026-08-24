---
種別: artifact
ID: "20260824t054709z"
タイトル: "Superseded By Python Structure Comparison"
状態: "accepted"
作成者: "iwasawayuuta"
最終更新: "2026-08-24"
親: ["iss-00003"]
template: "blank"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260824t054709z Superseded By Python Structure Comparison

## 結論

`iss-00003` / GitHub #3は、ChatGPT Use Strictによるvertical Issue再分割でsupersedeされた。独立したcontract-only Issueとして実装しない。

## 後継

- successor SpecDock node: `iss-00005`
- successor GitHub Issue: `#5`
- successor title: `Compare Python Structure Changes Safely`
- stable package key: `ISSUE-02`

## 根拠

旧Issueが意図したnamed Git comparison、fail-closed endpoint resolution、read-only Git、dual semantic snapshotの契約は、`iss-00005`のCLI入力からPython semantic JSON/PlantUML、影響探索、manifest、受入テストまでのvertical outcomeへ統合された。旧R/D/P templateは後継へ流用していない。

## 処置

- local nodeと本Artifactを監査履歴として保持する。
- GitHub #3へ後継#5を記録してcloseする。
- dependency DAGには旧Issueを含めない。
