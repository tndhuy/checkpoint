import { spawn } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { createInterface } from "node:readline";

const skillPath = process.argv[2] ? resolve(process.argv[2]) : null;
const taskPath = process.argv[3] ? resolve(process.argv[3]) : null;
const outputPath = process.argv[4] ? resolve(process.argv[4]) : null;
if (!skillPath || !taskPath || !outputPath) {
  console.error("usage: node smoke_codex_app_server.mjs <SKILL.md> <task.md> <output.md>");
  process.exit(2);
}
const task = await readFile(taskPath, "utf8");

const child = spawn("codex", ["app-server", "--stdio", "--disable", "plugin_hooks"], {
  stdio: ["pipe", "pipe", "pipe"],
});

const pending = new Map();
const completedMessages = [];
let nextId = 1;
let turnResolve;
let turnReject;
const turnDone = new Promise((resolve, reject) => {
  turnResolve = resolve;
  turnReject = reject;
});

function send(message) {
  child.stdin.write(`${JSON.stringify(message)}\n`);
}

function request(method, params) {
  const id = nextId++;
  send({ id, method, params });
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

createInterface({ input: child.stdout }).on("line", (line) => {
  let message;
  try { message = JSON.parse(line); } catch { return; }
  if (Object.hasOwn(message, "id") && pending.has(message.id)) {
    const waiter = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) waiter.reject(new Error(JSON.stringify(message.error)));
    else waiter.resolve(message.result);
    return;
  }
  if (Object.hasOwn(message, "id") && message.method) {
    send({ id: message.id, error: { code: -32601, message: "No server requests allowed in read-only smoke test" } });
    return;
  }
  if (message.method === "item/completed" && message.params?.item?.type === "agentMessage") {
    completedMessages.push(message.params.item.text);
  }
  if (message.method === "turn/completed") {
    if (message.params?.turn?.status === "completed") turnResolve(message.params.turn);
    else turnReject(new Error(JSON.stringify(message.params?.turn?.error || message.params?.turn)));
  }
});

let stderr = "";
child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
child.on("exit", (code) => {
  if (code && !completedMessages.length) turnReject(new Error(`app-server exited ${code}: ${stderr}`));
});

const timeout = setTimeout(() => {
  turnReject(new Error(`app-server smoke test timed out: ${stderr}`));
  child.kill("SIGTERM");
}, 120_000);

try {
  await request("initialize", {
    clientInfo: { name: "checkpoint-skill-smoke", title: "Checkpoint Skill Smoke", version: "0.1.0" },
    capabilities: { experimentalApi: true, requestAttestation: false },
  });
  send({ method: "initialized" });
  const started = await request("thread/start", {
    cwd: "/private/tmp",
    approvalPolicy: "never",
    sandbox: "read-only",
    ephemeral: true,
    config: { orchestrator: { mcp: { enabled: false } } },
  });
  await request("turn/start", {
    threadId: started.thread.id,
    input: [
      {
        type: "text",
        text: `$checkpoint Create a chat-only checkpoint from the supplied task state. Do not use tools or write files. Return only the checkpoint.\n\n${task}`,
        text_elements: [],
      },
      { type: "skill", name: "checkpoint", path: skillPath },
    ],
    cwd: "/private/tmp",
    approvalPolicy: "never",
    sandboxPolicy: { type: "readOnly", networkAccess: false },
    effort: "low",
  });
  const turn = await turnDone;
  const fromTurn = turn.items?.filter((item) => item.type === "agentMessage").map((item) => item.text) || [];
  const output = [...completedMessages, ...fromTurn].filter(Boolean).at(-1);
  if (!output) throw new Error(`no final agent message; stderr: ${stderr}`);
  await writeFile(outputPath, `${output.trim()}\n`, "utf8");
  console.log(output);
} finally {
  clearTimeout(timeout);
  child.kill("SIGTERM");
}
