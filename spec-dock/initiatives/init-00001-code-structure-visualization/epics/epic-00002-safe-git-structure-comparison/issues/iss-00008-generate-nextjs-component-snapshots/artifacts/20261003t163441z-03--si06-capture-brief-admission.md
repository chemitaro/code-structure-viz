# SI-06 改訂実装ブリーフの採用 — 2026-10-04

原回答1545行/45節を全文確認しました。exact c0a1dd2a35326f1656d87ea9a0b907f45a8b123fで採択済みのcapture pair限定訂正と独立semantic/publication軸を扱い、下位owner・ASSET・reader-prefix・productionの変更は要求しません。正規stage_failed chain、既存API、schema gapをローカル現物と照合しました。

原native issue8-si06-capture-brief / exec13118はterminal0。GPT-5.6 SolとExtra HighはUI pickerで確認済み、backendは未検証。生回答/logのhashと同conversationはlineage.jsonに固定し、設定変更だけを理由に再実行しません。

原§43のgpt-6.1-sol/maxは依頼時の設定です。現在は人間が明示したgpt-6-astra、直近Maxをcaller-visible設定として記録します。§43がmodel-specific capabilityを仮定しないため実装手順の失効はありません。スキルがactor/backendを設定/証明したとは扱いません。

実行順: schema-only null-pair Red→限定Green→片側null/public measurement非nullable regressions→catalog-owned diagnostic seam→独立validator→single final owner→実境界64KiB/16MiB exact/+1とowner/privacy/axes→必須gates→元af6f5d33f9487a33dabf2ddfe41df85b3d8267fbからfresh Code Review Strict。newpath七件と限定schema/testsだけ。既存git/SpecDock権限・instructionsは外部のgeneric commandsより優先します。

独立validatorはproducer/cacheをexpected builderにしません。large fixturesは実source/seal/Core/candidates bytesで到達し、padding/縮小limit/fake measurementを禁止します。外部consumerのimmutable v2要求などmaterialな新判断が判明したら人間へ戻します。

これはadvisory手順の採用で、コード/受入れ/SI-06/全A02/A03/production/Issueのpassではありません。durable記録はunit checkpointでrawを損失なく保存し、証跡とcanonical meaningを分離します。
