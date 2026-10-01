# 実装ブリーフ — A02-3 初期 public semantic-document-v2 / generic semantic-dispatcher-v2 reference slice

## 0. 検証済み実装基点

| 項目 | 固定値 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Branch | `iss-00008-generate-nextjs-component-snapshots` |
| 実装開始HEAD | `ae15deb505d610f74e7c59b506b001b5224c4235` |
| 選択単位 | A02-3 初期 public semantic-document-v2 / generic semantic-dispatcher-v2 reference slice |
| 実装者 | caller-reported `gpt-6.1-sol` / `max`。バックエンド認証値としては扱わない |
| Actor model | primary agentだけが実装する。subagentは使わない |
| Workflow | TDDを実行方式とし、Luna Max Implementは順序付けの参考にだけ使う |

GitHubコネクタで、分析開始前に指定repositoryの指定branch endpointからfull tip SHAを取得し、期待値と完全一致することを確認した。 分析完了後の再取得でも同じfull SHAが返り、分析中のbranch-tip変更はなかった。

この文書は、正本のRequirement／Design／Planを変更するものではなく、選択した一単位を実行可能な作業へ分解する companion brief である。実装そのものでも、独立レビュー証明でもない。正本全体とverified commit上のコード・テストを根拠にし、必要な文脈が欠ける場合は実装可能と偽らずblockerへ切り替える。attachments-bundle

**実装判定:** この選択単位は単独実行可能である。ただし、現行private requestが保持していないpublic config／depth／domain-config identityを、自由なdigestとして補わず同じdecision chainへ保持するため、後述する小さいparent-owned analysis-context leafをこのsliceの機械的必須依存として含める。

---

## 1. 目的と完了像

このsliceの出口は、次の4点が同じcheckpointで成立することである。

1. 既存の `ValidatedSemanticDecisionV2` だけを入力にして、availableなNext Core decisionから `code-structure-viz.semantic/v2` のpublic semantic document recordを生成できる。
2. 生成recordを、producerとは独立したvalidatorが同じsource／request／assets／same-process binding／Core gate／compatibilityから再計算して検証できる。
3. `semantic-v2.schema.json` が、
   - 既存Python／SQLAlchemyのv1 documentsをそのまま受理し、
   - Next-v2だけを新しいexact refで受理し、
   - Next-v1をmigration bypassとして受理しない。
4. 旧v1 schema、docs、ID／record／proof algorithms、Python／SQLAlchemyの既存挙動をbyte-identicalまたは回帰greenのまま維持する。

ここでいう「public semantic document」は**公開形式のdata record**であり、Artifactファイルの作成、LF付きexact publication bytes、manifest descriptor、stdout、exit code、publication transactionを意味しない。publication finalizerは別gateのまま残す。

---

## 2. 正本と非正本の境界

Requirement／Design／Planの各 `Current normative authority` が現在の単一正本であり、後続のRound履歴や未採択artifactを競合authorityとして使わない。PlanはA02-3をprovenance／public exact-ref closureとして位置付け、現時点では17-slot provenanceの初期sliceまでがGREEN、reader-owned prefixとpublic exact-ref closureは未完了としている。

採択済みADRは、利用者管理toolchainを信頼し、対象repositoryを実行しないlocal static-analysis model、same-process Node version observation、private staging、公開spawn、bounded capture／cleanupを採択している。同時に、取得していないverified-FD／actual-image attestationを偽らず、runtime変更を新versionへ明示移行することを要求する。attachments-bundle

A02 migration adjudicationは、semantic entity／proof definitions、identity versions、semantic algorithms、Unicode profileをv1のまま維持しつつ、Next semantic documentとgeneric dispatcherをv2へ移行する。旧`semantic-v1`のNext exact refへunionを追加する方式は採らない。attachments-bundle

`20261001t122836z-decision-candidate-a-source-prefix-asset-failure-adjudication.md`は未採択である。新しいASSET code、通常I/Oとpackage破損のfatal/unavailable境界、reader prefixは本sliceで採用・実装しない。

---

## 3. スコープ

### 3.1 含めるもの

| 分類 | 対象 |
|---|---|
| Public Next schema | `next-semantic-v2.schema.json` |
| Generic dispatcher | `semantic-v2.schema.json` |
| Public producer | availableな `ValidatedSemanticDecisionV2` からのrecord projection |
| Independent validator | schemaだけでなくowner join、digest、order、privacyを再計算 |
| Mechanically essential leaf | source／config／depth／run-contextを保持するprivate typed analysis context |
| Tests | nominal、empty、partial-safe、unavailable拒否、mutation、cross-version、registry regression |
| Documentation | `next-semantic-v2.md`、Plan／Report current section、durable evidence artifact |
| Checkpoint | 小さい一commit、ordinary push、clean pushed exact SHA |

### 3.2 含めないもの

- reader-owned request-independent source prefix
- 未採択asset failure policy、新diagnostic、新catalog
- run-decision-v2、publication-decision-v2、domain-manifest-v2
- root manifest、stdout-result-v2、run-summary変更
- Artifact作成・persist・publication transaction・selected-output measurement
- PlantUML v2
- production `src/`への接続
- Node／TypeScript／OS／CLIの実行受入れ
- package資材同梱、wheel／sdist、license closure
- A02全体の全matrix／full gate認定
- A03 independent ChatGPT Code Review Strict
- A04 production、A05 Issue acceptance
- Next semantic diff v2
- 旧v1 schema／documentの改変

---

## 4. verified commit上の既存owner chain

現行reference laneには次が既に存在する。

```text
SourceAcquisitionSeal
  + RetainedExecutionAssets
  -> RetainedRequestFrameV2
  -> ValidatedTransportCandidateV2
  -> ValidatedSemanticDecisionV2
```

`ValidatedTransportCandidateV2` はrequest frame、response frame、portable runtime bindingを保持するdata-join ownerであり、Core certificateではない。`ValidatedSemanticDecisionV2` は同じcandidate／source seal／assetsと、immutable Core gate／parent compatibilityを保持し、`validate_semantic_decision_v2` がgateとcompatibilityを再計算する。Core rejectionは別の `RejectedSemanticDecisionV2` であり、admitted gate／compatibility projectionを持たない。

