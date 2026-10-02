---
種別: decision-candidate
ID: "20261002t011638z-03-decision-candidate"
タイトル: "Source inventory仕様レビューP1とFile/Module公開条件の判断"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-10-02"
親: ["iss-00008"]
template: "decision-candidate"
authority: "draft"
mirror_eligible: false
derived_from: ["20261002t011638z--source-inventory-review-result.json", "20261002t011638z-01--source-inventory-findings-analysis-result.md", "20261002t011638z-02--source-inventory-findings-evidence-packet.md"]
reflected_to: []
---

# 20261002t011638z-03-decision-candidate FileとModuleの公開条件

## 現在地と判断の要点

**仕様レビューはfail、P1が1件です。実装は再開していません。** Oracleプロセスの正常完了は仕様合格ではありません。要件・設計・計画と三つのv3契約は`a4efdc373a515801777c924a1d14675fda686955`へcommit/push済みです。

独立ChatGPT Spec Review Strictと、別会話のChatGPT Analyze Review Findings Strict（両方GPT-5.6 Sol/Pro）が、File自身の安全性だけでは公開model全体の整合性を保証できないと確認しました。主担当も旧source/proof/model/target validatorで照合・限定再現しました。

推奨は**A: Moduleとの所有関係も含めて公開Fileを決める**案です。完全な取得一覧は残し、元のtaint規則を変えず、対応Moduleが合法的に非公開のprogram Fileも公開modelから外します。ただし「File自身がuntaintedなら必ず公開」という採択済み新保証を変えるため、未採択候補に留めます。

## Context: 何が矛盾したか

File recordはpath/size/hash/roles等のsource情報です。Module recordはそのprogram Fileを解析した構造です。旧契約には「公開program File一件につき公開Moduleがちょうど一件」という保証があります。

失敗rootはFileのparse/readだけではありません。関係・export・境界の導出失敗では、File metadataはuntaintedのまま、対応Moduleとその従属構造だけがtaintedになる経路があります。ModuleからFileへの逆向きtaintは旧規則にありません。新SIは三つを同時要求しています。

1. File自身がtaint集合外なら必ず公開する。
2. tainted Moduleを公開しない。
3. 公開program Fileには必ず公開Moduleがある。

これらは同時には満たせません。独立Buttonを明示targetにし、Card側のModuleだけが失敗する例でも、Card Fileだけが公開に残って3へ違反します。これはPythonかTypeScriptかという言語の問題ではなく、公開集合の定義の問題です。

再現は旧record/proofのmandatory seeds/causal/fixed pointと公開cardinalityのdata-only証拠です。実TypeScript producer、full seal/transport/Core-v3、locality、実CLIの受入れではありません。target未指定の旧helperは全program Fileを暗黙targetとしてtyped missing failureへ進むケースもあります。「全入力で結果を生成できない」と断定せず、explicit safe targetの経路を判断根拠にします。

## Options

| 案 | Fileはuntainted、Moduleだけtaintedの例 | 維持する保証 | 変わる保証 / 影響 |
| --- | --- | --- | --- |
| **A 最推奨: 所有関係を閉じた公開投影** | File/Moduleとも非公開proofに保持。独立Buttonは公開可能。 | 元のtaint、公開File→Module、全取得所有権、partial-safe、全件予算。 | `F−T`全File公開を「構造上も公開可能なFileは全件公開」へ変更。 |
| B: metadata-only Fileを公開 | Fileだけ公開し、Module不在を合法にする。 | 全untainted File公開、元のtaint。 | 公開File→Moduleとconsumerの欠落判定を変更。新state/schemaが必須とは未立証。 |
| C: ModuleのtaintをFileへ逆伝播 | Fileもtaintedにして両方除外。 | `F_safe=F−T`、公開File→Module。 | closed root/causal/taint意味と他recordへの伝播範囲を変更。 |
| D: domain全体unavailable | Buttonも公開せずArtifact無し。 | 不整合modelを出さない。 | 独立安全領域のpartial-safe availabilityを失う。暫定fail-closed用途。 |

Aを推す理由は、問題がroot伝播でなく公開modelの所有関係にあるためです。同じ原則でnonFile root、伝播Module失敗、合法selection exclusionを扱い、rootごとの例外や偽File taintを追加せず、既存consumerの一対一を保持できます。source seal/request/private proofの完全inventoryと予算は失いません。

## Candidate: Aの具体化（全体未採択）

### 公開条件と親所有

`T_record`はfull inventoryから検証した旧record-level taint集合のままです。source情報の安全性とpublic modelへの公開可否を分けます。

- 非program Fileはsource-safeなら公開し、Module条件を加えない。
- program Fileはsource-safeで、同じproject/pathの正規Moduleがfull proof/selection/taintから独立に公開可能と導出できる場合に公開。
- 公開可能なFileは必ず公開。childがModule/Fileを同時に省略して公開数や予算を減らす自由はない。
- Moduleのdiscovery欠落/重複を「owner非公開なのでFile除外」で隠さない。既存限定typed target branchを除きfull baseで拒否。
- 全Projectは残し、公開`file_ids`のみ導出された公開Fileへfilter。Projectのtaint/除外は禁止。
- eligible Module集合は提出modelの有無ではなく、親がfull proof/source/selectionから先に導出し、提出modelとのexact equalityを検証。循環した自己正当化をしない。

