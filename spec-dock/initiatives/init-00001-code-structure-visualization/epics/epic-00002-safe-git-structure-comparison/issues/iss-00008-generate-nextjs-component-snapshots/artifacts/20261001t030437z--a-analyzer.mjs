// Synthetic owned probe only. It is not a TypeScript implementation.
import { fstatSync, readdirSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";

export async function analyze(request, frame) {
  if (request.marker) writeFileSync(request.marker + ".analyzer", "initialized");
  if (request.mode === "report") {
    let parentFdInherited = true;
    try { fstatSync(request.denied_fd); } catch { parentFdInherited = false; }
    process.stdout.write(JSON.stringify({
      ...frame, status: "ok", request_id: request.request_id,
      observed: {
        argv: process.argv, exec_argv: process.execArgv, cwd: process.cwd(),
        cwd_entries: readdirSync(process.cwd()), env: process.env,
        parent_fd_inherited: parentFdInherited, pid: process.pid,
      },
    }) + "\n");
  } else if (request.mode === "stdout" || request.mode === "stderr") {
    const stream = request.mode === "stdout" ? process.stdout : process.stderr;
    stream.write(Buffer.alloc(request.count, "x"));
  } else if (request.mode === "descendant") {
    // Only this known synthetic probe intentionally spawns a child.
    const source = `const fs=require('node:fs'); process.on('SIGTERM',()=>{}); fs.writeFileSync(${JSON.stringify(request.marker + ".ready")},'ready'); setTimeout(()=>fs.writeFileSync(${JSON.stringify(request.marker)},'survived'),650); setInterval(()=>{},1000);`;
    spawn(process.execPath, ["-e", source], { stdio: "ignore", env: process.env });
    process.on("SIGTERM", () => {});
    setInterval(() => {}, 1000);
  } else {
    throw new Error("owned probe mode is invalid");
  }
}