compatibility v2はdocument／dispatcher identityを `code-structure-viz.semantic/v2` へ変更する一方、entity／props IDs、recognition／export／relation／fact等のalgorithm versionsを1のまま維持する。compatibilityはwhole-exchange candidateからparentが生成し、free runtime metadataやchild-authored descriptorを受理しない。

現行 `SourceAcquisitionSeal` はcanonical source plan bytes、plan digest、`SourceView`、source-view fingerprint、seal ID、applicabilityを保持する。public configのtargets／upstream depth／downstream depth／formatsは保持しない。

現行private request v2は、source-sealed projects／files、targets、limits、run contextを持つが、public `run_fingerprint`、public domain-config record、upstream／downstream depthを持たない。attachments-bundle 一方、維持するpublic `next-snapshot-request/v1` shapeは、projects、targets、両depth、formats、limits、trusted-environment digest、source plan／digest、domain-config digest、run fingerprintを要求する。attachments-bundle

したがって、rendererがdepthやdomain-config digestを自由値・zero default・fixture constantで補う実装は禁止する。これを閉じるため、次のprivate parent ownerを追加する。

---

## 5. 必須private leaf: retained analysis context

### 5.1 新規提案symbol

`tests/contracts/next_runtime_v2_reference.py` に次を追加する。以下は**提案する新symbol**であり、verified commitにはまだ存在しない。

```python
@dataclass(frozen=True, slots=True, init=False)
class RetainedNextAnalysisContextV2:
    ...

def retain_next_analysis_context_v2(
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
    *,
    targets: list[str],
    upstream_depth: int,
    downstream_depth: int,
    run_context: dict[str, Any],
) -> RetainedNextAnalysisContextV2:
    ...
```

`tests/contracts/next_runtime_v2_validation.py` に独立validatorを追加する。

```python
def validate_next_analysis_context_v2(
    context: RetainedNextAnalysisContextV2,
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
) -> None:
    ...
```

### 5.2 ownerが保持する内容

`RetainedNextAnalysisContextV2` は最低限、次をimmutable canonical bytesとして保持する。

- 完全な `code-structure-viz.domain-config/next/v1` success record
- canonical `NextRunContext/v1`
- `source_seal_id`
- `execution_asset_set_id`

公開getterはfresh copyを返す。

```python
def domain_config(self) -> dict[str, Any]: ...
def run_context(self) -> dict[str, Any]: ...
```

直接constructorは閉じる。`repr`へsource bytes、asset bytes、private stampを出さない。

### 5.3 domain-config recordの導出

factoryはcallerからdigestを受け取らず、次のrecordを同じseal／assets／intentから構築する。

| field | authority |
|---|---|
| `schema` | `code-structure-viz.domain-config/next/v1` |
| `request_independent` | `false` |
| `projects` | `seal.final_plan["projects"]` |
| `targets` | canonical validated input targets |
| `upstream_depth` | validated resolved input |
| `downstream_depth` | validated resolved input |
| `formats` | canonical `run_context["requested_formats"]` |
| `limits` | `seal.final_plan["limits"]` |
| `trusted_environment_digest` | `seal.final_plan`とsame retained assets descriptorのexact join |
| `source_plan` | `seal.final_plan` |
| `source_plan_digest` | `seal.plan_digest` |
| `config_resolution` | `seal.final_plan["config_resolution"]` |
| `domain_config_digest` | self fieldを除いたrecordのpinned canonical JSON SHA-256 |

depthはfactoryで暗黙default化しない。呼出側が解決済み値を明示し、既存v1 config semanticsとschemaへ通す。targetなし／depthの意味について現在のv1 validation helperと矛盾する値しか作れない場合は、そこで停止条件を発動し、zeroや1を推測しない。

### 5.4 private requestとの結合

既存 `build_request_frame_v2` を次の形へ狭める。

```python
def build_request_frame_v2(
    seal: SourceAcquisitionSeal,
    assets: RetainedExecutionAssets,
    analysis_context: RetainedNextAnalysisContextV2,
) -> RetainedRequestFrameV2:
    ...
```

旧 `targets=...`／`run_context=...` loose-argument overloadは残さない。全reference call siteをtyped contextへ移行する。

`RetainedRequestFrameV2` には `analysis_context` を `repr=False` で保持し、fresh owner accessorを追加する。

```python
def analysis_context(self) -> RetainedNextAnalysisContextV2: ...
```

`validate_request_frame_v2` は次を追加検証する。

1. contextがexact classである。
2. contextのsource／asset stampが実seal／assetsと一致する。
3. private requestのtargets、limits、run_context、trusted descriptorがcontextとexact-equalである。
4. contextのdomain config digestをvalidator側で再計算する。
5. requestの既存canonical bytes／request IDは従来どおり検証する。

depth／domain configはparent-owned metadataであり、private child requestへ新fieldとして挿入しない。したがって既存request v2 wire schemaを変更せず、同じtargets／run-contextで作る既存known requestのrequest ID、wire bytes、wire SHAは維持する。現行request contractは、実seal／retained assetsからcanonical frameを生成し、caller-selected identityをauthorityにしない設計である。attachments-bundle

---

## 6. Public semantic-document-v2 producer

### 6.1 新規提案ファイルとAPI

新規 `tests/contracts/next_public_semantic_v2_reference.py`:

```python
def project_public_semantic_document_v2(
    decision: ValidatedSemanticDecisionV2,
) -> dict[str, Any]:
    ...
```

この関数の入力は**decision一つだけ**とする。別引数としてsource、request、status、compatibility、run fingerprint、model、depth、configを受け取らない。

### 6.2 admission順序

producerは次の順序を守る。

1. `type(decision) is ValidatedSemanticDecisionV2` を要求する。
2. `validate_semantic_decision_v2(decision)` を実行し、保持gate／compatibilityを再照合する。
3. gateが次を満たすことを要求する。
   - `payload_available is True`
   - `outcome in {"complete", "partial_safe"}`
4. candidate、request frame、analysis context、seal、assets、runtime binding、semantic payloadを同じdecisionから取得する。
5. request frame／analysis contextをそれぞれ独立validatorへ通す。
6. public recordをfresh valueとして構築する。
7. producerのpostconditionとして独立 `validate_public_semantic_document_v2(record, decision)` を呼んでもよい。ただしvalidatorはproducerを呼んではならない。

次はdocumentを生成してはならない。

