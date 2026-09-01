# Next adapter process launch descriptor v1

`schemas/next-process-launch-v1.schema.json` は、Next adapter を起動する際の
trust boundary を表す閉じた descriptor である。これは production adapter の
実装ではなく、実装前に検証すべき契約である。descriptor は
`NextPublicationContext` と run-fingerprint preimage に含め、実際に観測・検証した
Node 実体を後段の writer が再構成しない。

## 固定する launch surface

`node_status=available` の場合、`node_realpath` は symlink を解決した絶対実体パス、
`node_sha256` はその実体の検証済み digest とする。`unavailable` と
`not_applicable` ではこの二つを `null` とする。`symlink_policy` は
`resolve_and_verify_realpath` のみを許可し、単に PATH の名前解決結果を信用しない。

以下の値は v1 の closed contract である。

- `argv` は `node` と固定された checked-in adapter entrypoint の二要素で、
  `shell=false` とする。
- `cwd` は絶対パスで、target repository の作業ディレクトリを公開・継承しない。
- 環境変数は `LANG=C.UTF-8`、`LC_ALL=C.UTF-8`、`TZ=UTC` の allowlist だけを使う。
  `NODE_OPTIONS`、`NODE_PATH`、PATH shadow、npm/npx の設定などは denied set として
  明示し、未列挙の host environment を暗黙に継承しない。
- stdin/stdout/stderr は全て pipe、file descriptor は close-on-exec で 0,1,2 だけを
  許可する。追加 FD を adapter へ渡さない。
- process group を作り、timeout または capture overrun では group 全体を終了し、
  終了後に wait する。子 process だけの kill や silent truncation は契約外である。

Descriptor の field、配列順、固定 map は JSON Schema と canonical JSON bytes で
検証する。PATH shadow、symlink の実体置換、hostile environment、locale/TZ の変更、
extra FD、process-group の scope 変更はいずれも descriptor mutation として拒否し、
検証済みの semantic/publication decision を作らない。

`process_launch_descriptor` は `NextPublicationContext` の必須フィールドであり、
default factory、host の PATH、または `node_status` からの後段 fallback は持たない。
available/unavailable/not-applicable の各 decision variant は、実際にその境界で
検証した descriptor を明示的に seal し、descriptor の digest を run-fingerprint
preimage に含める。descriptor を省略した構築、toolchain の node status と異なる
descriptor、preimage だけを差し替えた構築は受理しない。

## capture と証拠の境界

この descriptor は child stdout/stderr の incremental capture 契約と組み合わせる。
capture は chunk を retain する前に数え、上限超過時は read-stop、buffer dispose、
process-group termination を記録する。private response の raw-byte cap、public
selected-artifact copy cap、公開 stderr cap はそれぞれ別の measurement point であり、
descriptor へ混同して記録しない。

ローカルの reference test は `Iterable[bytes]` を使う faithful runner harness であり、
read-stop、dispose、termination flag、child text 非漏洩を検証する。ただしこれは OS
process-level の証明ではない。production 実装の OS process behavior は後続 acceptance
で別途検証する必要がある。

Round 16 content review は対象 SHA
`732477c72c7e05d3f15818ba8a3f75a4c97dc5a9`、CI `33494926439`（7/7 green）に対し、
`P0=0 / P1=16 / P2=3 / fail`、`implementation_ready=no` だった。fresh current-SHA
Strict は pending、readiness は未確認、production implementation は未着手である。

## Round 17 observation-to-spawn binding

The descriptor must be assembled from a launch observation made at the trust
boundary. The observation records the verified Node realpath, its digest and
version, and the exact executable passed to spawn; it also records the fixed
argv/cwd, allowlisted environment and denied variables, stdio/FD policy,
process-group scope, and the TOCTOU check. The actual spawn identity must
equal the observed identity. PATH lookup, a default executable name, a
caller-provided digest, symlink replacement, hostile locale/TZ or extra FD
cannot be used to complete the descriptor.

Request-independent decisions still carry an explicit descriptor field, with
`null`/`unobserved` values where the stage prevented observation. They do not
receive a synthetic launch descriptor from a fixture or host defaults. The
descriptor is bound to the toolchain and fingerprint before any publication
projection. Capture tests use a faithful iterable harness and explicitly do
not claim OS process-level coverage; production implementation is absent and
fresh current-SHA Strict is pending.

## Round 18 observation-to-spawn identity contract

An available descriptor is valid only when it is derived from one launch
observation and the observation is bound to the actual OS spawn. The contract
is:

1. On a supported OS, open the resolved executable without following a later
   replacement, record its absolute real path, file identity, version, and
   SHA-256, then close only after the observation is sealed.
2. Spawn the fixed `argv` with the recorded executable identity, fixed cwd and
   environment, pipe/FD policy, and process-group policy. The observed
   identity and the executable/handle used by spawn must compare equal.
3. Re-check the identity at the defined TOCTOU point. Replacement, PATH
   shadowing, symlink substitution, hostile inherited variables, locale/TZ
   changes, or extra descriptors fail closed before a publication decision.
4. If the host cannot provide the required identity/handle guarantee, the
   descriptor is unavailable and the run cannot claim an available Node
   observation; it is not completed using a fake default.

The schema/reference tests validate the descriptor shape and mutation rules.
They do not touch a host executable and do not claim this contract is an OS
process-level acceptance test; production implementation must add that
acceptance later. Request-independent provenance uses explicit
`null`/`unobserved` values for facts not observed before the failure. Fresh
current-SHA Strict remains pending, readiness is unconfirmed, and production
implementation is absent.
