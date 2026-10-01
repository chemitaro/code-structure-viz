// Disposable first-party bootstrap: no product analyzer or target code.
const version = process.versions.node;
const frame = { schema_version: "code-structure-viz.next-launch-spike/v1", node_version: version };
let request;
try {
  const chunks = [];
  let count = 0;
  for await (const chunk of process.stdin) {
    count += chunk.length;
    if (count > 4096) throw new Error("request-limit");
    chunks.push(chunk);
  }
  request = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  if (Object.keys(request).sort().join(",") !== "count,denied_fd,marker,mode,request_id") {
    throw new Error("request-shape");
  }
} catch {
  request = undefined;
  process.stdout.write(JSON.stringify({ ...frame, status: "protocol_failure" }) + "\n");
  process.exitCode = 65;
}
if (request !== undefined) {
  const stable = /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/.exec(version);
  if (!stable || Number(stable[1]) < 22) {
    process.stdout.write(JSON.stringify({ ...frame, status: "unsupported_runtime", request_id: request.request_id }) + "\n");
    process.exitCode = 66;
  } else {
    // Import is deliberately after the actual process version check.
    const { analyze } = await import("./a-analyzer.mjs");
    await analyze(request, frame);
  }
}