- target unavailable
- export unavailable
- entity-budget unavailable
- model-record rejection
- invalid Core payload
- `RejectedSemanticDecisionV2`
- transport failure
- duck decision
- forged decision gate
- foreign source／asset owner

このsliceでは、失敗時に新しいpublic diagnostic、typed unavailable record、empty success snapshotを作らない。内部referenceの `TypeError`／`ValueError` でprojectionを拒否し、public failure mappingは後続run/publication closureへ残す。

---

## 7. Public recordのfield-level契約

### 7.1 root

```json
{
  "type": "semantic_snapshot",
  "schema": "code-structure-viz.semantic/v2",
  "domain": "next",
  "document_kind": "snapshot"
}
```

### 7.2 source projection

同じdecisionの `SourceAcquisitionSeal` から次を作る。

```json
{
  "schema": "code-structure-viz.source-view/v1",
  "kind": "<seal.source_view.kind>",
  "head_commit": "<seal.source_view.head_commit or null>",
  "fingerprint": "<seal.source_view_fingerprint>",
  "file_count": "<len(seal.source_view.files)>"
}
```

`SourceView.fingerprint_value()` のprivate files／failures配列全体を公開しない。repository-relative source descriptorだけをpublic baseline shapeへ投影する。

### 7.3 public request projection

public requestのschema identityは維持する。

```json
{
  "schema": "code-structure-viz.next-snapshot-request/v1",
  "projects": "...",
  "targets": "...",
  "upstream_depth": "...",
  "downstream_depth": "...",
  "formats": "...",
  "limits": "...",
  "trusted_environment_digest": "...",
  "source_plan": "...",
  "source_plan_digest": "...",
  "domain_config_digest": "...",
  "run_fingerprint": "..."
}
```

| public field | 導出元 |
|---|---|
| `projects` | retained analysis contextのpublic domain config projects |
| `targets` | contextとprivate requestのexact-equal targets |
| `upstream_depth` / `downstream_depth` | context |
| `formats` | canonical run contextのrequested formats |
| `limits` | seal／context／private requestのexact-equal limits |
| `trusted_environment_digest` | seal plan、request trusted descriptor、binding、compatibilityのexact join |
| `source_plan` | seal.final_plan |
| `source_plan_digest` | seal.plan_digest |
| `domain_config_digest` | context recordから独立再計算 |
| `run_fingerprint` | 下記closed preimage |

public requestへprivate `request_id`、adapter request schema／protocol、`content_base64`を出さない。

### 7.4 run fingerprint

run fingerprintは、次の**12 fieldsだけ**のpinned canonical JSON SHA-256とする。

```json
{
  "source_view_fingerprint": "...",
  "source_plan_digest": "...",
  "domain_config_digest": "...",
  "projects": [],
  "targets": [],
  "formats": [],
  "stdout_selector": null,
  "limits": {},
  "node_version": "...",
  "typescript_version": "5.9.2",
  "adapter_version": "...",
  "protocol": "code-structure-viz.next-adapter/v2",
  "trusted_environment_digest": "..."
}
```

上の例は13 keysに見えるため、実装時にはDesign記載の列挙をそのままclosed key setとしてテストすること。Designの正本列挙は次である。

```text
source_view_fingerprint
source_plan_digest
domain_config_digest
projects
targets
formats
stdout_selector
limits
node_version
typescript_version
adapter_version
protocol
trusted_environment_digest
```

すなわち**13 fields**である。コメントや変数名で12と誤記しない。正本のpreimageはこの13項目で固定されている。

各値のauthorityは次とする。

| field | authority |
|---|---|
| `source_view_fingerprint` | decisionのseal |
| `source_plan_digest` | decisionのseal |
| `domain_config_digest` | retained analysis contextから再計算 |
| `projects` | private requestのsemantic project rows。public config project rowsへ置換しない |
| `targets` | private request／context exact join |
| `formats` | canonical run context |
| `stdout_selector` | canonical run context |
| `limits` | seal／request／context exact join |
| `node_version` | candidate runtime bindingのsame-process `node_observation.version` |
| `typescript_version` | retained trusted metadataの`5.9.2`。bindingの`typescript_identity == "typescript-5.9.2"`と照合 |
| `adapter_version` | request、retained adapter identity、binding adapterのexact join |
| `protocol` | request protocol、retained adapter identity、binding adapterのexact join |
| `trusted_environment_digest` | request descriptor、seal plan、binding、compatibilityのexact join |

preimageへ次を追加しない。

- Node candidate SHA
- runtime portable fingerprint
- compatibility ID
- request ID
- source seal ID
- Core gate、status、budget actual
- process policy／observation digest
- host-local path、private root、cwd
- PID、PGID、FD
- raw source、proof、response hash
- exception／traceback

callerから完成済みrun fingerprintを受け取らない。producerとvalidatorがそれぞれpreimageを組み立てる。共通の「expected record builder」は作らない。

### 7.5 status

| Core gate | public root |
|---|---|
| `outcome == "complete"` | `status: "complete"`。`incomplete_kind`なし |
| `outcome == "partial_safe"` | `status: "incomplete"`、`incomplete_kind: "partial_safe"` |
| `outcome == "payload_unavailable"` | document生成拒否 |

entity gateが保持する `original_outcome` と最終 `outcome` を混同しない。entity +1などで最終outcomeがunavailableなら、元がpartial-safeでも公開しない。

### 7.6 compatibilityとidentity versions

- `compatibility_descriptor` はdecisionが保持する `code-structure-viz.next-semantic-compatibility/v2` のfresh copy。
- `semantic_compatibility_id` はその `compatibility_id`。
- root `identity_versions` はcompatibility descriptorとsemantic payloadの両方にexact-equalでなければならない。
- v1 compatibility descriptor、v1 semantic schema、rehashed fake descriptor、別candidateのportable fingerprintを拒否する。
- compatibility preimageへsource／request／host-local factsを追加しない。

現行compatibility-v2 schemaは `semantic_schema=code-structure-viz.semantic/v2` と、v1 identity／algorithm definitionsへのexact refsを既に持つ。attachments-bundle

### 7.7 model projection

同じsemantic payloadのvalidated modelから次を投影する。

