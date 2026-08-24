---
種別: artifact
ID: "20260824t054311z"
タイトル: "Adoption Log ChatGPT Strict Specification Pack"
状態: "complete"
作成者: "iwasawayuuta"
最終更新: "2026-08-24"
親: ["init-00001"]
template: "blank"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260824t054311z Adoption Log ChatGPT Strict Specification Pack

## 採用対象

- source of truth: connected GitHub `chemitaro/code-structure-viz` / `main`
- exact baseline SHA: `7951ddabc2e6a3d66edb77eada7c6c16923264f7`
- ChatGPT Use Strict sessions: `code-structure-viz-spec-pack`, `code-structure-viz-spec-pack-2`
- complete replacement ZIP: `code-structure-viz-complete-specification-pack-v2.zip`
- outer SHA-256: `a3f9ff9d98271ae7c78c10b3e86e77c4fb90e713fe79de352e3f0e04ca9bc0aa`

## 受入検証

- ZIPは48 regular files。absolute path、path traversal、duplicate entry、symlinkは0件。
- `CHECKSUMS.sha256`が自身を除く47 filesすべてで一致。
- `SOURCE-BASELINE.json`のcanonical R/D/P 9件が採用直前のrepository bytesと一致。
- UTF-8/LF、final LF、trailing whitespaceなし、template placeholderなしを確認。
- Initiative 1件、Epic 1件、vertical Issue 7件、dependency edge 9件、cycle 0件。
- 9件の説明HTMLを公式`validate-plantuml-html.mjs`で検証し、static contract、PlantUML inline SVG rendering、click/keyboard zoom、bounds、focus trap、dismissal、focus restorationが9/9 PASS。
- 製品機能としてのHTML report/command/Tailscale publicationはR/D/Pから除外。説明HTMLは仕様evidenceとしてのみ採用。

## Issue identity mapping

| Stable key | SpecDock ID | GitHub | Metadata title | Canonical specification title |
| --- | --- | --- | --- | --- |
| ISSUE-01 | iss-00004 | #4 | Generate Python Structure Snapshots | 同左 |
| ISSUE-02 | iss-00005 | #5 | Compare Python Structure Changes Safely | 同左 |
| ISSUE-03 | iss-00006 | #6 | Generate SQLAlchemy ER Snapshots | 同左 |
| ISSUE-04 | iss-00007 | #7 | Compare SQLAlchemy ER Changes | 同左 |
| ISSUE-05 | iss-00008 | #8 | Generate Nextjs Component Snapshots | Generate Next.js Component Snapshots |
| ISSUE-06 | iss-00009 | #9 | Compare Nextjs Component Changes | Compare Next.js Component Changes |
| ISSUE-07 | iss-00010 | #10 | Run Unified Multi Domain Structure Comparison | Run Unified Multi-Domain Structure Comparison |

`Next.js`と`Multi-Domain`を含むpackage推奨titleは、SpecDock CLIのtitle grammarに適合しない。node/GitHub metadata titleだけを上表のとおり正規化し、R/D/P、HTML、slug、`package_sequence_key`、trace ID、技術本文は変更していない。

## Identity materialization

各IssueのR/D/Pへ適用した変更は、frontmatter `ID`、H1先頭scope ID、frontmatter `関連GitHub`の3箇所だけである。`package_sequence_key`とすべての`Ixx-*` trace IDを保持した。

| Stable key | design SHA-256 | plan SHA-256 | requirement SHA-256 |
| --- | --- | --- | --- |
| ISSUE-01 | `7fe5420fb05bec1d42083b82292bac00165644180ca75060a10e1001afe39f96` | `fea33310288e5cbda16bea6f0621efe6fb8ec6856e5fc1de9aa542755a0fb7e1` | `5c78fd50fee26eea35c7ecc0e84dcb0b9c0bde964a51899b470ee05973da2a98` |
| ISSUE-02 | `5761092019c2503156129088816bb9bff8708d4a7389d3dc638fe68ef1ae6085` | `bd2fb5fcde05fcb8e2c88d620cbaa7f8f4cbf1d8b055662c990f861c916cb4f5` | `14390bd22ab707efabeec53d767f1fd4c8ffa8fe31edb437c1a76468e42f96f1` |
| ISSUE-03 | `936943bd99d1b6c922fbe3e563150b1847716b8f5a53f1d3da7778973a66160a` | `fddf0f9c57f1fb8caa932d7fa699d982425cde4e2e73c405423823b72a2a33c9` | `a026ab52262cbc1f24d44f4ad1bd81feb1a0002c0b8b9ac66062427986a4e5bb` |
| ISSUE-04 | `fe8e5d183f46355076ed65f6c41ed8d72b193c768f8f3f2f5f82980d083bad7f` | `686f77cca636bc5daed03eb71da40eb801a7ab488e115a375efd4b77d1dfdf87` | `4672ec804e56916c0e478d93fe8cb70ef9c4f8edd01b63c63e5182b8a953ff04` |
| ISSUE-05 | `c34d019a388109a6ef4b4afbbdc91fbc22a563650f4dac971f47de6f4668fea8` | `5f79aa9c0511482287a3b8252ec74bfec60237f0d1532431d76710a69507c843` | `3dda855e962655181a7b93f6b970805e528e0ff41b5d718efc247a999aaeffdf` |
| ISSUE-06 | `861ea9cdbdc40c6734498ba809055ea47ec0c4215fda3a1cd1c5fce3ecd9e517` | `aba78fc5fc12dd81e86c6d584035f0ab1a126da6e3cd47288662d87213465fc0` | `81111b09b89cef9003c719191f8af3a88f3374b2857d596fe4cba8028bd7597f` |
| ISSUE-07 | `61cb2f94755385ec24ccfc84ac10734cfb8f74e05b84924f3fd18eeb11188060` | `e3bbaeae0ced57b38410118ca467ed2aa2835d5f59daee9c5527fc5deb2600a1` | `ce03d95abfd4f1e2ed5248949688ad4447459b96560de04ab52a7350a7007a5b` |

## Dependency storage

Package DAGの矢印はprerequisiteからconsumerを指す。SpecDockの`.meta.json.depends_on`はconsumerからprerequisiteを保存するため、9辺を正規に反転してcommand-firstで登録した。

## 保持と旧Issue

- interview 1件とaccepted ADR 8件は`SOURCE-BASELINE.json`のbytesを保持する。
- existing `.meta.json`、`report.md`、SpecDock runtime/templates/guides/rulesは直接編集しない。
- provisional `iss-00003`の有用なGit比較契約は`iss-00005`へ統合した。旧nodeは監査履歴として保持し、superseded-by evidenceを記録してGitHub #3をcloseする。
