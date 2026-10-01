# GitHub検証結果

検証は成功しました。

| 項目 | 検証値 |
|---|---|
| Repository | `chemitaro/code-structure-viz` |
| Target branch | `iss-00008-generate-nextjs-component-snapshots` |
| Expected full SHA | `710eb49a2a3143e31b8a91580700d16839d9070d` |
| Observed branch-tip full SHA | `710eb49a2a3143e31b8a91580700d16839d9070d` |
| SHA比較 | byte-for-byte一致 |

実行した操作は、GitHub connectorのbranch操作確認、repository取得、指定branch検索、指定branch endpointからのtip SHA取得です。default branchや別branchは内容参照に使用していません。

以下はこの固定SHAに対するA02技術設計助言です。採択済みADR自身も、A採択が実装完了・実測成功・独立レビューpassを意味しないと明示しています。:chatgpt-content-reference{index="1"}

# 結論

推奨する設計は次の三点です。

1. **semantic ontologyと要素identityはv1のまま維持し、runtimeに依存するdocument envelopeだけをv2へ移行する。**
2. **actual Node versionはrequestに入れず、同一Node processのbootstrap観測後にPython ownerがruntime bindingとcompatibilityを組み立てる。**
3. **資材保持・staging・spawn・capture・wait・cleanupを一つの深いexecution Moduleへ閉じ、Coreはsemantic validation・compatibility join・publicationを所有し続ける。**

旧`next-process-launch-v1`を新保証へ作り替えるのではなく、旧v1は履歴契約として凍結します。新方式ではpolicyとobservationを直接authorityとし、旧形式に似せた新しい派生`next-process-launch-v2`は原則として作らないのが最小です。

---

# 1. 最小の新version closure

## 1.1 必須の版移行

現在のrequest v1はclosed objectで、runtime要件を持たず、response v1はcompatibility descriptor、semantic compatibility ID、model、proofをすべて必須にしています。したがって、unsupported runtimeやbootstrap failureを「modelなしの正当な一応答」として表すにはprivate wireの破壊的移行が必要です。:chatgpt-content-reference{index="2"} :chatgpt-content-reference{index="3"}

| Surface | 判定 | 理由と新契約の要点 |
|---|---|---|
| `next-process-launch-policy-v1` | **v2必須** | v1は起動前にNode `version`を要求し、2要素argvとroot literal entrypointを固定している。v2は`runtime_requirement`、明示Node候補、候補content hash、runtime bundle identity、logical entrypoint、3要素argv templateを持ち、actual versionは持たない。 |
| `next-process-launch-observation-v1` | **v2必須** | v1 production branchはverified handle、spawn時identity equality、post-spawn equal、OS別verified-FD primitiveを必須とする。v2からこれらを除き、candidate measurement、same-process version observation、control result、exit/capture/cleanup/driftを記録する。 |
| `next-process-launch-v1` | **旧v1を凍結。v2は作らない** | 旧方式の派生compatibility viewであり、新方式のauthorityにしない。新consumersはpolicy v2＋observation v2を読む。 |
| `next-adapter-request-v1` | **v2必須** | `protocol`をv2へ移し、actual値を含まないclosedな`runtime_requirement`を追加する。 |
| `next-adapter-response-v1` | **v2必須** | 一つのclosed responseを、runtime control resultとnullable semantic payloadのunionにする。compatibilityは子processから除去する。 |
| `next-compatibility-v1` | **v2必須** | v1のNode hashは「実Node bytes/version」の意味を持つ。Aではcandidate hashとactual process versionを別観測として保持し、actual-image equalityを主張できないため、同じv1 preimageに投影できない。 |
| `next-provenance-v1` | **v2必須** | 現在のclosed observation mapではcandidate、policy、process start、same-process version、control response、semantic payloadの因果差を表せない。stage/code unionも追加が必要。 |
| `next-run-decision-v1` | **v2必須** | 現在のbound contextはcompatibility IDとprocess observation digestを必須とする。presemantic failureではこれらをnullにできるv2 contextが必要。 |
| `next-publication-decision-v1` | **v2必須** | `semantic_decision`がrun-decision-v1へのexact `$ref`。run-decision v2への移行だけでもpublication v2が必要。 |
| `next-domain-manifest-v1` | **v2必須** | compatibility-v1、旧toolchain形状、run/publication v1を直接参照している。runtime controlの安全なprojectionとsemantic compatibilityのnullable化が必要。 |
| `next-semantic-v1` | **document envelope v2必須** | compatibility-v1へのexact refを持つ。ただしproject/file/module/component/member/relation/fact等の要素defsはv1を再利用する。 |
| `run-manifest-v1` | **v2必須** | root manifestは旧process policy/observation、adapter response、run/publication decisionをexact refで束縛しているため、子surfaceだけv2にしても閉じない。 |
| `next-trusted-type-environment-v1` | **manifest表現v2を推奨** | semantic profileはv1維持。ただし現v1の`physical_path`は`tests/fixtures/next_trusted_profile/...`に固定され、インストール済みproduct resourceの実態を表せない。production manifestではlogical virtual pathとpackage memberを分離する。 |

旧process policyはNode versionと2要素argvを事前policyへ含め、旧observationはverified handleとactual identity equalityを要求しています。これらはAの保証内容と直接衝突します。:chatgpt-content-reference{index="4"} :chatgpt-content-reference{index="5"}

現在のcompatibility v1 preimageも、Nodeについて`status/version/sha256`を一体の実runtime contentとして扱います。candidate hashへ読み替えるsilent rewriteは避けるべきです。:chatgpt-content-reference{index="6"}

### 推奨する新schema paths