| public collection | source |
|---|---|
| `projects` | `model["projects"]` |
| `files` | `model["files"]` |
| `entities` | `model["modules"]` と `model["components"]` をfull ID UTF-8 orderでmerge |
| `members` | `model["members"]` |
| `relations` | `model["relations"]` |
| `facts` | `model["facts"]` |
| `coverage` | `model["coverage"]` |
| `diagnostics` | `model["diagnostics"]` |

`entities` は単純な `modules + components` concatenationではなく、両sorted collectionのID-order mergeとする。validatorは同じmergeを独立に再計算する。

それ以外のcollectionは、Coreが検証したsubmitted canonical orderをそのまま維持する。validator側でsubmitted arrayを先にsortしてから比較してはならない。

### 7.8 privacy

public documentに次を含めない。

- `content_base64`
- private semantic `proof`
- raw source bytes
- request／response envelope
- `request_id`
- child control／binding record
- process policy／observation
- host absolute path／private staging path／cwd
- PID／PGID／FD
- raw stdout／stderr
- Python exception message、class、traceback
- private owner stamps

closed JSON Schemaだけでなく、focused mutation testsでも拒否を証明する。

---

## 8. Independent validator

### 8.1 新規提案API

新規 `tests/contracts/next_public_semantic_v2_validation.py`:

```python
def validate_public_semantic_document_v2(
    value: dict[str, Any],
    decision: ValidatedSemanticDecisionV2,
) -> None:
    ...

def validate_semantic_dispatcher_v2(
    value: dict[str, Any],
) -> None:
    ...
```

必要なら次のshape-only helperを同ファイル内private symbolとして持てる。

```python
def _validate_next_semantic_v2_shape(value: object) -> None: ...
def _semantic_v2_registry() -> Registry: ...
```

### 8.2 独立性

`validate_public_semantic_document_v2` は `project_public_semantic_document_v2` を呼ばない。producerが作ったexpected recordを比較対象に使わない。

実行順序は次とする。

1. exact decision typeを検証。
2. `validate_semantic_decision_v2` を再実行。
3. document schemaをlocal closed registryで検証。
4. analysis context、request frame、seal、assetsのowner joinsを検証。
5. available gateとstatus mappingを再計算。
6. source projectionを再計算。
7. domain config digestを再計算。
8. 13-field run-fingerprint preimageを独立に組み立て、hashを再計算。
9. compatibilityをcandidateへ再結合。
10. model collectionsとentities mergeを再計算。
11. submitted orderを直接比較。
12. private fieldが存在しないことをclosed schemaとtargeted checksで確認。

producerとvalidatorが共有してよいのは次だけである。

- pinned canonical JSON codec
- SHA-256 primitive
- wire-independent v1 path／target／record-ID helpers
- local schema registry loader
- fixed constants

public document全体、request projection、run-fingerprint preimage、entities projectionを返す共通builderは作らない。

### 8.3 dispatcher validatorとの違い

`validate_semantic_dispatcher_v2` はgeneric schema routingだけを担当する。Next owner joinsを証明しない。

- 外部から読んだdocumentのversion／domain route確認: dispatcher validator
- 実decisionから作ったNext documentのsource／request／gate／compatibility証明: public semantic validator

schema passだけをNext public admissionと呼ばない。

---

## 9. JSON Schemas

### 9.1 `schemas/next-semantic-v2.schema.json`

新規schemaの要点:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:code-structure-viz:schema:next-semantic-v2",
  "type": "object",
  "additionalProperties": false
}
```

root fieldsとstatus branchは旧Next public document baselineを維持し、次だけを移行する。

| field | v2 |
|---|---|
| `schema` | `code-structure-viz.semantic/v2` |
| `compatibility_descriptor` | exact `$ref` to `next-compatibility-v2` |
| `semantic_compatibility_id` | digest |
| entity／record defs | `next-semantic-v1#/$defs/...` をexact reuse |
| request | `next-config-v1#/$defs/snapshot_request` + `run_fingerprint` required |
| source | unchanged source-view/v1 shape |
| identity versions | unchanged v1 fragment |

以下のv1 fragmentsを参照し、v2コピーを作らない。

- `identity_versions`
- `source`
- `project`
- `file`
- `module`
- `component`
- member variants
- relation variants
- facts
- coverage
- diagnostic
- digest／ID／path definitions

document schema versionとrecord algorithm versionを混同しない。

### 9.2 `schemas/semantic-v2.schema.json`

generic dispatcherは次のtwo-route unionとする。

```text
route 1:
  exact semantic-v1 document
  AND domain in {python, sqlalchemy}

route 2:
  exact next-semantic-v2 document
```

概念形:

```json
{
  "$id": "urn:code-structure-viz:schema:semantic-v2",
  "type": "object",
  "additionalProperties": false,
  "required": ["type", "schema", "domain", "document_kind", "status", "diagnostics"],
  "properties": {
    "...": "semantic-v1 と next-semantic-v2 のroot key supersetだけを宣言"
  },
  "oneOf": [
    {
      "allOf": [
        {"$ref": "urn:code-structure-viz:schema:semantic-v1"},
        {
          "required": ["domain"],
          "properties": {
            "domain": {"enum": ["python", "sqlalchemy"]}
          }
        }
      ]
    },
    {"$ref": "urn:code-structure-viz:schema:next-semantic-v2"}
  ]
}
```

重要事項:

- Python／SQLAlchemy document内の `schema` は既存どおり `code-structure-viz.semantic/v1`。
- Next documentだけが `code-structure-viz.semantic/v2`。
- `semantic-v2` はdispatcher schemaのversionであり、全domain documentを強制v2化しない。
- semantic-v1のNext branchをroute 1から明示的に除く。
- generic schemaのtop-level `additionalProperties:false`を維持する。
- root key supersetはdispatch用のkey許可だけであり、record definitionsを複製しない。

現行`semantic-v1.schema.json`はNext-v1へのexact refを持つため、そこへNext-v2 unionを足す方法は禁止する。attachments-bundle

### 9.3 local schema registry

現行schema testsはlocal `referencing.Registry` へ明示resourceを登録して検証している。

新registryでは次を行う。

1. `$id` を持つ全必要schemaをそのIDで登録。
2. `$id` を持たない既存 `semantic-v1.schema.json` を、retrieval URI
   `urn:code-structure-viz:schema:semantic-v1`
   へ明示登録。
3. `semantic-v2`、`next-semantic-v2`、`next-compatibility-v2` と、そのrecursive refsを登録。
4. network／remote retrievalへfallbackしない。
5. unresolved refはtest failureにする。