### Partition / reasonの候補

三分割を維持し、excludedに「必要Moduleが合法的に非公開のFile」も含めます。

| File条件 | disposition / wire reason候補 |
| --- | --- |
| direct parse/read File root | `failed`、実root kind。従来どおり。 |
| File自身がtaintedでdirect failedでない | `excluded / tainted`。従来どおり。 |
| Fileはuntainted、required Moduleがfailure/taintで非公開 | `excluded / failed`。Fileの`taints`や`proof.failed`に偽rootを足さない。 |
| required Moduleが合法selection/unsupportedで非公開 | 立証したModuleの`not_selected`/`target_excluded`/`unsupported`と対応する既存excluded reason。任意除外は禁止。 |

この写像も未採択です。response-v1 closed excluded enumにliteralは実在し、shape上はwire-v2維持候補です。ただし意味/producer/validator一致は未実装。owner原因は親certificateで保持/再導出し、File自身のtaintや直接読込失敗に偽装しません。wire-v3、新public state/codeが必要なら暗黙追加せず再判断します。

### Target / count / versionの候補

- target無しの正当failureは全proofと必要localityを確認したpartial-safe。真のbase欠落/重複を空成功にしない。
- 独立safe targetは失敗側Module/Fileの非公開だけでdomain全体unavailableにしない。
- 明示targetの必要構造が失敗ならfull inventoryで検証後TARGET-001 unavailable/no-artifact。public subsetだけからmissingを捏造しない。
- summaryの`safe.files`は公開model File数。acquiredは全取得数/bytes、accountedは全proof-onlyも含む。summaryのfieldは増やさない。
- 未実装/未出荷v3/profile/producer0.2.0の計画identityは維持候補。修正後の集合に新partition/KATを固定し、旧v1/v2 hash/意味は不変。
- 元taint/locality/静的解析、A runtime、Python/SQLAlchemy、別ASSET未採択は維持。

### 採択後の順序

Current Requirement SI-REQ-002/003、Design SI、accepted ADR、admission/public-v3、Planを同じ意味へ整合し、docs-only checks、通常commit/pushを行います。同じreviewerへのStrict followupで`review_status=pass`後だけSI-03 TDDへ進みます。仕様passを累積A03/製品完成へ転用しません。

`analyze-review-findings/SKILL.md`の「Return material meaning changes to a human」、同references/requirements-design.mdの「Human decision」がcanonical design/public meaning変更をhumanへ戻す根拠です。Aを未採択のまま修復・実装しません。

## Evidenceと来歴

- exact reviewed SHA: `a4efdc373a515801777c924a1d14675fda686955`。
- reviewer: `issue8-source-inventory-spec-review`、fresh/19m34s/exit0、conversation `6abefcca-0874-83ee-8647-5b0518e3106d`。schema-valid fail/P1一件。原/保存copy SHA `2fff0ab48628233db38a58ed86ae279ba8fb3dff95601a1e247d7efc3663676b`。
- analyst: `issue8-source-projection-findings-analysis`、fresh別会話/8m02s/exit0、conversation `6abf0359-5378-83e8-8bf7-bd71f37d7c97`、promptSubmitted=true、prompt hash `f1a19dc223eddee72ae029670e2900aee17be0d93f5eb82066f8fb4c3fb366b9`。11必須H1、全516行読了。原/保存copy SHA `43abca5c7b3b9b4575f9a18dc6763557c5bb20d0da8329b4ce859dd955c2967c`。
- 両model/thinking picker verified=true、Pro strictFailClosed=true。UI観測でbackend identityを推論しない。
- 提出packetのWB原文SHAは`f37c0da5e44279a73e19c49b644d488a84af341e13aaa45570fe319f0d4c4d29`。tracked copyはdiff-checkのため末尾空行一行だけ除去し、SHAは`2d97640abe6f92d64c5effddcdea122cfea7c73b45a9d7f1c49e9539a4631de2`。原WBは変更しません。importsは`canonical=false`。`committed=true`はatomic file保存で、Git commit/pass/採択ではない。
- exact a4efdc3で34 schema/pointer tests（0.78s）、別2 taint/cardinality tests（0.20s）、文書7/links14/keys、SpecDock10 nodesはpass。新v3/全pytest/actual TS/CLIは未実施。
- module_relation/export_binding/boundary_derivationの三ケースでFile untainted、Module tainted、explicit safe target failure無し、public modelはunrelated missingで拒否。scratchのimport path/元fixture相互依存を修正してexit0、tracked guard/testは無変更。

## 助言の採否とskill利用記録

有効P1と`design-decision-required`はlocal traceに合致します。author Use Strictのsource案だけではnonFile Module rootを閉じ切れず、fresh Spec Reviewが矛盾を発見しました。専用findings分析は真偽/blocking/route/認可を分離し、target無しの断定を限定し、無断修復を止めた点で有効でした。