```text
schemas/next-runtime-binding-v1.schema.json

schemas/next-process-launch-policy-v2.schema.json
schemas/next-process-launch-observation-v2.schema.json
schemas/next-adapter-request-v2.schema.json
schemas/next-adapter-response-v2.schema.json
schemas/next-compatibility-v2.schema.json
schemas/next-provenance-v2.schema.json
schemas/next-run-decision-v2.schema.json
schemas/next-publication-decision-v2.schema.json
schemas/next-domain-manifest-v2.schema.json
schemas/next-semantic-v2.schema.json
schemas/run-manifest-v2.schema.json

schemas/next-trusted-type-environment-v2.schema.json
```

`next-runtime-binding-v1`は新概念の最初の版です。成功したsame-process control observationとowner保持identityを結合した、success-onlyの共有leafにします。

現在のgeneric semantic dispatcherがNext artifactを直接exact refで検証している場合だけ、次も必要です。

```text
schemas/semantic-v2.schema.json
```

この必要性はA02で実writer/validator call pathを確認して決めます。既存`semantic-v1.schema.json`へadditive `oneOf`を足して弱める方法は採りません。

## 1.2 v1のまま保持できるsurface

| Surface | 判定 | 条件 |
|---|---|---|
| `next-run-context-v1` | **保持** | formats、budget、stdout selectorだけでruntime observationを含まない。request/response/domain v2から引き続き参照する。 |
| `next-limits-v1` | **保持** | 16 MiB、64 KiB、60秒、V8 old-space 512等の意味を変えない。 |
| `next-config-v1` | **保持** | source/config/snapshot requestの意味はruntime launch移行と独立。 |
| `next-source-plan-v1` | **保持** | source acquisition原則を変更しない。 |
| path/root/applicability schemas | **保持** | runtime変更と無関係。 |
| `next-semantic-v1#/$defs/*` | **保持・再利用** | project/file/module/component/member/relation/fact/coverage/proof recordをコピーしない。 |
| identity/algorithm versions | **すべて1を保持** | recognition/export/props/relation/fact/boundary、Unicode 15.0、props IRを変更しない。 |
| `next-runtime-build-inventory-v1` | **保持可能** | bootstrapとcompiled analyzerを複数の`adapter` memberとして収録し、entrypointのlogical memberはpolicy v2で明示する。role enum追加が必要になった場合だけv2。 |
| `run-summary-v1` | **保持** | status、diagnostics、exitのgeneric shapeが変わらない限り維持する。 |
| `stdout-result-v1` | **保持** | public selector/result形状が変わらない限り維持する。 |
| すべての旧v1 fixture/schema/doc | **凍結** | 新production producerからは生成しないが、履歴回帰テストを残す。 |

`next-run-context-v1`はformats、budget、selectorだけのclosed objectであり、ここへNode requirementやactual versionを混ぜる必要はありません。:chatgpt-content-reference{index="7"}

## 1.3 semantic modelを不必要にv2化しない方法

`next-semantic-v2.schema.json`は**意味モデルv2ではなくdocument envelope v2**として設計します。

推奨するinstance識別は次です。

```json
{
  "schema": "code-structure-viz.semantic/v1",
  "document_contract": "code-structure-viz.next-semantic-document/v2",
  "domain": "next",
  "compatibility_descriptor": {
    "schema": "code-structure-viz.next-semantic-compatibility/v2"
  }
}
```

つまり、

- `schema = code-structure-viz.semantic/v1`
- identity versions = 1
- algorithm versions = 1
- `semantic_profile_id = next-trusted-profile-v1`
- Unicode profile = 15.0.0
- TypeScript identity = 5.9.2

を維持します。

新しく版を持つのは、

- document envelope
- runtime binding profile
- compatibility preimage
- process/control/provenance

だけです。

`next-semantic-v2`の各配列itemは、次のように既存defsへ直接refします。

```json
{
  "projects": {
    "items": {
      "$ref": "urn:code-structure-viz:schema:next-semantic-v1#/$defs/project"
    }
  }
}
```

response v2の`model`と`proof`も同様に、`next-adapter-response-v1#/$defs/model`等を再利用できます。これにより数百行のsemantic/proof schemaを複写せず、要素identityの意図しない版上げも防げます。

## 1.4 producer・validator・testの分離

A02ではproduction moduleをまだ変更せず、次の小さいreference laneを追加します。

```text
tests/contracts/next_runtime_v2_reference.py
tests/contracts/next_runtime_v2_validation.py
tests/contracts/test_next_runtime_v2_contracts.py
tests/fixtures/next_runtime_v2/
```

新validatorは、少なくとも次の関数単位に分けます。

```text
validate_process_launch_policy_v2
validate_process_launch_observation_v2
validate_adapter_request_v2
validate_adapter_response_v2
validate_runtime_binding_v1
validate_compatibility_descriptor_v2
validate_observation_provenance_v2
validate_run_decision_v2
validate_publication_decision_v2
validate_domain_manifest_v2
validate_run_manifest_v2
```

既存`tests/contracts/next_reference_validation.py`はv1 authorityとして保持し、丸ごとコピーしません。共有が必要な場合も、canonical JSON digest、schema registry、digest/path/semver primitiveなど、意味を持たない小さいpure helperだけを別moduleへ抽出します。

---

# 2. actual versionを後から結合する循環のないwire

## 2.1 request v2は「intentだけ」を持つ

推奨形は次です。