registry testは、単に各leaf schemaを直接validatorへ渡すだけでなく、`semantic-v2` からrecursive `$ref` を実際に解決する。

---

## 10. 変更対象

### 10.1 新規ファイル

| path | 内容 |
|---|---|
| `schemas/next-semantic-v2.schema.json` | Next public document v2 |
| `schemas/semantic-v2.schema.json` | generic dispatcher v2 |
| `docs/contracts/next-semantic-v2.md` | owner／projection／fingerprint／dispatcher contract |
| `tests/contracts/next_public_semantic_v2_reference.py` | decision-only producer |
| `tests/contracts/next_public_semantic_v2_validation.py` | independent owner validator／dispatcher validator |
| `tests/contracts/test_next_public_semantic_v2.py` | focused TDD matrix |
| `tests/fixtures/next_runtime_v2/public-semantic-v2-run-fingerprint-preimage.json` | ASCII independent preimage KAT |
| `tests/fixtures/next_runtime_v2/public-semantic-v2.json` | independently authored nominal literal |
| Issue direct-child artifact | Red→Greenと検証結果を保存するdurable evidence |

fixture名はlocal organizationに合わせて微調整してよいが、producerがfixtureを書き出す構成は禁止する。

### 10.2 変更する既存ファイル

| path | 変更 |
|---|---|
| `tests/contracts/next_runtime_v2_reference.py` | retained analysis context、request frameのcontext binding |
| `tests/contracts/next_runtime_v2_validation.py` | context／request owner joins |
| `tests/contracts/test_next_request_frame_v2.py` | context owner、wire不変、mutation tests |
| `tests/contracts/test_next_exchange_v2.py` | 新request builder APIへ移行 |
| `tests/contracts/test_next_semantic_candidate_v2.py` | 新request builder API、public test helper reuseは最小限 |
| `tests/contracts/test_json_schemas.py` | 新schema validity／registry／cross-version regressions |
| `plan.md` | A02-3 current progressを限定更新 |
| `report.md` | 実施結果、tests、未認定範囲を限定更新 |

`build_request_frame_v2` の全call siteは実装前に次で列挙し、上表にないものも漏れなくtyped contextへ移行する。

```bash
rg -n 'build_request_frame_v2\(' tests
```

### 10.3 変更禁止

```text
schemas/next-semantic-v1.schema.json
schemas/semantic-v1.schema.json
schemas/next-config-v1.schema.json
docs/contracts/next-semantic-v1.md
src/**
pyproject.toml
uv.lock
```

Requirement／Designは変更しない。実装中に正本変更が必要と判明した場合は、勝手に編集せず停止条件へ進む。

---

## 11. TDD vertical cycles

各cycleは、対象test一件または一つのparameterized behaviorだけを先に追加し、**同じtestのRedを確認してから**最小Greenを実装する。複数cycleのtestsを一括で先に書かない。

### Cycle 1 — retained analysis context

**Red**

```text
test_analysis_context_derives_one_closed_domain_config_from_seal_assets_and_intent
test_analysis_context_rejects_direct_constructor_duck_and_foreign_owner
test_request_frame_retains_the_exact_analysis_context_without_changing_wire_bytes
```

既存known requestについて、次を固定する。

- request ID `364ae1c7150c97541f990bffc4a864ebc405cdf5d0472f3c250434a8f1375197`
- canonical wire bytes `3961`
- full wire SHA-256 `2775c51cb98c3a0c024521007b9c3473c65720ae592597fb9f4c7a9e675ce44f`

これらは既存request literalの独立vectorであり、context追加によって変えてはならない。attachments-bundle

**Green**

- `RetainedNextAnalysisContextV2`
- factory／validator
- request frame binding
- 全call siteの機械的移行

Focused command:

```bash
uv run pytest -q \
  tests/contracts/test_next_request_frame_v2.py \
  -k 'analysis_context or retained_context or known'
```

### Cycle 2 — Next semantic v2 schema

**Red**

```text
test_next_semantic_v2_schema_accepts_nominal_closed_document
test_next_semantic_v2_schema_rejects_v1_schema_and_v1_compatibility
test_next_semantic_v2_schema_rejects_private_and_unknown_fields
```

**Green**

- `next-semantic-v2.schema.json`
- v1 record refsのみを再利用
- status complete／partial-safe branch

```bash
uv run pytest -q \
  tests/contracts/test_json_schemas.py \
  -k 'next_semantic_v2'
```

### Cycle 3 — nominal complete nonempty

**Red**

```text
test_public_semantic_v2_projects_complete_nonempty_from_one_nominal_decision
test_public_semantic_v2_validator_independently_recalculates_nominal_document
```

入力は既存 `core_inputs` のactual `SourceAcquisitionSeal` とretained assets／request／whole-exchange candidateを使う。runtime PID／counter／compiler-less assets／semantic recordsはsyntheticであり、actual TS／OS acceptanceとは記録しない。既存known corpusもこの制限を明示している。

**Green**

- decision-only producer
- independent validator
- source／request／run fingerprint／compatibility／model projection

```bash
uv run pytest -q \
  tests/contracts/test_next_public_semantic_v2.py::test_public_semantic_v2_projects_complete_nonempty_from_one_nominal_decision \
  tests/contracts/test_next_public_semantic_v2.py::test_public_semantic_v2_validator_independently_recalculates_nominal_document
```

### Cycle 4 — legitimate complete empty

**Red**

```text
test_public_semantic_v2_accepts_legitimate_complete_empty_after_core_admission
```

条件:

- applicable projectは存在
- source correspondence／proofは閉じている
- Module／Componentは0
- statusは`complete`
- entities／members／relations／factsは空
- empty successful documentをunavailable branchから合成していない

**Green**

producerの特別なempty shortcutを作らず、同じprojection pathで通す。

### Cycle 5 — proof-backed partial-safe

**Red**

```text
test_public_semantic_v2_projects_proof_backed_partial_safe_without_upgrading_status
```

既存Core known corpusのlocalized proof-backed caseを使い、admitted gateが `partial_safe` であることを先に証明する。

**Green**

- `status: incomplete`
- `incomplete_kind: partial_safe`
- safe subset、coverage、diagnosticsを同じmodelから投影
- `complete`へ昇格しない

