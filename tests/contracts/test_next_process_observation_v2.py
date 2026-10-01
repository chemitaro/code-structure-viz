"""Data-only post-launch record tests; not an OS or product execution claim."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from tests.contracts import next_runtime_v2_reference, next_runtime_v2_validation
from tests.contracts.next_runtime_v2_validation import (
    validate_process_launch_policy_v2,
    validate_process_observation_v2,
)

ROOT = Path(__file__).resolve().parents[2]


def policy_fixture() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(
            (ROOT / "tests/fixtures/next_runtime_v2/launch-policy.json").read_text(encoding="utf-8")
        ),
    )


def complete_evidence(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "spawn": {
            "primitive": "subprocess.Popen",
            "pid": 1234,
            "pgid": 1234,
            "parameters": {
                name: deepcopy(policy[name])
                for name in (
                    "argv",
                    "shell",
                    "cwd",
                    "passed_environment",
                    "stdio",
                    "fd_inheritance",
                    "process_group",
                )
            },
        },
        "capture": {
            "stdin_bytes": 512,
            "stdin_sent_bytes": 512,
            "stdout_bytes": 1024,
            "stdout_retained_bytes": 1024,
            "stderr_bytes": 0,
            "stderr_retained_bytes": 0,
            "stdout_eof": True,
            "stderr_eof": True,
        },
        "exit_code": 0,
        "response": {
            "sha256": "7" * 64,
            "control": {
                "protocol": "code-structure-viz.next-adapter/v2",
                "adapter_version": "0.1.0",
                "binding": {"state": "bound", "request_id": policy["request_id"]},
                "runtime": {
                    "engine": "node",
                    "version_raw": "22.10.0",
                    "version": "22.10.0",
                    "eligibility": "supported",
                    "observation_source": "process.versions.node",
                },
                "result_kind": "success",
            },
        },
        "candidate_check": "unchanged",
        "assets_check": "unchanged",
        "terminal_cause": "none",
        "cleanup": {
            "group_stop": "not_required",
            "signals": [],
            "direct_child_waited": True,
            "pipes_closed": True,
            "candidate_closed": True,
            "private_root_removed": True,
        },
    }


def test_complete_reference_observation_opens_only_the_transport_payload_gate() -> None:
    policy = policy_fixture()
    validate_process_launch_policy_v2(policy)
    observed = next_runtime_v2_reference.reference_process_observation_v2(
        policy, complete_evidence(policy)
    )
    assert observed["producer"] == "reference"
    assert observed["platform"] == "fixture"
    assert observed["transport_payload_admissible"] is True
    assert observed["response"]["control"]["runtime"]["version"] == "22.10.0"
    assert "model" not in observed
    assert "proof" not in observed
    assert (
        observed["policy_digest"]
        == "abead3e8d882e02139fdfd849988fb3518e4d8f8b2302022699796c53c026448"
    )
    assert observed == json.loads(
        (ROOT / "tests/fixtures/next_runtime_v2/launch-observation.json").read_text(
            encoding="utf-8"
        )
    )


def test_reference_evidence_cannot_override_owner_fields_to_claim_production() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["producer"] = "production"
    evidence["platform"] = "linux"
    with pytest.raises(ValueError, match="evidence fields"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_observation_validator_rejects_spawn_arguments_that_do_not_match_policy() -> None:
    policy = policy_fixture()
    observed = next_runtime_v2_reference.reference_process_observation_v2(
        policy, complete_evidence(policy)
    )
    observed["spawn"]["parameters"]["argv"][0] = "/opt/unmeasured/node"
    with pytest.raises(ValueError, match="spawn parameters"):
        validate_process_observation_v2(observed, policy)


def test_timeout_discards_raw_buffers_without_inventing_version_or_target_proof() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"] = None
    evidence["terminal_cause"] = "timeout"
    evidence["exit_code"] = -9
    evidence["capture"]["stdout_eof"] = False
    evidence["capture"]["stderr_eof"] = False
    evidence["capture"]["stdout_retained_bytes"] = 0
    evidence["capture"]["stderr_retained_bytes"] = 0
    evidence["cleanup"]["group_stop"] = "verified"
    evidence["cleanup"]["signals"] = ["TERM", "KILL"]
    observed = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observed["transport_payload_admissible"] is False
    assert observed["response"] is None
    assert "target_completeness" not in observed


@pytest.mark.parametrize(
    "mutation",
    [
        {"policy_digest": "0" * 64},
        {"request_id": "0" * 64},
        {"producer": "production", "platform": "linux"},
    ],
)
def test_observation_validator_rejects_owner_identity_not_joined_to_policy(
    mutation: dict[str, str],
) -> None:
    policy = policy_fixture()
    observed = next_runtime_v2_reference.reference_process_observation_v2(
        policy, complete_evidence(policy)
    )
    observed.update(mutation)
    with pytest.raises(ValueError, match="policy binding"):
        validate_process_observation_v2(observed, policy)


def test_observation_validator_rejects_an_unrelated_process_group() -> None:
    policy = policy_fixture()
    observed = next_runtime_v2_reference.reference_process_observation_v2(
        policy, complete_evidence(policy)
    )
    observed["spawn"]["pgid"] = 9999
    with pytest.raises(ValueError, match="process group"):
        validate_process_observation_v2(observed, policy)


def test_cleanup_failure_preserves_validated_control_but_closes_the_payload_gate() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = "cleanup_unverified"
    evidence["cleanup"]["private_root_removed"] = False
    evidence["capture"]["stdout_retained_bytes"] = 0
    observed = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observed["response"] == evidence["response"]
    assert observed["transport_payload_admissible"] is False
    mutated = deepcopy(observed)
    mutated["transport_payload_admissible"] = True
    with pytest.raises(ValueError, match="payload gate"):
        validate_process_observation_v2(mutated, policy)


def test_supported_node_with_controlled_semantic_failure_has_no_transport_payload() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"]["control"]["result_kind"] = "semantic_failure"
    evidence["exit_code"] = 68
    observed = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observed["response"]["control"]["runtime"]["eligibility"] == "supported"
    assert observed["transport_payload_admissible"] is False


def test_none_terminal_cause_cannot_hide_a_child_exit_code_mismatch() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["exit_code"] = 65
    with pytest.raises(ValueError, match="exit"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_none_terminal_cause_cannot_hide_unverified_cleanup() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["cleanup"]["pipes_closed"] = False
    with pytest.raises(ValueError, match="cleanup"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_none_terminal_cause_cannot_hide_incomplete_capture() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["capture"]["stdout_eof"] = False
    with pytest.raises(ValueError, match="capture"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_timeout_cannot_retain_raw_capture_bytes_even_when_payload_flag_is_false() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = "timeout"
    evidence["response"] = None
    evidence["exit_code"] = -9
    evidence["cleanup"]["group_stop"] = "verified"
    evidence["cleanup"]["signals"] = ["TERM", "KILL"]
    with pytest.raises(ValueError, match="raw buffers"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_observation_cannot_claim_control_or_capture_without_a_spawned_process() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["spawn"] = None
    with pytest.raises(ValueError, match="spawn"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_request_bound_response_cannot_bind_to_an_unrelated_request() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"]["control"]["binding"]["request_id"] = "0" * 64
    with pytest.raises(ValueError, match="request binding"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_control_cannot_claim_a_supported_version_different_from_its_raw_observation() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"]["control"]["runtime"]["version"] = "24.0.0"
    with pytest.raises(ValueError, match="runtime version"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_control_cannot_claim_node_20_is_eligible() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"]["control"]["runtime"]["version_raw"] = "20.19.5"
    evidence["response"]["control"]["runtime"]["version"] = "20.19.5"
    with pytest.raises(ValueError, match="eligibility"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_success_control_requires_a_bound_request_and_supported_runtime() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"]["control"]["binding"] = {"state": "unbound", "request_id": None}
    with pytest.raises(ValueError, match="success control"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_protocol_failure_control_cannot_echo_an_unvalidated_request_id() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"]["control"]["result_kind"] = "protocol_failure"
    evidence["exit_code"] = 65
    with pytest.raises(ValueError, match="protocol_failure control"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_unsupported_runtime_control_cannot_disguise_a_supported_runtime() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"]["control"]["result_kind"] = "unsupported_runtime"
    evidence["exit_code"] = 66
    with pytest.raises(ValueError, match="unsupported_runtime control"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


@pytest.mark.parametrize("check", ["candidate_check", "assets_check"])
def test_none_terminal_cause_cannot_skip_observable_drift_checks(check: str) -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence[check] = "unverified"
    with pytest.raises(ValueError, match="drift checks"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_normal_observation_requires_a_control_response_not_just_complete_capture() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"] = None
    with pytest.raises(ValueError, match="control response"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_partial_stdout_cannot_supply_a_control_or_version_prefix() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = "timeout"
    evidence["exit_code"] = -9
    evidence["capture"]["stdout_eof"] = False
    evidence["capture"]["stdout_retained_bytes"] = 0
    evidence["cleanup"]["group_stop"] = "verified"
    evidence["cleanup"]["signals"] = ["TERM", "KILL"]
    with pytest.raises(ValueError, match="complete stdout"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_response_adapter_version_is_bound_to_the_retained_policy_identity() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["response"]["control"]["adapter_version"] = "9.9.9"
    with pytest.raises(ValueError, match="adapter version"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


@pytest.mark.parametrize(
    ("kind", "exit_code", "binding_state", "raw", "version", "eligibility"),
    [
        ("protocol_failure", 65, "unbound", "22.10.0", "22.10.0", "supported"),
        ("unsupported_runtime", 66, "bound", "20.19.5", "20.19.5", "unsupported"),
        ("unsupported_runtime", 66, "bound", "22.0.0-rc.1", None, "invalid"),
        ("bootstrap_failure", 67, "unbound", None, None, None),
        ("bootstrap_failure", 67, "bound", "22.10.0", "22.10.0", "supported"),
        ("semantic_failure", 68, "bound", "22.10.0", "22.10.0", "supported"),
    ],
)
def test_closed_child_failures_preserve_only_their_actual_control_prefix(
    kind: str,
    exit_code: int,
    binding_state: str,
    raw: str | None,
    version: str | None,
    eligibility: str | None,
) -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    control = evidence["response"]["control"]
    control["result_kind"] = kind
    control["binding"] = {
        "state": binding_state,
        "request_id": policy["request_id"] if binding_state == "bound" else None,
    }
    if raw is None:
        control["runtime"] = None
    else:
        control["runtime"].update(
            {"version_raw": raw, "version": version, "eligibility": eligibility}
        )
    evidence["exit_code"] = exit_code
    observed = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observed["response"]["control"] == control
    assert observed["transport_payload_admissible"] is False


def test_signal_exit_mismatch_preserves_a_previously_validated_control_prefix() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = "exit_mismatch"
    evidence["exit_code"] = -15
    evidence["capture"]["stdout_retained_bytes"] = 0
    observed = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observed["response"] == evidence["response"]
    assert observed["transport_payload_admissible"] is False


def test_normal_exit_cannot_claim_group_signals_were_needed() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["cleanup"]["group_stop"] = "verified"
    evidence["cleanup"]["signals"] = ["TERM"]
    with pytest.raises(ValueError, match="normal exit"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_child_wait_observation_must_agree_with_an_actual_exit_status() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = "cleanup_unverified"
    evidence["exit_code"] = None
    evidence["capture"]["stdout_retained_bytes"] = 0
    with pytest.raises(ValueError, match="wait"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_capture_counters_cannot_claim_more_stdin_written_than_was_encoded() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = "write_failed"
    evidence["response"] = None
    evidence["capture"]["stdout_retained_bytes"] = 0
    evidence["capture"]["stdin_sent_bytes"] = 513
    with pytest.raises(ValueError, match="capture counters"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_capture_limit_cause_requires_the_actual_cap_plus_one_measurement(stream: str) -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = f"{stream}_limit"
    evidence["response"] = None
    evidence["capture"]["stdout_retained_bytes"] = 0
    with pytest.raises(ValueError, match="cap measurement"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_capture_exact_cap_is_admissible_but_cap_plus_one_discards_both_raw_buffers(
    stream: str,
) -> None:
    policy = policy_fixture()
    cap = policy["limits"][f"max_adapter_{stream}_capture_bytes"]
    evidence = complete_evidence(policy)
    evidence["capture"][f"{stream}_bytes"] = cap
    evidence["capture"][f"{stream}_retained_bytes"] = cap
    exact = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert exact["transport_payload_admissible"] is True

    evidence["terminal_cause"] = f"{stream}_limit"
    evidence["response"] = None
    evidence["capture"][f"{stream}_bytes"] = cap + 1
    evidence["capture"]["stdout_retained_bytes"] = 0
    evidence["capture"]["stderr_retained_bytes"] = 0
    exceeded = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert exceeded["transport_payload_admissible"] is False


@pytest.mark.parametrize("cause", ["stage_failed", "spawn_failed"])
def test_pre_spawn_failure_cannot_claim_an_actual_spawn(cause: str) -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = cause
    evidence["response"] = None
    evidence["capture"]["stdout_retained_bytes"] = 0
    with pytest.raises(ValueError, match="pre-spawn"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


@pytest.mark.parametrize("cause", ["stage_failed", "spawn_failed", "interrupted"])
def test_unspawned_failure_has_no_capture_control_exit_or_child_cleanup(cause: str) -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence.update(
        {
            "terminal_cause": cause,
            "spawn": None,
            "capture": None,
            "exit_code": None,
            "response": None,
            "candidate_check": "unobserved",
            "assets_check": "unobserved",
        }
    )
    evidence["cleanup"]["direct_child_waited"] = False
    observed = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observed["transport_payload_admissible"] is False
    assert observed["spawn"] is observed["capture"] is observed["response"] is None

    evidence["cleanup"]["direct_child_waited"] = True
    with pytest.raises(ValueError, match="unspawned"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


@pytest.mark.parametrize(("field", "claim"), [("group_stop", "verified"), ("signals", ["TERM"])])
def test_unspawned_observation_cannot_claim_a_process_group_cleanup(
    field: str, claim: str | list[str]
) -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence.update(
        {
            "terminal_cause": "spawn_failed",
            "spawn": None,
            "capture": None,
            "exit_code": None,
            "response": None,
        }
    )
    evidence["cleanup"]["direct_child_waited"] = False
    evidence["cleanup"][field] = claim
    with pytest.raises(ValueError, match="unspawned"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


def test_runtime_binding_is_derived_from_one_joined_successful_reference_observation() -> None:
    policy = policy_fixture()
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {
            next_runtime_v2_reference.ENTRYPOINT_MEMBER: (
                "adapter",
                b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
            ),
            "code_structure_viz/_next_runtime/typescript/typescript.cjs": (
                "typescript_lib",
                b"reference compiler\n",
            ),
        }
    )
    observed = next_runtime_v2_reference.reference_process_observation_v2(
        policy, complete_evidence(policy)
    )
    binding = next_runtime_v2_reference.runtime_binding_from_observation_v1(
        policy, assets, observed
    )
    known = json.loads(
        (ROOT / "tests/fixtures/next_runtime_v2/runtime-binding.json").read_text(encoding="utf-8")
    )
    assert binding == known


def test_semantic_failure_preserves_node_observation_but_creates_no_binding() -> None:
    policy = policy_fixture()
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {
            next_runtime_v2_reference.ENTRYPOINT_MEMBER: (
                "adapter",
                b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
            ),
            "code_structure_viz/_next_runtime/typescript/typescript.cjs": (
                "typescript_lib",
                b"reference compiler\n",
            ),
        }
    )
    evidence = complete_evidence(policy)
    evidence["response"]["control"]["result_kind"] = "semantic_failure"
    evidence["exit_code"] = 68
    observed = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observed["response"]["control"]["runtime"]["version"] == "22.10.0"
    with pytest.raises(ValueError, match="successful transport"):
        next_runtime_v2_reference.runtime_binding_from_observation_v1(policy, assets, observed)


def test_rehashed_binding_with_another_node_version_is_not_joined_to_observation() -> None:
    policy = policy_fixture()
    assets = next_runtime_v2_reference.retain_execution_assets_v1(
        {
            next_runtime_v2_reference.ENTRYPOINT_MEMBER: (
                "adapter",
                b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
            ),
            "code_structure_viz/_next_runtime/typescript/typescript.cjs": (
                "typescript_lib",
                b"reference compiler\n",
            ),
        }
    )
    observed = next_runtime_v2_reference.reference_process_observation_v2(
        policy, complete_evidence(policy)
    )
    changed = next_runtime_v2_reference.runtime_binding_identity_v1(
        policy, assets, node_version="22.11.0"
    )
    with pytest.raises(ValueError, match="node observation"):
        next_runtime_v2_validation.validate_runtime_binding_observation_v1(
            changed, policy, assets, observed
        )


@pytest.mark.parametrize("field", ["candidate", "assets", "adapter", "trusted_environment"])
def test_self_valid_binding_cannot_substitute_another_retained_or_measured_identity(
    field: str,
) -> None:
    policy = policy_fixture()
    members = {
        next_runtime_v2_reference.ENTRYPOINT_MEMBER: (
            "adapter",
            b"// CodeStructureViz-Adapter-Version: 0.1.0\n",
        ),
        "code_structure_viz/_next_runtime/typescript/typescript.cjs": (
            "typescript_lib",
            b"reference compiler\n",
        ),
    }
    assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    observed = next_runtime_v2_reference.reference_process_observation_v2(
        policy, complete_evidence(policy)
    )
    substituted_policy = deepcopy(policy)
    if field == "candidate":
        substituted_policy["node_candidate"]["sha256"] = "3" * 64
    elif field == "trusted_environment":
        substituted_policy["trusted_environment_digest"] = "6" * 64
    elif field == "assets":
        members["code_structure_viz/_next_runtime/typescript/typescript.cjs"] = (
            "typescript_lib",
            b"other compiler\n",
        )
    elif field == "adapter":
        members[next_runtime_v2_reference.ENTRYPOINT_MEMBER] = (
            "adapter",
            b"// CodeStructureViz-Adapter-Version: 0.2.0\n",
        )
    substituted_assets = next_runtime_v2_reference.retain_execution_assets_v1(members)
    substituted_policy["execution_asset_set_id"] = substituted_assets.descriptor()["asset_set_id"]
    substituted_policy["adapter"] = substituted_assets.adapter_identity()
    changed = next_runtime_v2_reference.runtime_binding_identity_v1(
        substituted_policy, substituted_assets, node_version="22.10.0"
    )
    with pytest.raises(ValueError, match="binding owner identity"):
        next_runtime_v2_validation.validate_runtime_binding_observation_v1(
            changed, policy, assets, observed
        )


def test_host_policy_digest_preserves_opaque_composed_and_decomposed_path_spellings() -> None:
    observations = []
    for spelling in ("caf\u00e9", "cafe\u0301"):
        policy = policy_fixture()
        root = f"/private/tmp/{spelling}"
        policy.update(
            {
                "private_root": root,
                "runtime_directory": f"{root}/runtime",
                "cwd": f"{root}/cwd",
                "argv": [
                    policy["node_candidate"]["absolute_path"],
                    "--max-old-space-size=512",
                    f"{root}/runtime/next-adapter.mjs",
                ],
            }
        )
        observations.append(
            next_runtime_v2_reference.reference_process_observation_v2(
                policy, complete_evidence(policy)
            )
        )
    assert observations[0]["policy_digest"] != observations[1]["policy_digest"]
    assert observations[0]["spawn"]["parameters"]["cwd"].endswith("caf\u00e9/cwd")
    assert observations[1]["spawn"]["parameters"]["cwd"].endswith("cafe\u0301/cwd")


def test_cleanup_unverified_cause_requires_an_actual_unverified_cleanup_result() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = "cleanup_unverified"
    evidence["capture"]["stdout_retained_bytes"] = 0
    with pytest.raises(ValueError, match="cleanup cause"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


@pytest.mark.parametrize("subject", ["candidate", "assets"])
def test_drift_cause_requires_an_actual_observable_drift_result(subject: str) -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = f"{subject}_drift"
    evidence["capture"]["stdout_retained_bytes"] = 0
    with pytest.raises(ValueError, match="drift cause"):
        next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)


@pytest.mark.parametrize("subject", ["candidate", "assets"])
def test_observed_drift_preserves_control_but_never_creates_an_admissible_payload(
    subject: str,
) -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence["terminal_cause"] = f"{subject}_drift"
    evidence[f"{subject}_check"] = "drift"
    evidence["capture"]["stdout_retained_bytes"] = 0
    observed = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observed["response"] == evidence["response"]
    assert observed["transport_payload_admissible"] is False


def test_a_later_cleanup_failure_does_not_replace_the_original_timeout_cause() -> None:
    policy = policy_fixture()
    evidence = complete_evidence(policy)
    evidence.update({"terminal_cause": "timeout", "response": None, "exit_code": -9})
    evidence["capture"].update(
        {"stdout_eof": False, "stderr_eof": False, "stdout_retained_bytes": 0}
    )
    evidence["cleanup"].update(
        {"group_stop": "unverified", "signals": ["TERM", "KILL"], "private_root_removed": False}
    )
    observed = next_runtime_v2_reference.reference_process_observation_v2(policy, evidence)
    assert observed["terminal_cause"] == "timeout"
    assert observed["cleanup"]["group_stop"] == "unverified"
    assert observed["transport_payload_admissible"] is False


@pytest.mark.parametrize(
    "field", ["model", "proof", "target_completeness", "actual_image_sha256", "verified_handle"]
)
def test_observation_rejects_semantic_payload_and_historical_strong_guarantee_fields(
    field: str,
) -> None:
    policy = policy_fixture()
    observed = next_runtime_v2_reference.reference_process_observation_v2(
        policy, complete_evidence(policy)
    )
    observed[field] = {}
    with pytest.raises(ValidationError):
        validate_process_observation_v2(observed, policy)