```json
{
  "schema": "code-structure-viz.next-adapter-request/v2",
  "protocol": "code-structure-viz.next-adapter/v2",
  "request_id": "<sha256>",
  "runtime_requirement": {
    "schema": "code-structure-viz.next-node-runtime-requirement/v1",
    "engine": "node",
    "release": "stable",
    "minimum_major": 22
  },
  "adapter_version": "<owner-derived version>",
  "trusted_type_environment": {
    "schema": "code-structure-viz.next-trusted-types/v1",
    "environment_version": "1",
    "semantic_profile_id": "next-trusted-profile-v1",
    "sha256": "<digest>"
  },
  "projects": [],
  "files": [],
  "targets": [],
  "limits": {},
  "run_context": {}
}
```

requestに入れないものは次です。

- actual Node version
- Node candidate absolute path
- Node candidate hash
- device/inode
- stage path
- process observation
- runtime binding fingerprint
- compatibility descriptor
- compatibility ID
- run fingerprint

`request_id`は、`request_id` fieldを除いたclosed objectのcanonical JSONに対するSHA-256です。wire送信時はその完全なrequestをcanonical JSON bytesにし、stdinを閉じます。

`adapter_version`やtrusted environment descriptorをfree-form caller inputにするのではなく、retained bundleから生成したowner objectをrequest builderへ渡すべきです。現在のbuilderは`adapter_version`とtrusted environmentを個別入力として受け取っていますが、v2ではbundle-derived identityへ絞るのが安全です。:chatgpt-content-reference{index="8"}

## 2.2 response v2はcontrol resultとsemantic payloadを分ける

概念形は次です。

```json
{
  "schema": "code-structure-viz.next-adapter-response/v2",
  "protocol": "code-structure-viz.next-adapter/v2",
  "adapter": {
    "version": "<compiled adapter version>"
  },
  "binding": {
    "state": "bound",
    "request_id": "<sha256>"
  },
  "runtime": {
    "engine": "node",
    "version_raw": "22.10.0",
    "version": "22.10.0",
    "eligibility": "supported",
    "observation_source": "process.versions.node"
  },
  "result": {
    "kind": "success",
    "failure": null,
    "semantic_payload": {
      "typescript_identity": "typescript-5.9.2",
      "trusted_type_environment_digest": "<sha256>",
      "identity_versions": {},
      "limits": {},
      "run_context": {},
      "model": {},
      "proof": {},
      "model_digest": "<sha256>"
    }
  }
}
```

`result.kind`はclosed unionにします。

```text
success
unsupported_runtime
protocol_failure
bootstrap_failure
semantic_failure
```

transport failureは有効なresponseではなく、Python execution Module側の結果です。

### 各branchの規則

| result | binding | runtime version | semantic payload |
|---|---|---|---|
| `protocol_failure` | `unbound`、`request_id=null` | bootstrapで安全に観測できたraw値 | null |
| `unsupported_runtime` | valid requestへbound | 必須。invalidまたはmajor<22 | null |
| `bootstrap_failure` | request parse前ならunbound、parse後ならbound | 観測済みなら保持 | null |
| `semantic_failure` | bound | supported | null |
| `success` | bound | supported | 必須 |

malformed JSON内にそれらしい`request_id`があってもechoしてはいけません。closed schema、canonical request digest、runtime requirementまで検証できた時点で初めて`bound`にします。

## 2.3 因果順序

循環のないproduction順序は次です。

1. source seal、limits、trusted declarations、TypeScript identityを検証する。
2. package resourceを一度だけ読み、immutableなretained runtime bundleを作る。
3. 利用者が指定したabsolute Node候補をopen/hashし、pre-launch candidate identityを得る。
4. retained bundleからadapter version/trusted environment descriptorを取り、request v2を作る。
5. request IDを確定し、candidate・request・bundle・launch条件をpolicy v2へ封印する。
6. retained bytesからrun-private runtime directoryへstagingする。別に空cwdを作る。
7. 次を一回だけspawnする。

```text
[absolute_node, "--max-old-space-size=512", run_private_entrypoint]
```

8. bootstrap自身が`process.versions.node`を観測する。
9. requestをclosed validationし、request IDを再計算する。
10. stable major >=22を満たさなければ、TypeScript import前に`unsupported_runtime`を一回だけ返す。
11. supportedならowned analyzerをimportし、semantic successまたはcontrolled failureを一回だけ返す。
12. Python execution Moduleがcapture、frame、request binding、exit status、cleanup、driftを検証する。
13. Python ownerがcandidate hash、same-process version、retained assets、TS/trusted identityからruntime bindingを作る。
14. success payloadをCoreが検証した後にcompatibility v2を構築する。
15. Coreがrun decision、domain manifest、publication、root manifestを生成する。

現在のbootstrap spikeも、Node version checkをanalyzer importより前に置いています。:chatgpt-content-reference{index="9"}

## 2.4 failureとobserved prefix

推奨するprovenance v2の順序は次です。

```text
applicability
config
source
limits
source_plan
trusted_environment
runtime_bundle
node_candidate
request
launch_policy
process_start
node_version
control_response
semantic_payload
compatibility
model
budget
```

| 結果 | 観測済みにできる最大prefix | 必ずunobserved/nullにするsuffix |
|---|---|---|
| Node候補open/hash失敗 | runtime bundleまで | node candidate以降 |
| request encode失敗 | node candidateまで | request以降 |
| stage失敗 | request、policyまで | process start以降 |
| spawn失敗 | request、policyまで | process start以降 |
| timeout/capture/read/wait failure | process startまで | node version以降。partial stdoutから値を補完しない |
| valid child protocol-failure frame | process start、node version、control response | request binding、semantic、compatibility、model |
| unsupported runtime | request、process、node version、control response | semantic、compatibility、model、budget |
| bootstrap failure | request、process、node version、control response | semantic、compatibility、model |
| semantic failure | request、process、node version、control response | semantic model、proof、compatibility、target completeness |
| success | 全部 | なし |