### Cycle 6 — unavailable／rejected refusal

一挙に大きなparameterized testへせず、少なくとも次の4 Red→Greenを分ける。

```text
test_public_semantic_v2_refuses_target_unavailable_decision
test_public_semantic_v2_refuses_export_unavailable_decision
test_public_semantic_v2_refuses_entity_budget_unavailable_decision
test_public_semantic_v2_refuses_rejected_semantic_decision
```

期待結果はdocumentなし。空projects／empty entitiesの成功snapshot、compatibility、run fingerprintをmintしない。

### Cycle 7 — owner hardeningとmutation

次を小さいparameterized groupsへ分ける。

```text
test_public_semantic_v2_rejects_constructor_duck_and_foreign_owner_bypasses
test_public_semantic_v2_projection_is_fresh_after_caller_mutation
test_public_semantic_v2_rejects_a_forged_immutable_gate
test_public_semantic_v2_rejects_compatibility_downgrade_and_fingerprint_mutations
test_public_semantic_v2_rejects_collection_order_mutations
test_public_semantic_v2_rejects_private_field_mutations
test_public_semantic_v2_rejects_root_discriminator_mutations
test_public_semantic_v2_recalculates_every_run_fingerprint_field
```

run-fingerprint mutation testは各13 fieldについて、次の両方を拒否する。

1. fieldだけ変更し、run fingerprintを更新しない。
2. document内の改変値でrun fingerprintを再hashする。

2もownerと不一致なので拒否しなければならない。

追加で、Node candidate hashをpreimageへ挿入して計算したhash、host pathを挿入したhashも拒否する。

### Cycle 8 — generic dispatcher v2

**Red**

```text
test_semantic_v2_dispatcher_accepts_next_v2
test_semantic_v2_dispatcher_rejects_next_v1_migration_bypass
test_semantic_v1_dispatcher_rejects_next_v2
test_next_semantic_v1_schema_rejects_next_v2
test_next_semantic_v2_schema_rejects_next_v1
test_semantic_v2_dispatcher_accepts_unchanged_python_v1_documents
test_semantic_v2_dispatcher_accepts_unchanged_sqlalchemy_v1_documents
test_semantic_v2_registry_resolves_all_refs_offline
```

**Green**

- `semantic-v2.schema.json`
- explicit local registry retrieval URI
-既存Python／SQLAlchemy golden／renderer regressions

### Cycle 9 — docs／evidence／local gate

- `next-semantic-v2.md`
- Plan current A02-3 progress
- Report verification／remaining gates
- durable evidence artifact
- focused／adjacent／static／SpecDock／diff gates

このcycleで新しいcontract behaviorを追加しない。

---

## 12. Test matrix

| ケース | producer | owner validator | Next-v2 schema | dispatcher-v2 |
|---|---:|---:|---:|---:|
| complete nonempty | accept | accept | accept | accept |
| legitimate complete empty | accept | accept | accept | accept |
| proof-backed partial-safe | accept | accept | accept | accept |
| target unavailable | refuse | N/A | shapeを作らない | N/A |
| export unavailable | refuse | N/A | shapeを作らない | N/A |
| entity-budget unavailable | refuse | N/A | shapeを作らない | N/A |
| rejected Core owner | TypeError/refuse | refuse | N/A | N/A |
| direct context constructor | refuse | refuse | N/A | N/A |
| duck decision／context | refuse | refuse | N/A | N/A |
| foreign source seal | refuse | refuse | N/A | N/A |
| foreign asset owner | refuse | refuse | N/A | N/A |
| caller-mutated returned dict | 次回projection不変 | mutated value拒否 | 状況次第 | 状況次第 |
| forged decision gate bytes | refuse | refuse | shapeだけでは検出不可 | shapeだけでは検出不可 |
| compatibility-v1 downgrade | N/A | refuse | refuse | refuse |
| rehashed fake portable fingerprint | N/A | refuse | shape pass可能でもowner拒否 | shape only |
| run-fingerprint field mutation | N/A | refuse | shape pass可能 | shape pass可能 |
| wrong collection order | N/A | refuse | schema pass可能 | schema pass可能 |
| `content_base64`追加 | N/A | refuse | refuse | refuse |
| `proof`追加 | N/A | refuse | refuse | refuse |
| host path／PID／FD追加 | N/A | refuse | refuse | refuse |
| wrong schema/domain/status | N/A | refuse | refuse | refuse |
| complete + `incomplete_kind` | N/A | refuse | refuse | refuse |
| partial-safe without `incomplete_kind` | N/A | refuse | refuse | refuse |
| Next-v1 document | N/A | N/A | refuse | refuse |
| Python-v1 document | N/A | N/A | N/A | accept unchanged |
| SQLAlchemy-v1 document | N/A | N/A | N/A | accept unchanged |

schema validationとowner validationの役割差をtestsで明示する。schema-validだがowner-invalidなmutationを必ず含める。

---

## 13. Independent known vector

### 13.1 vector作成規則

nominal success fixtureはproducerで生成して保存しない。先にliteral recordとrun-fingerprint preimageを手で構成し、既存known corpusの固定IDs、source-sealed fixture、compatibility fixtureへ照合する。

run-fingerprint preimageはASCII値だけのvectorにし、`jq`／`shasum`で独立計算する。

```bash
PREIMAGE=tests/fixtures/next_runtime_v2/public-semantic-v2-run-fingerprint-preimage.json
SCRATCH=.workbench/luna-max-implement/issue8-nextjs-snapshots/public-semantic-v2

jq -cS . "$PREIMAGE" \
  | tr -d '\n' \
  | tee "$SCRATCH/run-fingerprint-preimage.bytes" \
  | shasum -a 256

wc -c < "$SCRATCH/run-fingerprint-preimage.bytes"
```

得られたdigestとbyte countをtest literalおよびevidence artifactへ固定する。実装の `digest()` やproducerをexpected生成に使わない。

### 13.2 vectorが証明しないもの

- TypeScript compilerが実行されたこと
- actual Node binary／OS process acceptance
- actual CLI output
- installed distributionの資材完全性
- arbitrary Next sourceへの一般化
- publication exact bytes
- A02／A03／Issue全体のpass

full public documentのcanonical byte hashを追加する場合も、同じ独立shell手順で計算し、「reference record KAT」であってArtifact publication sealではないと明記する。

---