助言の「Bには新state/schemaが必要」は確定扱いしません。現schemaのshapeはFile/Module cardinalityを表さず、v3既存coverageで表現できるか未確認です。ただしBはconsumer guaranteeを変えます。既知の未実装v3を追加の仕様欠陥/P1にせず、production evidenceは後段gateへ残します。

analystからlocal native ID/harness sourceは見えませんでした。親がnative metadataのexact IDを記録し、以下へharnessを保存します。Git無視workbenchのGitHub404は期待された状態です。完全JSON/digestとconnector source traceによる意味分析は成立し、これをproduction認定に読み替えません。

## 再現コード（data-only / 非production）

既存repoの`.workbench/luna-max-implement/issue8-nextjs-snapshots/specs/nonfile-root-source-projection-check.py`へ保存し、`uv run --locked --group dev python <path>`で実行しました。script SHA `936e11e2bccb01efa2eff917d6b5de6407c0788dc54b5c01dcfff06a5a49f722`。結果全文は証拠packetにあります。

```python
"""Read-only falsification of SI-v3's retained File-to-Module constraint.

This exercises baseline record/proof algebra, not a nominal new Core-v3,
a frozen-TypeScript acceptance case, or a proposed implementation.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.contracts import next_reference_validation as v1
from tests.contracts.test_next_contracts import (
    _complete_proof,
    _discovered_index,
    _materialize_single_root_taints,
    _model,
)

base = _model()
# The original fixture links Button/Card.  Build an explicitly disjoint
# data-only record graph so a different selected target is genuinely safe.
base["relations"] = []
base["members"] = [record for record in base["members"] if record["kind"] != "import_binding"]
roles = v1.derive_boundary_roles(base)
for module in base["modules"]:
    module["derived_roles"] = roles[module["id"]]
counts = base["coverage"]["counts"]
for collection in v1.COLLECTIONS:
    counts[collection] = len(base[collection])
counts["published"] = sum(len(base[collection]) for collection in v1.COLLECTIONS)
counts["discovered"] = counts["published"]
assert v1.validate_model(base) == 4
evidence = []
for kind in ("module_relation", "export_binding", "boundary_derivation"):
    proof = _complete_proof(base)
    root = {
        "id": "next:failure:" + "c" * 64,
        "collection": "modules",
        "kind": kind,
        "path_ref": "src/Card.tsx",
        "record_ids": [],
    }
    discovered = _discovered_index(proof, base)
    root["record_ids"] = v1._derive_required_root_seed_ids(root, v1._record_index(discovered))
    proof["failure_roots"] = [root]
    _materialize_single_root_taints(proof, base)
    discovered = _discovered_index(proof, base)
    tainted = v1._derived_taint_fixed_point(proof, discovered)
    file = next(record for record in base["files"] if record["path"] == "src/Card.tsx")
    module = next(record for record in base["modules"] if record["path"] == "src/Card.tsx")
    assert module["id"] in tainted
    assert file["id"] not in tainted
    public = deepcopy(base)
    for collection in v1.COLLECTIONS:
        public[collection] = [
            record for record in public[collection] if record["id"] not in tainted
        ]
    assert public["files"] == base["files"]  # F_safe=F-T retains every File here.
    assert all(record["id"] != module["id"] for record in public["modules"])
    failure = v1.target_completeness_failure(public, ["path:src/Button.tsx"])
    assert failure is None
    exceptions = v1._target_missing_module_exceptions(
        public, ["path:src/Button.tsx"], failure
    )
    assert exceptions == (set(), set())
    try:
        v1.validate_model(public)
    except v1.NextTargetCompletenessFailure as exc:
        model_failure = {"type": type(exc).__name__, "failures": exc.failures}
    else:
        raise AssertionError("Expected retained public File-to-Module rule to reject")
    default_failure = v1.target_completeness_failure(public, [])
    assert default_failure is not None
    evidence.append({
        "root_kind": kind,
        "path": file["path"],
        "root_seed_count": len(root["record_ids"]),
        "file_tainted": False,
        "module_tainted": True,
        "safe_file_retained": True,
        "tainted_module_published": False,
        "explicit_safe_target_failure": None,
        "explicit_safe_target_missing_exemptions": [],
        "public_model_failure": model_failure,
        "no_explicit_target_baseline_failure": default_failure.failures,
    })
print(json.dumps({
    "baseline_model_validated": True,
    "mandatory_seeds_causal_fixed_point_checked": True,
    "cases": evidence,
    "not_proven": [
        "nominal Core-v3",
        "complete proof/source seal/transport",
        "actual frozen TypeScript root generation",
        "source locality",
        "production/public integration",
    ],
}, ensure_ascii=False, indent=2))
```

## Reflection

未採択です。正本の公開条件/taint/record契約は変更せず、Report/Planにreviewの実状態と判断先だけを記録します。人間がAまたは別案を選んだら、候補を直接authorityへ昇格せず、accepted ADRとCurrent R/D/Pへ再記述し、same-reviewer closureへ進みます。