現在のprovenance v1は固定された12項目のobservation mapとstage別unionを持つため、この分離を同じidentityで追加することはできません。:chatgpt-content-reference{index="10"}

### target proofの規則

presemantic failureでは次を生成しません。

- `model`
- `proof`
- `target_resolutions`
- `target_completeness`
- entity count
- semantic coverage
- semantic compatibility ID
- 「全target failed」の合成結果

requestにtargetがあることはtarget-resolution observationではありません。

source planまで観測済みなら、source/config/limitsのsafe projectionは保持できます。ただしsemantic rowsは空、target proofも空です。

## 2.5 response framingとexit code

wireは次に固定します。

- stdoutはcanonical JSON object 1個＋LF 1個
- trailing bytesなし
- second JSONなし
- stderrはsemantic/control transportに使わない
- raw stdout/stderrはprivate
- cap超過、timeout、cleanup failure時はretained raw bytesを0にする

private child exit codeの推奨値は次です。

| response kind | child exit |
|---|---:|
| success | 0 |
| protocol failure | 65 |
| unsupported runtime | 66 |
| bootstrap failure | 67 |
| semantic failure | 68 |

65と66だけが現行spikeで実測済みであり、67と68はA02で固定する新提案です。spikeではmalformed requestの二重JSONをREDで再現し、単一protocol responseへ修正後にmatrixを再実行しています。:chatgpt-content-reference{index="11"}

次の組合せはすべてtransport/process failureです。

- `success` frame＋非0 exit
- failure frame＋別のexit code
- exit 0＋frameなし
- valid JSON＋extra bytes
- 二つのJSON
- request ID mismatch
- signal termination
- cleanup未確認
- candidateまたはstaged asset drift

public CLIのexitはchild codeをそのまま伝播させません。

- interrupt: 130
- usage: 2
- fatal invariant: 1
- runtime/control/semantic payload unavailable: 3
- complete success: 0
- partial-safe:既存publication原則に従い0または3

interruptは常に最優先です。その他は「最初に確定したterminal cause」を固定し、後続cleanup failureは原因を書き換えず`cleanup_verified=false`としてpayloadを抑止します。

---

# 3. asset identity・runtime provenance・Module境界

## 3.1 retained bytesから導出するidentity

`CJ(x)`をNFC・UTF-8・key sort・余分な空白なしのcanonical JSONとします。

### Execution asset set

```text
execution_asset_set_id =
  SHA256(CJ({
    schema: "code-structure-viz.next-execution-assets/v1",
    entrypoint_member: <logical package path>,
    members: [
      {
        package_path,
        role,
        size_bytes,
        sha256
      }
    ]
  }))
```

規則は次です。

- membersはUTF-8 package path順
- bytesを一度読んだretained objectからsize/hash/header/stagingを導出
- bootstrap、compiled adapter、TypeScript runtime/lib、trusted declarationsを含む
- host staging path、repository source pathは含めない
- license本文はdistribution/build inventoryに含めるが、semantic compatibilityのexecution asset setには含めない
- entrypointはhost pathでなくlogical member名

### Runtime binding fingerprint

```text
runtime_toolchain_fingerprint =
  SHA256(CJ({
    runtime_binding_profile_id: "next-public-spawn-runtime-v1",
    node_candidate: {
      sha256
    },
    node_observation: {
      version,
      source: "process.versions.node"
    },
    execution_asset_set_id,
    adapter: {
      protocol: "code-structure-viz.next-adapter/v2",
      version,
      sha256
    },
    typescript_identity: "typescript-5.9.2",
    trusted_type_environment_digest
  }))
```

ここで重要なのは、次のような主張をしないことです。

> candidate hashのbytesがactual process imageと同一だった。

記録する事実は二つだけです。

- Pythonが起動候補として測ったfile content hash
- 起動した同じNode processのbootstrapが返したversion

両者の関係は`next-public-spawn-runtime-v1`という明示的なtrust modelです。actual-image attestationではありません。

### Compatibility ID v2

```text
compatibility_id =
  SHA256(CJ({
    semantic_schema,
    identity_versions,
    algorithm_versions,
    semantic_profile_id,
    runtime_binding_profile_id,
    unicode_profile,
    typescript_identity,
    trusted_type_environment_digest,
    runtime_toolchain_fingerprint
  }))
```

次はpreimageから除きます。

- descriptor transport schema
- compatibility ID自身
- target/source/commit
- limits、timeout、format
- OS、architecture
- absolute Node path
- device/inode
- private runtime/cwd path
- PID/PGID/FD
- local cleanup observation

`semantic_schema`は`code-structure-viz.semantic/v1`、`semantic_profile_id`は`next-trusted-profile-v1`のままです。launch model変更だけを理由に`next-trusted-profile-v2`を作りません。

trusted declarationsの内容、certified symbols、TypeScript 5.9.2、意味algorithmが変わった場合だけsemantic profileのmigrationを別に判断します。

## 3.2 stable値とhost-local値

| Portable/stable identity | Host-local/ephemeral observation |
|---|---|
| request ID | absolute Node path |
| Node candidate content SHA-256 | device/inode/mtime/ctime |
| observed Node version | private root |
| logical package member path | staged entrypoint path |
| execution asset set ID | empty cwd path |
| adapter version/hash | concrete argv path |
| TS identity | PID/PGID |
| trusted environment digest | FD番号 |
| runtime binding fingerprint | libproc enumeration result |
| compatibility ID | timestamps、OS cleanup errno |