## 14. 実行手順

### 14.1 preflight

```bash
set -euo pipefail

REPO=chemitaro/code-structure-viz
BRANCH=iss-00008-generate-nextjs-component-snapshots
START_SHA=ae15deb505d610f74e7c59b506b001b5224c4235
SCRATCH=.workbench/luna-max-implement/issue8-nextjs-snapshots/public-semantic-v2

test "$(git branch --show-current)" = "$BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA"

git fetch --no-tags origin \
  "refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"

test "$(git rev-parse "refs/remotes/origin/$BRANCH")" = "$START_SHA"
test -z "$(git status --porcelain=v1 --untracked-files=all)"

mkdir -p "$SCRATCH"
git check-ignore -q "$SCRATCH/"
```

どれかが失敗したら実装を開始しない。別branchへcheckoutしない。default branchへfallbackしない。

### 14.2 初期調査

```bash
rg -n 'build_request_frame_v2\(' tests
rg -n 'semantic-v1|next-semantic-v1|next-compatibility-v2' \
  schemas tests/contracts docs/contracts
rg -n 'domain_config_digest|run_fingerprint|upstream_depth|downstream_depth' \
  tests/contracts schemas
```

scratch memoは `$SCRATCH` 以下だけに置く。

### 14.3 編集規則

- repository fileの変更は `apply_patch` だけで行う。
- formatterのwrite modeで一括変更しない。format checkの指摘は `apply_patch` で直す。
- subagent、Oracle、別model jobを開始しない。
- Browser／Computer Useでtestやpushを監視しない。
- quiet duplicate jobを作らない。
- `git reset`、`git restore`、`git checkout`、`git rebase`、history rewriteを使わない。
- `--force`、`--force-with-lease`、`--no-verify`を使わない。
- `.workbench` 外へscratchを置かない。

---

## 15. 必須検証コマンド

### 15.1 dependency environment

```bash
uv sync --frozen --all-groups
```

### 15.2 focused slice

```bash
uv run pytest -q tests/contracts/test_next_public_semantic_v2.py
```

### 15.3 adjacent owner／schema regressions

```bash
uv run pytest -q \
  tests/contracts/test_next_request_frame_v2.py \
  tests/contracts/test_next_exchange_v2.py \
  tests/contracts/test_next_semantic_candidate_v2.py \
  tests/contracts/test_json_schemas.py
```

### 15.4 bounded contract／security gate

```bash
uv run pytest -q tests/contracts tests/security
```

このgateは広い隣接回帰であるが、A02-4の全terminal/publication matrixやA05 acceptanceの代用ではない。

### 15.5 static quality

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
```

CIもRuff、mypy、pytest、SpecDock validationを別jobsで要求している。

### 15.6 legacy／production boundary

```bash
git diff --exit-code "$START_SHA" -- \
  schemas/next-semantic-v1.schema.json \
  schemas/semantic-v1.schema.json \
  schemas/next-config-v1.schema.json \
  docs/contracts/next-semantic-v1.md

git diff --exit-code "$START_SHA" -- \
  src \
  pyproject.toml \
  uv.lock
```

一件でも差分があればsliceを完了扱いにしない。

### 15.7 SpecDock

repository-local skillは、現行CLI helpを直前に読み、canonical docs／artifactをcommand-firstで扱い、変更後にsync／validateすることを要求する。

```bash
python3 ./spec-dock/scripts/spec-dock --help
python3 ./spec-dock/scripts/spec-dock new --help
python3 ./spec-dock/scripts/spec-dock new artifact --help
```

直前のhelpが示す現行構文で、Issue `iss-00008` 直下へ一件の`disc` evidence artifactを作る。metadata pathを手書きで捏造しない。CLIが返したartifact pathを `EVIDENCE_ARTIFACT` として保持し、その本文だけを `apply_patch` で埋める。

その後:

```bash
python3 ./spec-dock/scripts/spec-dock sync
python3 ./spec-dock/scripts/spec-dock validate
```

### 15.8 whitespace／diff

```bash
git diff --check
git status --short
```

---

## 16. Plan／Report／evidenceへの記録

### 16.1 Plan

`Current normative authority` 内のA02-3進捗へ、次だけを追記する。

- public semantic-document-v2 producer／validator／schema closureが完了したこと
- generic dispatcher-v2がNext-v2と既存Python／SQLAlchemy-v1をroutingすること
- private analysis-context leafをmechanically essential dependencyとして追加したこと
- focused／adjacent test結果
- publication、source prefix、asset policy、run/domain/root/stdout、A02全gate、A03が未完了であること

過去Round節や過去test件数を書き換えない。

### 16.2 Report

Verificationへ次を記録する。

- starting SHA
- 変更path
- Red→Greenの対象
- test commandとexact result
- independent run-fingerprint vectorのdigest／byte count
- v1 forbidden pathsがbyte-identicalであること
- `src`／dependenciesが無変更であること
- 実TS／OS／CLI／publicationは実行していないこと
- A02、A03、A04、A05は未完了であること

### 16.3 evidence artifact

最低限の見出し:

```markdown
# A02-3 public semantic v2 reference slice evidence

## Scope and exact starting SHA
## Authority and excluded work
## Red observations
## Green changes
## Independent known vector derivation
## Focused and adjacent verification
## Static and SpecDock verification
## Changed-path inventory
## Residual gates
```

このartifactを `review_status=pass`、independent review、production readinessと呼ばない。

---

## 17. Checkpointとpush

### 17.1 scope確認

```bash
git status --short
git diff --name-only
git diff --stat
```

変更が本briefのin-scope pathだけであることを確認する。予期しないtracked changeが一件でもあればcommitしない。

### 17.2 explicit staging

globやrepository全体をstageせず、実際に変更したpathをすべて明記する。

例:

```bash
git add -- \
  schemas/next-semantic-v2.schema.json \
  schemas/semantic-v2.schema.json \
  docs/contracts/next-semantic-v2.md \
  tests/contracts/next_public_semantic_v2_reference.py \
  tests/contracts/next_public_semantic_v2_validation.py \
  tests/contracts/test_next_public_semantic_v2.py \
  tests/contracts/next_runtime_v2_reference.py \
  tests/contracts/next_runtime_v2_validation.py \
  tests/contracts/test_next_request_frame_v2.py \
  tests/contracts/test_next_exchange_v2.py \
  tests/contracts/test_next_semantic_candidate_v2.py \
  tests/contracts/test_json_schemas.py \
  tests/fixtures/next_runtime_v2/public-semantic-v2-run-fingerprint-preimage.json \
  tests/fixtures/next_runtime_v2/public-semantic-v2.json \
  spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/plan.md \
  spec-dock/initiatives/init-00001-code-structure-visualization/epics/epic-00002-safe-git-structure-comparison/issues/iss-00008-generate-nextjs-component-snapshots/report.md \
  "$EVIDENCE_ARTIFACT"
