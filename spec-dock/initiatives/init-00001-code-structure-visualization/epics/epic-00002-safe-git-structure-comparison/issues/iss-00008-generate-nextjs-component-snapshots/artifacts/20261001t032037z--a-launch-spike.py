"""Bounded, non-production public-spawn probe on trusted installed Node."""

from __future__ import annotations

import argparse
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import selectors
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ENVIRONMENT = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"}
HERE = Path(__file__).resolve().parent
ASSETS = {name: (HERE / name).read_bytes() for name in ("a-bootstrap.mjs", "a-analyzer.mjs")}


def darwin_group_has_no_live_members(pgid: int) -> bool:
    """Bounded public libproc query; an error is not proof of group absence."""

    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    list_pids = library.proc_listpids
    list_pids.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_int]
    list_pids.restype = ctypes.c_int
    pid_info = library.proc_pidinfo
    pid_info.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    pid_info.restype = ctypes.c_int
    # Public SDK: PROC_PGRP_ONLY=2, PROC_PIDT_SHORTBSDINFO=13, short BSD size=64.
    members = (ctypes.c_int * 256)()
    ctypes.set_errno(0)
    size = list_pids(2, pgid, members, ctypes.sizeof(members))
    if size < 0 or ctypes.get_errno() or size >= ctypes.sizeof(members) or size % 4:
        return False
    for pid in list(members)[:size // 4]:
        info = (ctypes.c_uint32 * 16)()
        ctypes.set_errno(0)
        read = pid_info(pid, 13, 0, info, ctypes.sizeof(info))
        if read == 0 and ctypes.get_errno() == errno.ESRCH:
            continue  # exited/zombie, not a permission or enumeration error
        if read != 64 or ctypes.get_errno():
            return False
        if info[0] == pid and info[2] == pgid and info[3] != 5:
            return False
    return True


def stop(process: subprocess.Popen[bytes]) -> None:
    # Retain the unreaped leader until signaling ends; do not signal a recycled PGID.
    for sig, delay in ((signal.SIGTERM, 0.08), (signal.SIGKILL, 0)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            if sys.platform != "darwin" or not darwin_group_has_no_live_members(process.pid):
                raise
            break
        if delay:
            time.sleep(delay)
    process.wait(timeout=2)


def launch(
    node: str, request: dict[str, object], *, stdout_cap: int = 4096,
    stderr_cap: int = 65536, timeout: float = 3,
) -> dict[str, object]:
    """Own staging, one public spawn, input/capture, wait, and temp cleanup."""

    with tempfile.TemporaryDirectory(prefix="issue8-a-spike-") as directory:
        root = Path(directory).resolve()
        runtime = root / "runtime"
        cwd = root / "cwd"
        runtime.mkdir(mode=0o700)
        cwd.mkdir(mode=0o700)
        for name, content in ASSETS.items():
            asset = runtime / name
            asset.write_bytes(content)
            asset.chmod(0o400)
        payload = json.dumps(request, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        argv = [node, "--max-old-space-size=512", str(runtime / "a-bootstrap.mjs")]
        process = subprocess.Popen(
            argv, cwd=cwd, env=ENVIRONMENT, shell=False, close_fds=True,
            pass_fds=(), start_new_session=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        assert process.stdin and process.stdout and process.stderr
        selector = selectors.DefaultSelector()
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        counts = {"stdout": 0, "stderr": 0}
        status = "ok"
        offset = 0
        deadline = time.monotonic() + timeout
        for pipe in (process.stdin, process.stdout, process.stderr):
            os.set_blocking(pipe.fileno(), False)
        selector.register(process.stdin, selectors.EVENT_WRITE, ("stdin", len(payload)))
        selector.register(process.stdout, selectors.EVENT_READ, ("stdout", stdout_cap))
        selector.register(process.stderr, selectors.EVENT_READ, ("stderr", stderr_cap))
        try:
            while selector.get_map():
                left = deadline - time.monotonic()
                if left <= 0:
                    status = "timeout"
                    break
                for key, _ in selector.select(min(left, 0.05)):
                    name, cap = key.data
                    if name == "stdin":
                        try:
                            offset += os.write(key.fd, payload[offset:offset + 4096])
                        except BrokenPipeError:
                            offset = len(payload)
                        if offset == len(payload):
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                        continue
                    # Count before retention, read at most remaining cap+1.
                    chunk = os.read(key.fd, min(65536, cap - counts[name] + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    counts[name] += len(chunk)
                    if counts[name] > cap:
                        status = "output_limit"
                        break
                    buffers[name].extend(chunk)
                if status != "ok":
                    break
            if status == "ok":
                try:
                    process.wait(timeout=max(0.001, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    status = "timeout"
            if status != "ok":
                stop(process)
                buffers = {"stdout": bytearray(), "stderr": bytearray()}
        except BaseException:
            stop(process)
            raise
        finally:
            selector.close()
            for pipe in (process.stdin, process.stdout, process.stderr):
                pipe.close()
        result = {
            "status": status, "returncode": process.returncode,
            "stdout": bytes(buffers["stdout"]) if status == "ok" else None,
            "stderr": bytes(buffers["stderr"]) if status == "ok" else None,
            "stdout_count": counts["stdout"], "stderr_count": counts["stderr"],
            "cwd": str(cwd), "argv": argv,
            "asset_drift": any((runtime / name).read_bytes() != content for name, content in ASSETS.items()),
        }
    result["private_root_removed"] = not root.exists()
    return result


def main(node_override: str | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=node_override is None)
    parser.add_argument("--unsupported", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    node = Path(node_override or args.node).resolve(strict=True)
    assert node.is_file() and os.access(node, os.X_OK)
    initial_hash = hashlib.sha256(node.read_bytes()).hexdigest()
    cases: list[str] = []
    os.environ["NODE_OPTIONS"] = "--this-parent-setting-must-not-be-inherited"
    os.environ["NODE_PATH"] = "/does/not/exist"
    with tempfile.TemporaryDirectory(prefix="issue8-a-marker-") as marker_directory:
        marker = str(Path(marker_directory) / "survived")
        raw_fd = os.open(os.devnull, os.O_RDONLY)
        denied_fd = fcntl.fcntl(raw_fd, fcntl.F_DUPFD, 128)
        os.set_inheritable(denied_fd, True)
        os.close(raw_fd)
        try:
            request = {
                "mode": "report", "request_id": "a-spike-one-request",
                "count": 0, "denied_fd": denied_fd, "marker": marker,
            }
            report_run = launch(str(node), request)
            report = json.loads(report_run["stdout"])
            assert report["schema_version"] == "code-structure-viz.next-launch-spike/v1"
            assert report["request_id"] == request["request_id"]
            assert report_run["private_root_removed"] is True
            assert report_run["asset_drift"] is False
            invalid = launch(str(node), {**request, "extra": "owned-invalid-field"})
            invalid_report = json.loads(invalid["stdout"])
            assert invalid_report["status"] == "protocol_failure"
            assert invalid["returncode"] == 65
            cases.append("invalid request returns only one protocol-failure frame")
            if args.unsupported:
                assert report["status"] == "unsupported_runtime"
                assert report_run["returncode"] == 66
                assert not Path(marker + ".analyzer").exists()
                cases.append("unsupported runtime rejected before analyzer import")
            else:
                assert report["status"] == "ok" and report_run["returncode"] == 0
                observed = report["observed"]
                assert observed["argv"] == [str(node), report_run["argv"][2]]
                assert observed["exec_argv"] == ["--max-old-space-size=512"]
                assert observed["cwd"] == report_run["cwd"]
                assert observed["cwd_entries"] == []
                assert {key: observed["env"][key] for key in ENVIRONMENT} == ENVIRONMENT
                runtime_added_keys = set(observed["env"]) - set(ENVIRONMENT)
                assert runtime_added_keys <= ({"__CF_USER_TEXT_ENCODING"} if sys.platform == "darwin" else set())
                native_environment = subprocess.run(
                    ["/usr/bin/env", "-0"], env=ENVIRONMENT, shell=False,
                    close_fds=True, capture_output=True, check=True, timeout=3,
                ).stdout
                assert set(native_environment.split(b"\0")) - {b""} == {
                    (key + "=" + value).encode() for key, value in ENVIRONMENT.items()
                }
                assert observed["parent_fd_inherited"] is False
                cases.extend(["single closed JSON response and same-process actual version", "private staged assets and separate empty cwd", "closed argv, exact spawn env, denied inheritable parent FD"])
                second = launch(str(node), request)
                second_report = json.loads(second["stdout"])
                assert second["cwd"] != report_run["cwd"]
                assert second_report["node_version"] == report["node_version"]
                cases.append("repeat run uses different private path with identical retained content")
                for stream, cap in (("stdout", 16 * 1024 * 1024), ("stderr", 64 * 1024)):
                    for extra in (0, 1):
                        output = launch(str(node), {**request, "mode": stream, "count": cap + extra}, stdout_cap=cap if stream == "stdout" else 4096)
                        if extra:
                            assert output["status"] == "output_limit"
                            assert output["stdout"] is None and output["stderr"] is None
                            assert output[stream + "_count"] == cap + 1
                        else:
                            assert output["status"] == "ok" and output["returncode"] == 0
                            assert output[stream] == b"x" * cap
                        assert output["private_root_removed"] is True
                    cases.append(stream + " actual cap and cap+1, no retained partial on failure")
                timed = launch(str(node), {**request, "mode": "descendant"}, timeout=0.35)
                assert timed["status"] == "timeout" and timed["stdout"] is None
                assert Path(marker + ".ready").exists(), "child must start before cleanup test"
                time.sleep(0.75)
                assert not Path(marker).exists(), "TERM-resistant child survived group cleanup"
                assert timed["private_root_removed"] is True
                cases.append("timeout kills TERM-resistant parent/child, waits, and cleans staging")
        finally:
            os.close(denied_fd)
    assert hashlib.sha256(node.read_bytes()).hexdigest() == initial_hash
    result = {
        "scope": "non-production public-spawn feasibility, not TypeScript or security certification",
        "platform": sys.platform, "python": sys.version.split()[0],
        "node_version": report["node_version"], "node_path": str(node),
        "observed_runtime_environment_keys": sorted(report.get("observed", {}).get("env", {})),
        "candidate_sha256": initial_hash,
        "asset_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in ASSETS.items()},
        "cases": cases, "result": "pass",
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    if "--node-stdin" in sys.argv:
        # Probe-only transport of a trusted existing Linux image's executable.
        # This is neither a product runtime download nor a bundled Node design.
        sys.argv.remove("--node-stdin")
        with tempfile.TemporaryDirectory(prefix="issue8-trusted-probe-node-") as node_directory:
            candidate = Path(node_directory) / "node"
            count = 0
            with candidate.open("xb") as output:
                while chunk := sys.stdin.buffer.read(1024 * 1024):
                    count += len(chunk)
                    assert count <= 160 * 1024 * 1024, "trusted probe executable exceeds bound"
                    output.write(chunk)
            candidate.chmod(0o500)
            main(str(candidate))
    else:
        main()