process policyにはlocal値を入れて構いませんが、portable fingerprintとsemantic compatibilityへ流してはいけません。

推奨する三種類のdigestは次です。

1. **policy digest**
   そのrunのabsolute path、request ID、candidate identity、concrete owner条件を含む。

2. **stable process fingerprint**
   concrete staging path等をlogical tokenへ置換したportable projection。

3. **local process attestation digest**
   path、device/inode、PID/PGID、concrete argv、cleanup observationを含むhost-local record。

## 3.3 trusted environment manifest v2

現在のtrusted environment schemaはfixture physical pathをclosed patternとして持っています。:chatgpt-content-reference{index="12"}

production用v2では、少なくとも次を分離します。

```json
{
  "schema": "code-structure-viz.next-trusted-type-environment-manifest/v2",
  "environment_descriptor": {
    "schema": "code-structure-viz.next-trusted-types/v1",
    "environment_version": "1",
    "semantic_profile_id": "next-trusted-profile-v1",
    "sha256": "..."
  },
  "files": [
    {
      "virtual_path": "/.code-structure-viz/trusted/v1/...",
      "package_path": "code_structure_viz/_next_runtime/...",
      "size_bytes": 0,
      "sha256": "...",
      "license_id": "..."
    }
  ]
}
```

semantic digestではlogical virtual pathとbytes identityを使います。インストール先absolute pathやtemporary staging pathは除外します。

## 3.4 小さいbundle Interfaceと深いexecution Module

### Retained bundle側

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True, slots=True)
class RuntimeMember:
    package_path: str
    role: str
    content: bytes
    sha256: str

@dataclass(frozen=True, slots=True)
class RetainedNextRuntimeBundle:
    execution_asset_set_id: str
    adapter_version: str
    adapter_sha256: str
    typescript_identity: str
    trusted_environment_digest: str
    entrypoint_member: str
    members: tuple[RuntimeMember, ...]

class NextRuntimeBundleSource(Protocol):
    def retain(self) -> RetainedNextRuntimeBundle:
        ...
```

`retain()`の中で、

- package rootを一度解決
- exact member setを一度だけ読む
- inventory、header、hashを照合
- immutable bytesとして保持

まで完了します。

現在の`resolve_next_adapter_identity()`はresourceを読んでversion/hashだけを返すため、後続stagingでは別lookupが必要になります。v2ではこのAPIをproduction pathから外し、retained bundleへ置き換えるべきです。:chatgpt-content-reference{index="13"}

### Callerへ見せるexecution API

```python
class NextExecutionModule:
    def execute(
        self,
        *,
        node_absolute_path: str,
        request: NextAdapterRequestV2,
    ) -> NextExecutionResult:
        ...
```

callerには次を公開しません。

```text
prepare()
stage()
spawn()
read_stdout()
terminate()
wait()
cleanup()
close()
```

これらはすべて`execute()`内部の一つのstate machineです。

### Execution Moduleの責務

- explicit absolute Node candidateのopen/hash/drift check
- bundle retain
- private runtime/cwd allocation
- retained bytesからのstaging
- policy sealing
- public spawn
- concurrent stdin/stdout/stderr処理
- caps、timeout、interrupt
- group termination
- direct child wait
- temporary cleanup
- response frame/control/request binding検証
- closed `NextExecutionResult`生成

### Coreの責務

- source/config/target semantics
- request semantic bodyの構築
- success semantic payloadのschema/reference/proof検証
- model/entity/budget gate
- runtime bindingとcompatibility v2のowner join
- domain/run/publication/root manifest
- public diagnostics、stdout、stderr、exit

Execution Moduleはsemantic modelを「正しい」と判定せず、Artifact公開もしません。Coreはprocess stagingやkillpgを知りません。

---

# 4. prototype lifecycleの優先点検

feasibility evidenceはmacOS/Linux上で、単一response、private staging、closed env/FD、cap exact/+1、timeout group cleanupを確認しています。一方、synthetic analyzerだけであり、実TypeScript、CLI、interrupt、drift、wheel/sdist、全OS/version/architectureの認定ではありません。:chatgpt-content-reference{index="14"} :chatgpt-content-reference{index="15"}

## 4.1 先に固定すべきP0 contract

| 優先 | Contract | 主要negative vector |
|---|---|---|
| P0-1 | 単一owner state machine | spawn前例外、spawn後例外、二重stop、二重wait、reap後signal |
| P0-2 | stdin/stdout/stderrを同時nonblocking処理 | 96 MiB requestを書いている間に子がstdout/stderrを満杯にする |
| P0-3 | capを保持前にcount | stdout 16 MiB exact/+1、stderr 64 KiB exact/+1、両方同一iterationで超過 |
| P0-4 | terminal causeを一度だけlatch | timeoutとcap、interruptとtimeout、read errorとchild exitの競合 |
| P0-5 | failure時はgroup signalをdirect child reapより先に実行 | leaderが先にexit、TERM-resistant child、遅延sentinel |
| P0-6 | cleanup確認前にpayloadを返さない | valid success frame後のwait失敗、temp removal失敗、pipe close失敗 |
| P0-7 | frameとexit codeを相互検証 | success＋exit68、unsupported＋exit0、JSON二つ、trailing byte |
| P0-8 | candidate/package driftをtyped failureにする | Node path交換、stage member変更、二度目のresource lookup |
| P0-9 | fast normal exitを別扱いする | stdin途中のBrokenPipe、stdout EOF、stderr EOF、direct childの早期exit |
| P0-10 | interruptを全stageで扱う | staging中、stdin write中、read中、TERM grace中、wait中のSIGINT |

### 推奨state

```text
NEW
  -> RETAINED
  -> STAGED
  -> SPAWNED_UNREAPED
  -> TERMINATING
  -> REAPED
  -> CLEANED
