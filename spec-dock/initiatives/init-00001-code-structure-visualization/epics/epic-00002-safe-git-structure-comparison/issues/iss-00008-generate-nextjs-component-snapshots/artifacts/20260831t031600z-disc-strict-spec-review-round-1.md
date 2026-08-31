---
種別: disc
ID: "20260831t031600z-disc"
タイトル: "Issue #8 ChatGPT Strict Specification Review Round 1"
状態: "draft"
作成者: "iwasawayuuta"
最終更新: "2026-08-31"
親: ["iss-00008"]
template: "disc"
authority: "evidence"
derived_from: []
reflected_to: []
---

# 20260831t031600z-disc Issue #8 ChatGPT Strict Specification Review Round 1

ChatGPT Use Strictによる独立仕様レビュー第1回の検証点、finding、採否、修復方針を保存する。
外部回答はadvisory evidenceであり、canonical authorityはRequirement / Design / Planとuser decisionにある。

## Inputs

- wrapper: `/Users/iwasawayuuta/.agents/skills/chatgpt-use-strict/scripts/oracle-chatgpt`
- session: `required-strict-github-connector-verificati-507`
- model/thinking: GPT-5.6 Sol / Pro
- reviewed repository: `chemitaro/code-structure-viz`
- reviewed branch: `iss-00008-generate-nextjs-component-snapshots`
- verified exact tip: `05db6a5574384a9011dd4342c7ff0c49230abb2e`
- GitHub connector verification: branch tipとexpected SHAが完全一致。
- attached evidence: canonical R/D/P、zero-base research、decision-candidate、current source/config/domain/outcome/artifact paths、security/schema tests。16 files、約96.7k tokens。
- scope: specification quality only。production implementation/test completionは対象外。
- review result: `review_status: fail`
- finding count: P0 1 / P1 9 / P2 2。

## Synthesis

### Accepted review facts

- declaration identity、explicit project roots、Python-frozen bytes、two-plane relations、positive-evidence boundary、fail-closed publicationという中心方針は妥当。
- Next production adapter、Node workspace、protocol/schema、fixtures/goldenは未実装で、現段階はimplementation-readyではない。
- P0/P1は実装者へ仕様判断を委ねるため、production implementation前にcanonical文書で閉じる必要がある。

### P0-1 Trusted type environment missing

target `node_modules`とpackage-based type resolutionを禁止しながら、`React.FC`、React class、`memo`、
`forwardRef`、`lazy`、`next/dynamic`、React-compatible signatureをTypeCheckerで認識するdeclaration sourceがない。

adopted remediation:

- adapter compatibility unitにversioned/closed/license-reviewed `TrustedTypeEnvironment/v1`をbundleする。
- TypeScript standard libs、minimal JSX namespace、v1 React component/class/wrapper declarations、minimal
  `next/dynamic` declarationを含める。
- exact version、digest、licenseをmanifest provenanceに記録する。
- environment外external typeはopaque/coverage/outcomeへ閉じる。
- target type roots/node_modules/networkを参照しないfixtureで認識を証明する。

### P1 findings and adopted remediation

1. **Component/export resolution**
   - syntax pattern別のcanonical declaration、key、entity/binding/wrapper relation、collision/failureを
     `ComponentDeclarationResolution/v1`と`ExportBindingResolution/v1`で固定する。
2. **Project/applicability/target**
   - `ProjectRootValidationMatrix`、`PackageApplicabilityMatrix`、`TargetResolutionMatrix`を追加する。
   - normalize/duplicate/nested/overlap/symlink/missing/malformed/mixed-root aggregationを閉じる。
3. **Source plan/protocol/CompilerHost**
   - stale SourceView例をcurrent型へ合わせ、`SourceAcquisitionPlan/v1`、file roles、discovery closure、
     compiler option allowlist、request/response schema、process exit matrixを固定する。
   - adapter `model_digest`とPython render後`Artifact digest`を分離する。
   - old-spaceを総メモリと呼ばず`v8_old_space_mib`とする。
4. **Props IR/limits**
   - variant fields/enums/order/ref/countをJSON Schema相当で固定する。
   - local complexityはopaque + localized partial、entity/transport/process limitはpayload unavailableと分離する。
   - candidate limitsをimplementation前calibration gateでnormative defaultsへ固定する。
5. **Relation/client algorithms**
   - `SelectionAndTraversal/v1`、`JsxOutputFlow/v1`、`RouterContextClassification/v1`、
     `BoundaryRolePropagation/v1`を規範疑似コード/表で固定する。
6. **Failure algebra/single-domain**
   -全failureをstage/scope/diagnostic/recoverability/status/payload/manifest/stdout/exitの一表に統合する。
   - current single-domain scopeからall-domain/sibling文言を削除しIssue #10へ委譲する。
7. **Closed registries/packaging**
   - CLI、diagnostic、schemas、contracts、semantic branches、PlantUML grammar、writer、manifest、wheel/sdist、
     resource lookup、distribution/license、CI/securityを実在path matrixへ追加する。
8. **Domain config projection/regression**
   - `domain_config_projection(domain)`と`domain_config_digest(domain)`を定義する。
   - Python/SQLAlchemy projection/digest/manifest/fingerprint bytesを変えず、Next fieldsはNext runだけに含める。
9. **Issue #9 handoff**
   - declaration identity、ExportBinding change、primitive boundary facts/edges、derived-role non-primary、
     snapshot failure semanticsをIssue #9 canonical R/D/Pへ反映する。

### P2 findings

- current CLI parserはNext stdout selector syntaxを部分的に受理済み。Planは新規grammar実装ではなくclosed registriesを一貫して有効化すると表現する。
- `.meta.json`/reportの`Nextjs`とR/D/Pの`Next.js`、Design/PlanのNode test command、issue gateの
  SpecDock/package/license checksを整合させる。managed metadataはraw editしない。

## Options and trade-offs

### React/Next type environment

| option | advantage | constraint | decision |
| --- | --- | --- | --- |
| target node_modules/typeRootsを読む | targetに近い型 | trust boundary、reproducibility、optionalityを破る | reject |
| React型依存acceptanceを大幅縮小 | bundleが小さい | `React.FC`/class/wrapperの価値を失う | reject |
| closed TrustedTypeEnvironmentをbundle | offline、deterministic、target非依存 | declaration/version/license maintenanceが必要 | adopt |

### Local type complexity outcome

| option | advantage | constraint | decision |
| --- | --- | --- | --- |
| payload unavailable | 単純 | 一つの複雑propで全snapshotを失う | reject as default |
| silent truncation | payloadを保つ | false completeness | reject |
| subtree opaque + localized partial coverage | 安全subsetと欠落を表現 | IR/coverage contractが必要 | adopt |

### Multiple-domain language

Issue #8はsingle-domain CLI/schemaをauthorityとし、all-domain healthy sibling preservationはIssue #10へ委譲する。
将来のmulti-domain設計を先取りしてcurrent outcomeを曖昧にしない。

## Reflection

- P0/P1 remediationをIssue #8 canonical Requirement/Design/Planへ反映する。
- identity/boundary/failure handoffをIssue #9 canonical R/D/Pへ反映する。
- review response自体をcanonical authorityにしない。
- 修復後にSpecDock/PlantUML/format validation、commit/push、clean/upstream equalityを確認する。
- 新しいexact GitHub SHAでfresh ChatGPT Use Strict reviewを行い、P0/P1=0と`review_status: pass`まで修復する。
- Strict passはIssue #8 production implementation completionではなく、implementation-readiness gateである。