```

`rg`で発見して変更した追加call siteがあれば、同様にpathを明記してstageする。`git add -A`、`git add .`は使わない。

### 17.3 staged diff全読

```bash
git diff --cached --check
git diff --cached --name-status
git diff --cached --stat
git diff --cached
```

確認事項:

- historical sectionsの書換えなし
- v1 schema／docsなし
- `src`なし
- lock／dependencyなし
- generated expected vectorsなし
- secret／absolute local pathなし
- out-of-scope source-prefix／asset policyなし

さらに、unstaged tracked changesが残っていないことを確認する。

```bash
test -z "$(git diff --name-only)"
```

### 17.4 commit

```bash
commit-codex -a
```

一つの小さいcoherent checkpointとする。hookを回避しない。

### 17.5 post-commit local check

```bash
test -z "$(git status --porcelain=v1 --untracked-files=all)"
git show --stat --oneline --decorate HEAD
git diff --exit-code "$START_SHA" -- \
  schemas/next-semantic-v1.schema.json \
  schemas/semantic-v1.schema.json \
  schemas/next-config-v1.schema.json \
  docs/contracts/next-semantic-v1.md \
  src \
  pyproject.toml \
  uv.lock
```

### 17.6 ordinary push

push直前にremoteが開始SHAから予期せず進んでいないことを確認する。

```bash
REMOTE_BEFORE="$(
  git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}'
)"
test "$REMOTE_BEFORE" = "$START_SHA"
```

一致した場合だけordinary pushする。

```bash
git push origin "HEAD:refs/heads/$BRANCH"
```

push後:

```bash
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_AFTER="$(
  git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}'
)"

test "$REMOTE_AFTER" = "$LOCAL_HEAD"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
```

remote divergence、non-fast-forward、hook failure、test failureがあれば停止する。rebase、reset、force pushで自己解決しない。

---

## 18. 選択sliceの受入条件

次をすべて満たした場合だけ、このsliceを「実装完了」と記録できる。

- exact starting SHAから開始した。
- producerは `ValidatedSemanticDecisionV2` だけを入力にする。
- retained analysis contextがsource／assets／requestへtyped bindされている。
- public source／request／status／compatibility／collectionsが同じdecisionから導出される。
- run fingerprintの13-field preimageがowner由来で独立再計算される。
- candidate hash／host-local factsがrun fingerprintへ入らない。
- complete nonemptyが通る。
- legitimate complete emptyが通る。
- proof-backed partial-safeが通る。
- target／export／entity unavailableがdocumentを生成しない。
- rejected ownerがdocumentを生成しない。
- constructor／duck／foreign owner／caller mutation／forged gateを拒否する。
- compatibility downgrade／portable fingerprint mutationを拒否する。
- collection order／private field／discriminator mutationを拒否する。
- Next-v1／Next-v2 cross-version rejectionが閉じている。
- dispatcher-v2で既存Python／SQLAlchemy documentsが回帰green。
- schema registryがlocal exact refsを解決し、remote fallbackしない。
- old v1 filesがbyte-identical。
- `src`、`pyproject.toml`、`uv.lock`が無変更。
- focused、adjacent、contracts/security、Ruff、format、mypy、SpecDock、diff checksがgreen。
- Plan／Report／evidenceが限定更新されている。
- 一つのordinary commitとしてpush済みで、remote SHAとlocal HEADが一致する。
- worktreeがcleanである。

---

## 19. 停止条件

次のいずれかが発生したら、ready-to-implement briefからblocker／decision reportへ切り替える。

1. upstream／downstream depthを既存v1 semanticsへ照合できず、default推測が必要になる。
2. domain-config digestまたはrun fingerprintをcaller-supplied hashとして受理しなければ実装できない。
3. public rendererがdecision以外のfree status／model／compatibility／sourceを必要とする。
4. depthをparent contextへ保持するだけではsemantic meaningを証明できず、Core selection algorithmの変更が必要になる。
5. unavailable／rejected branchからempty successful snapshotを作る必要がある。
6. Next-v2を受け入れるために `semantic-v1` または `next-semantic-v1` のbytes変更が必要になる。
7. generic dispatcher-v2がNext-v1を受け入れないとPython／SQLAlchemy回帰を維持できない。
8. raw source、`content_base64`、proof、private envelope、host path、PID／FDをpublic documentへ出す必要がある。
9. `src`／dependency／lockfile変更が必要になる。
10. source-prefixまたは未採択asset policyがmechanically requiredになる。
11. Current Requirement／Design／Plan間に、このsliceだけでは解消できないmaterial contradictionが見つかる。
12. remote branchが開始SHAから先行している。
13. local worktreeに本slice外の変更がある。

停止時は新contractを推測せず、該当authority、観測した矛盾、必要な人間判断を分離して報告する。

---

## 20. 明示的に残る隣接gate

このcheckpoint後も次は未完了である。

| gate | 残作業 |
|---|---|
| A02-3 adjacent | reader-owned source prefix、未採択asset policy判断、remaining provenance/public refs |
| A02 public chain | run／publication／domain／root／stdoutのv2 exact-ref closure |
| A02-4 | terminal selector／failure／publication全chain、全local quality matrix |
| A03 | clean/pushed exact SHAに対する独立ChatGPT Code Review Strict |
| A04 | actual retained package assets、public spawn、TypeScript、CLI、JSON／PlantUML production |
| A05 | 両OS、minimum/update lanes、offline wheel/sdist、licenses、既存domain不変、Final Quality Gate |

A03は、基準 `f4159066f3954454ad2f0c2701fa54bf1bc7bc4a` から最終clean/pushed exact SHAを対象にした、別actorによる独立gateとして残す。このbriefの作成者、実装primary、evidence artifactは、その独立passを自己認定しない。
