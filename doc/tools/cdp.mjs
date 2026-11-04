// Usage: node cdp.mjs <fileurl> <outprefix> <width> <height> <spec...>
// spec = "id:offsetPx" scrolls to element top + offset, then screenshots.
// Al final informa errores de JS y si la página desborda en horizontal (scrollWidth > innerWidth).
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";
const [url, out, W, H, ...specs] = process.argv.slice(2);
const port = 9333;
const chrome = spawn("google-chrome", ["--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${port}`, `--window-size=${W},${H}`, "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let i = 0; i < 40; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.length) break; } catch {} await sleep(250); }
const page = targets.find(t => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r));
let id = 0; const pending = new Map(); const logs = [];
ws.addEventListener("message", ev => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === "Runtime.exceptionThrown") logs.push("EXC " + JSON.stringify(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
  if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") logs.push("ERR " + JSON.stringify(m.params.args.map(a => a.value)));
});
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Runtime.enable"); await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: +W, height: +H, deviceScaleFactor: 1, mobile: +W < 700 });
await send("Page.navigate", { url }); await sleep(2500);
for (const s of specs) {
  const [sid, off] = s.split(":");
  // scroll in small increments so IntersectionObservers fire like a real user
  await send("Runtime.evaluate", { expression: `(async()=>{const e=document.getElementById('${sid}');const target=e.getBoundingClientRect().top+scrollY+(${off});let y=Math.max(0,target-1500);while(y<target){y=Math.min(target,y+120);scrollTo(0,y);await new Promise(r=>setTimeout(r,30));}})()`, awaitPromise: true });
  await sleep(1600);
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(`${out}_${sid}_${off}.png`, Buffer.from(r.result.data, "base64"));
}
const ov = await send("Runtime.evaluate", { expression: "JSON.stringify({scrollWidth: document.documentElement.scrollWidth, innerWidth: innerWidth})", returnByValue: true });
console.log("ancho:", ov.result.result.value);
console.log(logs.length ? logs.join("\n") : "no JS errors");
ws.close(); chrome.kill();