```

原則は次です。

- group signalを送れるのは`SPAWNED_UNREAPED`または`TERMINATING`だけ
- `REAPED`後に古いPGIDへsignalしない
- failure時はTERM、bounded grace、KILL、direct child wait
- normal successではdirect child wait後にgroup signalを行わない
- cleanup failureではsemantic payloadを破棄
- cleanup routineは内部的にidempotentだが、成功扱いを重複生成しない

## 4.2 selector/backpressure

production event loopでは、stdin writeを完了するまでstdout/stderr readを後回しにしてはいけません。

一回のselector cycleで、

1. interruptを確認
2. deadline超過を確認
3. ready eventsを固定順に処理
4. stdout/stderrを最大`remaining_cap + 1`だけ読む
5. countを加算
6. cap超過ならbufferを一切追加せずterminal causeをlatch
7. terminal cause後は新しいpayload byteを保持しない

とします。

cap超過時は、超過したstreamだけでなくstdout/stderr双方のretained bufferを破棄します。countsとfailure reasonだけを残します。

## 4.3 normal fast exit

正常なfast exitでは次を区別します。

- childがresponseを完全に書き、stdinを読み切る前にexitした
- stdinがBrokenPipeだが、有効なprotocol failure frameを返した
- stdout/stderr EOF後にexit 0
- childがexitしたがdescendantがpipeを保持してEOFにならない

productionのcanonical requestではBrokenPipeは通常のsuccessではありません。fault injection上、valid closed failure frameとexit pairが成立した場合だけcontrolled failureとして扱います。

## 4.4 cleanup failure

次はすべてpayload unavailableです。

- process group termination未確認
- direct child wait timeout
- unexpected wait error
- selector/read error
- runtime/cwd cleanup失敗
- staged asset drift
- candidate observable drift
- response validation後に発見したlifecycle不整合

「semantic successを既に受信した」ことはcleanup failureを上書きしません。

## 4.5 Darwin libproc候補

現spikeは、

- `proc_listpids(PROC_PGRP_ONLY)`
- `proc_pidinfo(PROC_PIDT_SHORTBSDINFO)`
- 256 PID固定配列
- 64 byte short BSD info
- numeric constants

を使い、EPERMを一律成功にはせず、live memberがいないと確認した場合だけ限定処理しています。:chatgpt-content-reference{index="16"}

### 最初のproduction sliceでの推奨

**libprocを必須にせず、保守的に失敗させる方式を先に採用します。**

- first-party adapterはdescendantをspawnしない契約
- normal successはdirect childをwaitし、終了済みgroupへsignalしない
- timeout/cap/interruptではleader未reapのまま`killpg`
- `ESRCH`はgroup不在として扱える
- Darwinの`EPERM`は成功にせず`cleanup_unverified`
- `cleanup_unverified`ではpayloadを公開しない
- `killpg(0)`、`waitid(P_PGID)`、kqueueだけで任意descendant不在を証明したことにしない

これはfalse negativeを許しますが、未確認cleanupを成功と偽りません。

### libprocを製品採用できる条件

次を全部満たした場合だけ、Darwin implementation内部へ追加します。

1. public SDK headersの型・定数だけを使う。
2. hard-coded `uint32_t[16]`や`64`ではなく、SDK structに対応した`ctypes.Structure`または検証済み小helperを使う。
3. PID列挙はsize queryとbounded retryを行う。
4. buffer満杯、truncation、query error、permission errorを「空」と扱わない。
5. `ESRCH`、zombie、live processを明示区別する。
6. leaderは列挙・signal完了まで未reap。
7. reap後のPGID再利用にsignalしない。
8. supported macOS versionと各配布architectureで実機matrixを通す。
9. query failure、切断、truncation、live memberをすべてcleanup failureにする。
10. escaped process group、任意same-UID攻撃、grandchildをPythonがwaitしたという保証に拡張しない。

libprocは「Darwinの終了済みgroupに対するEPERM false failureを減らす」ための局所実装であり、security boundaryではありません。

---

# 5. A02からFinal Quality Gateまでの実行単位

## A02-1: shared leafとprocess契約

### 変更

```text
schemas/next-runtime-binding-v1.schema.json
schemas/next-process-launch-policy-v2.schema.json
schemas/next-process-launch-observation-v2.schema.json
docs/contracts/next-process-launch-v2.md
```

### 受入れ

- policy v2にactual Node versionが存在しない。
- argvはlogical templateとして3要素。
- concrete private pathはlocal observationだけ。
- observation v2にverified-FD、actual-image equality、post-spawn equalが存在しない。
- candidate hashがactual executable hashという名称になっていない。
- inherited parent FDとNode内部FDを区別する。
- 旧v1 fixtureと既知値が一切変わらない。

## A02-2: private wireとcompatibility

### 変更

```text
schemas/next-adapter-request-v2.schema.json
schemas/next-adapter-response-v2.schema.json
schemas/next-compatibility-v2.schema.json
docs/contracts/next-adapter-protocol-v2.md
docs/contracts/next-compatibility-v2.md
```

### 受入れ

- requestはintentだけ。
- responseはcontrol＋nullable semantic payload。
- success以外にmodel/proofがない。
- compatibility descriptorはresponseから除去。
- parent-side既知値からcompatibility v2を計算。
- candidate hash、same-process versionの片方だけではruntime bindingを生成できない。
- host path変更でcompatibility IDが変わらない。
- candidate hashまたはactual version変更でcompatibility IDが変わる。
- semantic profile、identity、algorithm versionsはv1のまま。

## A02-3: provenanceとpublic closure

### 変更

```text
schemas/next-provenance-v2.schema.json
schemas/next-run-decision-v2.schema.json
schemas/next-publication-decision-v2.schema.json
schemas/next-domain-manifest-v2.schema.json
schemas/next-semantic-v2.schema.json
schemas/run-manifest-v2.schema.json
schemas/next-trusted-type-environment-v2.schema.json
docs/contracts/next-provenance-v2.md
```

必要なら次も追加します。

```text
schemas/semantic-v2.schema.json
```

### 受入れ

- unsupported/bootstrap/protocol/transport/semantic failureが別branch。
- observed prefixを後続failureが消さない。
- unobserved suffixをsuccess defaultで埋めない。
- presemantic failureにcompatibility、model、proof、target completenessがない。
- run decisionはruntime control responseとsemantic responseを区別。
- public response descriptorはdigest/length/canonical flagだけ。
- raw stdout/stderr、source本文、private proofを公開しない。
- publication v2はrun-decision-v2へexact ref。
- run-manifest-v2から全 `$ref` を再帰的に解決できる。
- v1 objectをv2へ偽装しても拒否される。

## A02-4: 小さいreference helperとnegative suite

### 変更

```text
tests/contracts/next_runtime_v2_reference.py
tests/contracts/next_runtime_v2_validation.py
tests/contracts/test_next_runtime_v2_contracts.py
tests/fixtures/next_runtime_v2/
tests/contracts/test_next_contracts.py
```

`tests/contracts/next_reference_validation.py`は原則変更しません。どうしても共有が必要なら、小さいpure helperだけを次へ抽出します。

```text
tests/contracts/next_contract_validation_support.py
```

### 最優先negative vectors

1. old v1 policyをv2 schema値だけ変えて送る。
2. v2へunknown fieldを追加する。
3. requestにactual Node versionを追加する。
4. childが自己生成したcompatibility descriptorを返す。
5. candidate hashをactual-image hashとして命名する。
6. request IDの交換。
7. unbound failureでrequest IDを保持する。
8. bound responseのrequest ID mismatch。
9. unsupportedでsemantic payloadを付ける。
10. bootstrap failureでmodel/proofを付ける。
11. semantic failureでtarget completenessを付ける。
12. successだがnode version observationがない。
13. valid JSONの後にLF以外の1 byteを付ける。
14. valid frameを二つ連結する。
15. response kindとexit codeを不一致にする。
16. private pathだけを変えてcompatibility IDが変わる。
17. candidate hashを変えてcompatibility IDが変わらない。
18. v1 known hashがA02変更で変わる。

### A02完了条件

- schema/reference closure green
- v1 regression green
- v2 known-value/mutation tests green
- production runner/CLIには未接続
- product availabilityは引き続きfalse
- 「契約が追加されたのでruntimeが利用可能になった」という記述がない

---

## A03: exact clean/pushed SHAでのfresh独立Strict gate

受入れ条件は次です。

1. clean worktree。
2. A02の全commitをremoteへpush。
3. target branchの新full SHAを取得。
4. reviewerがGitHub connectorでそのbranchとfull SHAを再検証。
5. untracked `.workbench`やローカル添付をauthorityにしない。
6. fresh cloneまたは同等のclean checkoutでcontract testを実行。
7. 旧Roundのpassを引き継がない。
8. P0/P1 findingが0。
9. schema closure、hash preimage、failure causality、v1不変性を個別判定。
10. gate記録にSHA、commands、platform、test summary、未確認事項を残す。

現在の固定SHAに対する本回答は、このA03 gateの代替ではありません。

---

## A04-1: retained runtime bundle

### 変更候補

```text
src/code_structure_viz/adapters/next/runtime_bundle.py
src/code_structure_viz/adapters/next/protocol_v2.py
src/code_structure_viz/_next_runtime/runtime-inventory.json
src/code_structure_viz/_next_runtime/bootstrap.mjs
src/code_structure_viz/_next_runtime/adapter.mjs
src/code_structure_viz/_next_runtime/typescript/
src/code_structure_viz/_next_runtime/trusted/
src/code_structure_viz/_next_runtime/licenses/
tests/unit/adapters/next/test_runtime_bundle.py
```

### 受入れ

- exact package member setを一回だけ読む。
- identity/header/stagingの全てが同じretained bytes由来。
- missing/extra/duplicate/traversal/hash/license mismatchを拒否。
- metadata resolver後の別resource再読なし。
- checkout外のinstalled packageからretain可能。
- まだspawnしない、availabilityも変更しない。

## A04-2: synthetic control縦切り

### 変更候補

```text
src/code_structure_viz/adapters/next/execution.py
src/code_structure_viz/adapters/next/runner.py
tests/unit/adapters/next/test_execution.py
tests/integration/adapters/next/test_execution_control.py
```

### 受入れ

- explicit absolute Nodeだけ。
- PATH探索なし。
- `[node, --max-old-space-size=512, private_entrypoint]`。
- minimal passed envだけ。
- parent FD 0/1/2以外を継承しない。
- separate runtime/cwd。
- one process、one request、one response。
- Node 20相当はanalyzer import前にunsupported。
- supported Nodeはsynthetic success。
- Python ownerがruntime bindingを生成。
- 実semantic modelやCLIへはまだ接続しない。

## A04-3: lifecycle TDD

### 受入れ

- stdout 16 MiB exact/+1。
- stderr 64 KiB exact/+1。
- large stdinと両outputのbackpressure。
- timeout。
- SIGINT。
- TERM-resistant first-party test descendant。
- leader fast exit。
- spawn/read/wait/stage/temp cleanup fault injection。
- candidate/staged asset drift。
- response/exit mismatch。
- failure時raw/partial bytes非保持。
- Darwin EPERMを成功にしない。
- direct childを確実にreap。
- reap後PGIDへsignalしない。

## A04-4: real TypeScript 5.9.2縦切り

### 受入れ

- retained package内TypeScriptだけをimport。
- target `node_modules`を参照しない。
- virtual CompilerHostにFS fallbackなし。
- target TS/JS/config/plugin/scriptを実行しない。
- request内frozen file set以外をopenしない。
- trusted declarationsのexact digestを照合。
- existing semantic element IDsとalgorithm known valuesが不変。
- real model/proofをCore validatorが検証。
- childはcompatibility IDを決めない。

## A04-5: Core decision/publication接続

### 受入れ

- runtime bindingとsemantic payloadをPython ownerがjoin。
- compatibility v2 known value一致。
- run decision v2、domain manifest v2、semantic envelope v2、publication v2、run manifest v2が同一contextを投影。
- presemantic failureでpayload unavailable。
- raw response/private proof非公開。
- selected stdout failureの既存publication原則を維持。
- availabilityはまだOS/package gateの後。

## Real OS・CLI・offline package gate

各宣言support OS/architectureで次を実施します。

- macOS実process。
- Linux実process。
- minimum Node 22 lane。
- それより新しいstable major lane。
- unsupported Node lane。
- explicit Node path。
- polluted parent `PATH/NODE_OPTIONS/NODE_PATH`。
- target repositoryに悪意あるscripts/plugins/node_modules。
- network disabled。
- checkout外の新規venv。
- wheel install。
- sdistからwheel再build。
- wheel/sdist exact runtime member set。
- license inventory。
- package resource bytesとbuild inventoryの一致。
- CLI complete、partial-safe、payload-unavailable、interrupt。
- temp resource残存なし。
- semantic artifact、domain manifest、root manifest、stdout/stderr、exitのcross-surface一致。

参照inventoryのgreenだけではproduct package gateをpassにしない、という既存方針を維持します。:chatgpt-content-reference{index="17"}

## Final Quality Gate

production availabilityを有効化できるのは、次の全ての後です。

```text
A02 schema/reference closure
→ clean/pushed exact-SHA independent Strict
→ A04 production TDD
→ real TypeScript/CompilerHost
→ real macOS/Linux/CLI
→ offline wheel+sdist
→ semantic/domain/publication cross-surface validation
→ final exact-SHA quality gate
```

---

# 却下すべき案

| 案 | 却下理由 |
|---|---|
| 旧schemaへadditive `oneOf` | v1 consumerの保証を弱め、旧fixtureが新production authorityに見える。 |
| verified-FD fieldsをnullや架空equalで埋める | 旧identityの意味を偽装する。 |
| candidate hashをactual process image hashと呼ぶ | Aのtrust modelを超える主張になる。 |
| requestへactual Node versionを入れる | 起動前には観測できず、別probeまたは捏造が必要になる。 |
| `node --version`別process | one process/one responseとsame-process observationを破る。 |
| child responseをcompatibility authorityにする | 子が自己申告したdescriptorをowner observationとして採用する循環になる。 |
| process policyとobservationを再び一objectへ潰す | prelaunch intentとpostlaunch factを区別できなくなる。 |
| full `process.env`とpassed envを一致要求する | Darwinのruntime内部追加stateと親のspawn envを混同する。 |
| `prepare/stage/launch/close`をpublic API化 | lifecycle順序違反、cleanup漏れ、caller差替えを招く。 |
| 将来用backend registry | 実backendが一つの段階で架空の拡張点になる。 |
| Darwin EPERMの握りつぶし | live descendantまたはquery不能を終了済みと誤認する。 |
| libproc導入だけでhard isolationを主張 | group列挙はsame-UID tamper、escaped group、runtime exploitを解決しない。 |
| Linux専用/container必須/private CPython API | 採択済みAのOS/runtime判断を別scopeへ変更する。 |
| A02契約greenをruntime可用性とする | process、TS、CLI、package、OS gateが未実装のまま。 |

---

# 確認範囲・仮定・未確認事項

## 確認済み

- 指定repository、branch、full SHAの一致。
- accepted ADR、feasibility evidence、spike/bootstrap。
- `runner.py`、`protocol.py`。
- 関連process/request/response/compatibility/provenance/domain/run/publication/semantic/runtime inventory schemas。
- root `run-manifest-v1`のruntime-bound exact refs。
- requirement/design/plan先頭のcurrent authorityとA02→Strict→A04順序。
- 既存test moduleがprocess、compatibility、provenance、run/publication validatorを結合していること。

## 未確認または未実行

- 大規模な`tests/contracts/next_reference_validation.py`全体の通読。
- `tests/contracts/test_next_contracts.py`全test bodyの通読。
- 1907 pass/1 skipの再実行。
- production adapter/TypeScript bundleの存在。
- CLI接続。
- wheel/sdist build。
- actual macOS/Linux production execution。
- interrupt/driftの製品実装。
- Darwin libprocの全support OS/architecture保証。
- 新しい67/68 private exit codeとpublic catalog codeの最終採番。
- generic `semantic-v2` dispatcherが必要となる実writer call path。
- independent Strict reviewまたは`review_status=pass`。

したがって、本回答は**A02の設計closure案**であり、実装完了、production availability、security certification、独立コードレビューpassの認定ではありません。
