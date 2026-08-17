"""Live orchestration engine: a LangGraph plan/act loop over orchestrator and executor agents.

Imported only in live mode; litellm and langgraph are imported lazily."""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any, TypedDict

from .. import steer
from ..bus import Bus, browser_channel, chat_channel, control_channel, shell_channel, shell_input_channel
from ..config import settings
from ..db import session_scope
from ..repositories import agents as agents_repo
from ..repositories import chat as chat_repo
from ..repositories import files as files_repo
from ..repositories import findings as findings_repo
from ..repositories import hosts as hosts_repo
from ..repositories import ids
from ..repositories import listeners as listeners_repo
from ..repositories import loot as loot_repo
from ..repositories import provider_credentials as creds_repo
from ..repositories import proxies as proxies_repo
from ..repositories import runs as runs_repo
from ..repositories import servers as servers_repo
from ..repositories import sessions as sessions_repo
from ..repositories import settings as settings_repo
from ..repositories import shells as shells_repo
from ..schemas import ExecutionSettings, LlmSettings
from ..storage import storage
from . import msf, nmap, pivot, webscan
from .browser import BrowserManager
from .execution import ExecResult, build_backend
from .llm import LlmClient
from .tools import (
    EXECUTOR_TOOLS,
    ORCHESTRATOR_TOOLS,
    codescan_executor_system,
    codescan_orchestrator_system,
    executor_system,
    orchestrator_system,
)

MAX_ORCH_STEPS = 40
MAX_EXEC_STEPS = 10

# Fallback CVSS when a finding is recorded without a numeric score.
_CVSS_BY_SEVERITY = {"critical": 9.5, "high": 8.0, "medium": 5.5, "low": 3.1, "info": 0.0}


def _resolve_cvss(args: dict[str, Any]) -> float:
    raw = args.get("cvss")
    try:
        score = float(raw) if raw is not None else 0.0
    except (TypeError, ValueError):
        score = 0.0
    if score <= 0.0:
        score = _CVSS_BY_SEVERITY.get(str(args.get("severity", "info")).lower(), 0.0)
    return round(max(0.0, min(10.0, score)), 1)


def _is_source_url(source: str) -> bool:
    s = source.strip().lower()
    return "://" in s or s.startswith("git@")


def _safe_source(source: str) -> bool:
    """Reject shell metacharacters to prevent command injection via a source path."""
    return not any(c in source for c in ("'", '"', ";", "|", "&", "`", "$", "\n", "\\", "<", ">", "("))


def _proxy_url_with_creds(proxy, secret: str | None) -> str:
    """Fold proxy credentials into its URL (scheme://user:pass@host:port),
    deriving the scheme from the proxy kind when the URL omits it."""
    url = (proxy.url or "").strip()
    if "://" not in url:
        scheme = "socks5" if getattr(proxy, "kind", "") == "socks5" else "http"
        url = f"{scheme}://{url}"
    user = getattr(proxy, "username", None)
    if user and secret and "@" not in url.split("://", 1)[1]:
        scheme, rest = url.split("://", 1)
        return f"{scheme}://{user}:{secret}@{rest}"
    return url


# TCP catcher run inside the remote Kali container (--network host binds on the
# VPS public interface). Accepts one reverse shell, bridges the socket to its
# stdin/stdout over the SSH `docker exec -i` channel. Base64-shipped to avoid
# shell quoting.
_REMOTE_LISTENER_PY = (
    "import socket,sys,os,threading\n"
    "p=int(sys.argv[1])\n"
    "s=socket.socket()\n"
    "s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n"
    "s.bind(('0.0.0.0',p))\n"
    "s.listen(1)\n"
    "sys.stderr.write('LISTENING %d\\n'%p);sys.stderr.flush()\n"
    "c,a=s.accept()\n"
    "sys.stderr.write('CONNECT %s:%d\\n'%(a[0],a[1]));sys.stderr.flush()\n"
    "def _pin():\n"
    "    while True:\n"
    "        d=os.read(0,4096)\n"
    "        if not d:break\n"
    "        try:c.sendall(d)\n"
    "        except Exception:break\n"
    "threading.Thread(target=_pin,daemon=True).start()\n"
    "while True:\n"
    "    d=c.recv(4096)\n"
    "    if not d:break\n"
    "    os.write(1,d)\n"
)


class _State(TypedDict, total=False):
    messages: list[dict[str, Any]]
    steps: int
    done: bool
    pending: dict[str, Any] | None


class LiveRunner:
    def __init__(self, bus: Bus, run_id: str) -> None:
        self.bus = bus
        self.run_id = run_id
        self.llm: LlmClient | None = None
        self.backend = None
        self.orch_id = ""
        self.session_id = ""
        self.scope: list[str] = []
        self.targets: list[str] = []
        self.roe: str | None = None
        self.run_name = ""
        self.kind = "network"
        self.source: str | None = None
        self.brief: str | None = None
        self.instruction: str | None = None
        self.assessment_files: list[str] = []
        self._assessment_meta: list[tuple[str, str, str]] = []  # (bucket, key, filename)
        self.server = None  # the chosen remote Server row, or None for local
        self._listener_tasks: list[asyncio.Task] = []
        self._browser: BrowserManager | None = None
        self._pivot: pivot.PivotManager | None = None
        self._current_cmd_task: asyncio.Task | None = None
        self._interrupted = False

    async def run(self) -> None:
        await self._load()
        if self._browser is not None:
            self._listener_tasks.append(asyncio.create_task(self._watch_browser_control()))
        if self.kind != "code":
            await self._seed_targets()
        try:
            try:
                await self.backend.start(on_status=self._status)
            except Exception as exc:
                # Backend unavailable: keep the agent loop running with simulated output.
                from .execution import SimBackend
                await self._event("orchestrator", "steer",
                                  f"execution backend unavailable ({exc}); using simulated execution")
                self.backend = SimBackend()
                if self._browser is not None:
                    self._browser.backend = self.backend
            self._listener_tasks.append(asyncio.create_task(self._watch_control()))
            if self._assessment_meta:
                await self._stage_assessment_files()
            if self.kind == "code":
                await self._prepare_source()
            await self._orchestrate()
            async with session_scope() as s:
                await runs_repo.set_status(s, self.run_id, "completed")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._event("orchestrator", "steer", f"engine error: {exc}")
            async with session_scope() as s:
                await runs_repo.set_status(s, self.run_id, "failed")
        finally:
            for t in self._listener_tasks:
                t.cancel()
            if self._pivot is not None:
                try:
                    await self._pivot.close()
                except Exception:
                    pass
            if self._browser is not None:
                try:
                    await self._browser.stop()
                except Exception:
                    pass
            if self.backend is not None:
                await self.backend.close()

    async def _load(self) -> None:
        server = server_secret = proxy_url = None
        mounts = None
        async with session_scope() as s:
            run = await runs_repo.get(s, self.run_id)
            session = await sessions_repo.get(s, run.session_id)
            cfg = await settings_repo.get(s)
            self.session_id = session.id
            self.scope = session.scope or []
            self.targets = session.targets or []
            self.roe = session.roe
            self.run_name = run.name
            self.kind = session.kind or "network"
            self.source = session.source
            self.brief = session.brief
            self.instruction = run.instruction
            afiles = await files_repo.list_for_session(s, session.id, kind="assessment")
            self.assessment_files = [f.filename for f in afiles]
            self._assessment_meta = [(f.bucket, f.object_key, f.filename) for f in afiles]
            base = LlmSettings(**cfg.llm) if cfg.llm else LlmSettings()
            # Run picks provider + model; key comes from that provider's stored
            # credential, falling back to the legacy single key.
            provider = run.provider or base.provider
            model = run.model or base.model
            api_key, api_base = await creds_repo.get_secret(s, provider)
            # Legacy single key only belongs to the default (base) provider.
            if not api_key and provider == base.provider:
                api_key, api_base = base.api_key, base.api_base
            llm_cfg = LlmSettings(
                provider=provider, model=model,
                api_key=api_key,
                api_base=api_base or base.api_base,
                reasoning_effort=base.reasoning_effort,
            )
            exec_cfg = ExecutionSettings(**cfg.execution) if cfg.execution else ExecutionSettings()
            # Per-session execution routing: a chosen server (SSH) and/or proxy.
            if session.server_id:
                server = await servers_repo.get(s, session.server_id)
                if server is not None:
                    server_secret = await servers_repo.get_secret(s, session.server_id)
            self.server = server
            if session.proxy_id:
                proxy = await proxies_repo.get(s, session.proxy_id)
                if proxy is not None:
                    secret = await proxies_repo.get_secret(s, session.proxy_id)
                    proxy_url = _proxy_url_with_creds(proxy, secret)
            self.orch_id = await self._ensure_orchestrator(s)
        # A code scan against a local folder mounts it read-only at /src.
        if self.kind == "code" and self.source and not _is_source_url(self.source):
            mounts = [f"{self.source}:/src:ro"]
        if self.llm is None:
            self.llm = LlmClient(llm_cfg)
        if self.backend is None:
            # Name the container per session so a session's runs reuse it.
            self.backend = build_backend(exec_cfg, server=server, server_secret=server_secret,
                                         proxy_url=proxy_url, name=f"redcell-exec-{self.session_id[:12]}",
                                         mounts=mounts)
        if self._browser is None and self.kind != "code":
            self._browser = BrowserManager(self.backend, self.session_id, self.bus)

    async def _ensure_orchestrator(self, s) -> str:
        nodes, _ = await agents_repo.graph(s, self.run_id)
        root = next((a for a in nodes if a.role == "root"), None)
        if root:
            return root.id
        agent = await agents_repo.add(s, {"run_id": self.run_id, "name": "orchestrator",
                                          "role": "root", "status": "running", "action": "planning", "calls": 0})
        return agent.id

    # ---- LangGraph plan/act loop ----
    async def _orchestrate(self) -> None:
        from langgraph.graph import END, StateGraph

        graph = StateGraph(_State)
        graph.add_node("plan", self._plan)
        graph.add_node("act", self._act)
        graph.set_entry_point("plan")
        # plan may decide to stop (finish / budget / stopped): route straight to
        # END so `act` cannot clobber the stop signal. Otherwise plan -> act -> plan.
        graph.add_conditional_edges("plan", lambda st: END if st.get("done") else "act",
                                    {END: END, "act": "act"})
        graph.add_conditional_edges("act", lambda st: END if st.get("done") else "plan",
                                    {END: END, "plan": "plan"})

        # durable checkpointing: state is saved to SQLite (via aiosqlite) after
        # every step so a crash or restart can resume the run.
        saver = None
        try:
            from .checkpoint import get_checkpointer
            saver = await get_checkpointer()
        except Exception as exc:
            await self._event("orchestrator", "steer",
                              f"checkpointing unavailable ({exc}); running without crash-resume")

        app = graph.compile(checkpointer=saver) if saver else graph.compile()

        system = (codescan_orchestrator_system(self.run_name, self.source or "")
                  if self.kind == "code"
                  else orchestrator_system(self.run_name, self.scope, self.targets, self.roe,
                                           brief=self.brief, instruction=self.instruction,
                                           files=self.assessment_files))
        init: _State = {
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": "Begin the engagement."}],
            "steps": 0, "done": False,
        }
        if not saver:
            await app.ainvoke(init, config={"recursion_limit": MAX_ORCH_STEPS * 2 + 4})
            return

        config = {"configurable": {"thread_id": self.run_id},
                  "recursion_limit": MAX_ORCH_STEPS * 2 + 4}
        snap = await app.aget_state(config)
        if snap is None or not snap.values:
            # Never started: run from the top.
            await app.ainvoke(init, config=config)
        elif snap.next:
            # Interrupted mid-run (crash/restart): resume exactly where it stopped.
            await self._event("orchestrator", "steer", "resuming from the last checkpoint")
            await app.ainvoke(None, config=config)
        else:
            # Previously finished, reopened by an operator directive: re-enter with a
            # fresh step budget, preserving conversation history.
            await self._event("orchestrator", "steer", "continuing the engagement on operator request")
            await app.ainvoke({"done": False, "steps": 0}, config=config)

    async def _plan(self, state: _State) -> _State:
        await self._gate()
        if await self._stopped():
            return {**state, "done": True}
        if state.get("steps", 0) >= MAX_ORCH_STEPS:
            await self._event("orchestrator", "steer",
                              f"reached the {MAX_ORCH_STEPS}-step budget; concluding the run")
            return {**state, "done": True}
        directives = await steer.drain_steer(self.run_id)
        messages_in = state["messages"]
        for d in directives:
            messages_in = messages_in + [{"role": "user", "content": f"[Operator steer] {d}"}]
            await self._event("orchestrator", "steer", f"operator: {d[:80]}")
        msg = await self._complete(messages_in, ORCHESTRATOR_TOOLS)
        messages = messages_in + [self._assistant_msg(msg)]
        return {**state, "messages": messages, "steps": state.get("steps", 0) + 1, "pending": msg}

    async def _act(self, state: _State) -> _State:
        msg = state.get("pending")
        if not msg or not msg.get("tool_calls"):
            nudge = {"role": "user", "content": "Use a tool: delegate, record_finding, ask_operator, or finish."}
            return {**state, "messages": state["messages"] + [nudge]}
        messages = state["messages"]
        done = False
        for call in msg["tool_calls"]:
            name = call["name"]
            args = _parse_args(call["arguments"])
            result = await self._dispatch(name, args)
            messages = messages + [{"role": "tool", "tool_call_id": call["id"], "name": name,
                                    "content": json.dumps(result)}]
            if name == "finish":
                done = True
        return {**state, "messages": messages, "done": done}

    async def _dispatch(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "delegate":
            return await self._delegate(args.get("agent", "executor"), args.get("objective", ""))
        if name == "record_finding":
            return await self._record_finding(args)
        if name == "record_loot":
            return await self._record_loot(args)
        if name == "record_host":
            return await self._record_host(args)
        if name == "start_listener":
            return await self._start_listener(int(args.get("port", 4444)))
        if name == "open_pivot":
            return await self._open_pivot(args.get("shellId") or args.get("shell_id", ""))
        if name == "close_pivot":
            return await self._close_pivot()
        if name == "ask_operator":
            return {"operator_reply": await self._ask_operator(args.get("question", ""), args.get("options"))}
        if name == "finish":
            await self._event("orchestrator", "steer", "run finished: " + args.get("summary", ""))
            return {"ok": True}
        return {"error": f"unknown tool {name}"}

    async def _dispatch_browser(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if self._browser is None:
            return {"error": "browser not available for this session"}
        # Authoritative ownership: read the durable value before every action, so a
        # take/release is honored even if the live subscription missed it.
        self._browser.set_owner(await steer.get_browser_owner(self.session_id))
        if name == "browser_open":
            return await self._browser.open(args.get("url", ""))
        if name == "browser_click":
            return await self._browser.click(args.get("selector", ""))
        if name == "browser_type":
            return await self._browser.type(args.get("selector", ""), args.get("text", ""),
                                            bool(args.get("submit")))
        if name == "browser_read":
            return await self._browser.read()
        if name == "browser_screenshot":
            res = await self._browser.screenshot()
            if res.get("ok") and res.get("b64"):
                # Persist the PNG to the loot bucket and record it as evidence; keep the
                # blob out of the agent's context and hand back a stable artifact key.
                key = f"browser/{self.run_id}/{ids.new_id('shot')}.png"
                try:
                    await storage.put(settings.bucket_loot, key, base64.b64decode(res["b64"]), "image/png")
                    await self._record_loot({"kind": "file", "label": "browser screenshot",
                                             "value": key, "source": "browser"})
                except Exception as exc:
                    return {"ok": False, "error": f"screenshot capture ok but store failed: {exc}"[:200]}
                return {"ok": True, "captured": True, "artifact": key, "url": res.get("url")}
            return res
        return {"error": f"unknown browser tool {name}"}

    async def _watch_browser_control(self) -> None:
        """Flip the browser's control owner when the operator takes or releases it.
        Loads the persisted owner first so a take-control that landed before this
        subscription is not lost, then follows live updates on the channel."""
        if self._browser is not None:
            self._browser.set_owner(await steer.get_browser_owner(self.session_id))
        try:
            async for payload in self.bus.subscribe(browser_channel(self.session_id)):
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if self._browser is not None and "owner" in data:
                    self._browser.set_owner(data["owner"])
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._event("orchestrator", "steer", f"browser control watch ended: {exc}")

    # ---- structured tool integrations ----
    async def _dispatch_toolset(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "nmap_scan":
            return await self._run_nmap(args)
        if name == "nuclei_scan":
            return await self._run_nuclei(args)
        if name == "web_discover":
            return await self._run_web_discover(args)
        if name == "msf_search":
            return await self._run_msf_search(args)
        if name == "msf_run":
            return await self._run_msf_run(args)
        return {"error": f"unknown tool {name}"}

    async def _run_nmap(self, args: dict[str, Any]) -> dict[str, Any]:
        target = str(args.get("target", "")).strip()
        if not target:
            return {"error": "target required"}
        pivoting = self._pivot is not None and self._pivot.active
        cmd = nmap.build_nmap_command(target, ports=args.get("ports"),
                                      service_detection=bool(args.get("service_detection")),
                                      scripts=bool(args.get("scripts")),
                                      connect_scan=pivoting)
        # Through a pivot, tunnel the connect scan over the SOCKS proxy so internal
        # hosts are reachable; discovered hosts are tagged as pivot-sourced.
        cmd = pivot.proxychains_wrap(cmd, pivoting)
        res = await self._exec(cmd)
        hosts = nmap.parse_nmap_xml(getattr(res, "output", "") or "")
        for h in hosts:
            await self._record_host({
                "host": (h["hostnames"][0] if h["hostnames"] else h["ip"]) or target,
                "ip": h["ip"],
                "ports": [{"port": p["port"], "service": p["service"], "version": p["version"]}
                          for p in h["ports"]],
                "source": "pivot" if pivoting else "nmap",
            })
        open_ports = sum(len(h["ports"]) for h in hosts)
        summary = [{"ip": h["ip"], "hostnames": h["hostnames"][:2], "ports": h["ports"][:20]}
                   for h in hosts[:20]]
        return {"ok": True, "hosts_up": len(hosts), "open_ports": open_ports, "hosts": summary}

    async def _run_nuclei(self, args: dict[str, Any]) -> dict[str, Any]:
        target = str(args.get("target", "")).strip()
        if not target:
            return {"error": "target required"}
        cmd = webscan.build_nuclei_command(target, severity=args.get("severity"))
        res = await self._exec(cmd)
        findings = webscan.parse_nuclei_jsonl(getattr(res, "output", "") or "", target=target)
        for f in findings:
            await self._record_finding(f)
        return {"ok": True, "findings": len(findings), "titles": [f["title"] for f in findings[:20]]}

    async def _run_web_discover(self, args: dict[str, Any]) -> dict[str, Any]:
        url = str(args.get("url", "")).strip()
        if not url:
            return {"error": "url required"}
        cmd = webscan.build_ffuf_command(url, wordlist=args.get("wordlist"),
                                         vhost=(args.get("mode") == "vhost"))
        res = await self._exec(cmd)
        results = webscan.parse_ffuf_json(getattr(res, "output", "") or "")
        return {"ok": True, "found": len(results), "results": results[:50]}

    async def _run_msf_search(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query", "")).strip()
        if not query:
            return {"error": "query required"}
        res = await self._exec(msf.build_msf_search(query))
        modules = msf.parse_msf_search(getattr(res, "output", "") or "")
        return {"ok": True, "count": len(modules), "modules": modules[:40]}

    async def _run_msf_run(self, args: dict[str, Any]) -> dict[str, Any]:
        module = str(args.get("module", "")).strip()
        if not msf.valid_module(module):
            return {"error": "invalid module path"}
        options = args.get("options") if isinstance(args.get("options"), dict) else {}
        cmd = msf.build_msf_run(module, {str(k): str(v) for k, v in options.items()})
        res = await self._exec(cmd)
        return {"ok": True, "output": (getattr(res, "output", "") or "")[-3000:]}

    # ---- executor sub-agent ----
    async def _delegate(self, agent_name: str, objective: str) -> dict[str, Any]:
        async with session_scope() as s:
            agent = await agents_repo.add(s, {"run_id": self.run_id, "name": agent_name, "role": "executor",
                                              "status": "running", "parent_id": self.orch_id,
                                              "action": objective[:80], "calls": 0})
            await agents_repo.add_edge(s, self.run_id, self.orch_id, agent.id)
            shell = await shells_repo.create(s, {"session_id": self.session_id, "kind": "tool",
                                                 "label": agent_name, "status": "running", "pty": False})
            agent_id, shell_id = agent.id, shell.id
        await self._event(agent_name, "steer", f"delegated: {objective}")

        exec_system = (codescan_executor_system(agent_name, objective) if self.kind == "code"
                       else executor_system(agent_name, objective))
        messages = [{"role": "system", "content": exec_system},
                    {"role": "user", "content": "Start."}]
        report: dict[str, Any] = {}
        outputs: list[str] = []
        findings_here: list[str] = []
        calls = 0
        for i in range(MAX_EXEC_STEPS):
            await self._gate()
            if await self._stopped():
                break
            if i == MAX_EXEC_STEPS - 1:
                messages.append({"role": "user", "content": (
                    "Step budget reached. Call report now with a concise summary of what you found "
                    "and any finding.")})
            msg = await self._complete(messages, EXECUTOR_TOOLS)
            messages.append(self._assistant_msg(msg))
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                if msg.get("content"):  # plain text -> treat as the report
                    report = {"summary": msg["content"][:600]}
                break
            stop = False
            for call in tool_calls:
                cname = call["name"]
                cargs = _parse_args(call["arguments"])
                if cname == "run_command":
                    cmd = cargs.get("command", "")
                    calls += 1
                    async with session_scope() as s:
                        await agents_repo.update(s, agent_id, action=cmd[:80], calls=calls)
                    await self._event(agent_name, "tool", f"$ {cmd}")
                    res = await self._exec(cmd, on_output=lambda line: self._shell_out(shell_id, line))
                    outputs.append(f"$ {cmd}\n{res.output}")
                    messages.append({"role": "tool", "tool_call_id": call["id"], "name": cname,
                                     "content": res.output[:4000]})
                elif cname == "report":
                    report = cargs
                    fnd = cargs.get("finding")
                    if fnd:
                        await self._record_finding({**fnd, "status": fnd.get("status", "candidate")})
                        if fnd.get("title"):
                            findings_here.append(fnd["title"])
                    stop = True
                elif cname.startswith("browser_"):
                    calls += 1
                    label = (cargs.get("url") or cargs.get("selector") or "").strip()
                    async with session_scope() as s:
                        await agents_repo.update(s, agent_id, action=f"{cname} {label}".strip()[:80], calls=calls)
                    await self._event(agent_name, "tool", f"[browser] {cname} {label}".strip())
                    res = await self._dispatch_browser(cname, cargs)
                    messages.append({"role": "tool", "tool_call_id": call["id"], "name": cname,
                                     "content": json.dumps(res)[:2000]})
                elif cname in ("nmap_scan", "nuclei_scan", "web_discover", "msf_search", "msf_run"):
                    calls += 1
                    label = str(cargs.get("target") or cargs.get("url") or cargs.get("query")
                                or cargs.get("module") or "")[:60]
                    async with session_scope() as s:
                        await agents_repo.update(s, agent_id, action=f"{cname} {label}".strip()[:80], calls=calls)
                    await self._event(agent_name, "tool", f"[{cname}] {label}".strip())
                    res = await self._dispatch_toolset(cname, cargs)
                    messages.append({"role": "tool", "tool_call_id": call["id"], "name": cname,
                                     "content": json.dumps(res)[:4000]})
            if stop or self._interrupted:
                break

        if self._interrupted:
            self._interrupted = False
            await self._event(agent_name, "steer", "interrupted by operator; returning to the orchestrator")

        async with session_scope() as s:
            await agents_repo.update(s, agent_id, status="done")
            await shells_repo.set_status(s, shell_id, "idle")
        summary = report.get("summary") or f"ran {calls} command(s); no explicit summary"
        output_tail = ("\n".join(outputs))[-1800:]
        await self._event(agent_name, "steer", "executor done: " + str(summary)[:120])
        return {"executor": agent_name, "summary": summary, "commands_run": calls,
                "findings": findings_here, "output_tail": output_tail}

    # ---- operator interaction ----
    async def _ask_operator(self, question: str, options: list[str] | None) -> str | None:
        async with session_scope() as s:
            msg = await chat_repo.create(s, self.run_id, "assistant", question, options)
            payload = {"id": msg.id, "runId": self.run_id, "role": "assistant",
                       "text": question, "options": options, "ts": msg.ts}
        await self.bus.publish_json(chat_channel(self.run_id), payload)
        await steer.set_awaiting(self.run_id, True)
        try:
            return await self._await_operator(timeout=600)
        finally:
            await steer.set_awaiting(self.run_id, False)

    async def _await_operator(self, timeout: float) -> str | None:
        async def wait() -> str | None:
            async for payload in self.bus.subscribe(chat_channel(self.run_id)):
                try:
                    data = json.loads(payload)
                except Exception:
                    continue
                if data.get("role") == "operator":
                    return data.get("text")
            return None

        try:
            return await asyncio.wait_for(wait(), timeout=timeout)
        except TimeoutError:
            await self._event("orchestrator", "steer", "operator did not answer; proceeding conservatively")
            return None

    async def _watch_control(self) -> None:
        try:
            async for raw in self.bus.subscribe(control_channel(self.run_id)):
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                if msg.get("action") in ("stop", "interrupt"):
                    task = self._current_cmd_task
                    if task is not None and not task.done():
                        task.cancel()
        except asyncio.CancelledError:
            raise
        except Exception:
            pass

    async def _stage_assessment_files(self) -> None:
        for bucket, key, name in self._assessment_meta:
            try:
                data = await storage.get_bytes(bucket, key)
                await self.backend.stage_file(f"/root/assessment/{name}", data)
                await self._event("orchestrator", "steer", f"staged assessment file: {name}")
            except Exception as exc:
                await self._event("orchestrator", "steer", f"could not stage {name}: {exc}")

    async def _exec(self, command: str, on_output=None) -> ExecResult:
        task = asyncio.create_task(self.backend.run(command, on_output=on_output))
        self._current_cmd_task = task
        try:
            return await task
        except asyncio.CancelledError:
            if task.cancelled():
                self._interrupted = True
                return ExecResult(exit_code=130, output="[interrupted by operator]")
            raise
        finally:
            self._current_cmd_task = None

    async def _gate(self) -> None:
        while True:
            async with session_scope() as s:
                run = await runs_repo.get(s, self.run_id)
                status = run.status if run else "stopped"
            if status != "paused":
                return
            await asyncio.sleep(0.5)

    async def _stopped(self) -> bool:
        async with session_scope() as s:
            run = await runs_repo.get(s, self.run_id)
        return run is None or run.status == "stopped"

    # ---- finding + bus helpers ----
    async def _record_finding(self, args: dict[str, Any]) -> dict[str, Any]:
        title = args.get("title", "finding")
        loc = args.get("location", "")
        async with session_scope() as s:
            # Idempotent: a resumed step must not double-record the same finding.
            if await findings_repo.exists(s, self.session_id, title, loc):
                return {"recorded": False, "duplicate": True}
            finding = await findings_repo.create(s, {
                "session_id": self.session_id, "run_id": self.run_id,
                "title": title, "severity": args.get("severity", "info"),
                "cvss": _resolve_cvss(args),
                "location": loc, "cwe": args.get("cwe"),
                "status": args.get("status", "candidate"), "remediation": args.get("remediation"),
            })
            fid, sev = finding.id, finding.severity
        await self._event("orchestrator", "finding", f"[{sev}] {title} @ {loc}")
        return {"id": fid, "recorded": True}

    async def _record_loot(self, args: dict[str, Any]) -> dict[str, Any]:
        label = args.get("label", "loot")
        value = args.get("value", "")
        async with session_scope() as s:
            if await loot_repo.exists(s, self.session_id, label, value):
                return {"recorded": False, "duplicate": True}
            await loot_repo.create(s, {"session_id": self.session_id, "kind": args.get("kind", "other"),
                                       "label": label, "value": value, "source": args.get("source", "")})
        await self._event("orchestrator", "net", f"loot: {args.get('kind', 'item')} {label}")
        return {"recorded": True}

    async def _record_host(self, args: dict[str, Any]) -> dict[str, Any]:
        host = args.get("host", "")
        if not host:
            return {"recorded": False}
        async with session_scope() as s:
            if await hosts_repo.exists(s, self.session_id, host):
                return {"recorded": False, "duplicate": True}
            await hosts_repo.create(s, {"session_id": self.session_id, "host": host, "ip": args.get("ip"),
                                        "ports": args.get("ports") or [], "tech": args.get("tech") or [],
                                        "source": args.get("source", "")})
        await self._event("recon", "net", f"host: {host}")
        return {"recorded": True}

    async def _open_pivot(self, shell_id: str) -> dict[str, Any]:
        """Route tool traffic through a caught reverse shell so internal hosts
        become reachable. Needs a docker backend where the shell and the exec
        container share a host network (the remote/VPS topology)."""
        if not shell_id:
            return {"error": "shellId required (the caught reverse shell to pivot through)"}
        if getattr(self.backend, "kind", "") not in ("local-docker", "remote-docker"):
            return {"error": "pivoting needs a live docker execution backend"}
        async with session_scope() as s:
            shell = await shells_repo.get(s, shell_id)
        if shell is None or shell.session_id != self.session_id:
            return {"error": "reverse shell not found in this session"}
        if shell.kind != "reverse" or shell.status != "running":
            return {"error": "pivot target must be a running reverse shell"}
        if self._pivot is not None and self._pivot.active:
            return {"error": f"a pivot is already active through {self._pivot.shell_id}; close it first"}
        callback = (self.server.host if self.server is not None
                    and getattr(self.backend, "kind", "") == "remote-docker"
                    else settings.callback_host)
        pm = pivot.PivotManager(self.backend, self.bus, callback)
        result = await pm.open(shell_id)
        if result.get("ok"):
            self._pivot = pm
            await self._event("orchestrator", "net", f"pivot up through {shell_id} -> {result.get('socks')}")
        else:
            await self._event("orchestrator", "steer", f"pivot failed: {result.get('detail', 'unknown')}")
        return result

    async def _close_pivot(self) -> dict[str, Any]:
        if self._pivot is None:
            return {"ok": True, "note": "no active pivot"}
        await self._pivot.close()
        self._pivot = None
        await self._event("orchestrator", "net", "pivot closed")
        return {"ok": True}

    async def _start_listener(self, port: int) -> dict[str, Any]:
        bind = f"0.0.0.0:{port}"
        async with session_scope() as s:
            listener = await listeners_repo.create(s, {"session_id": self.session_id, "kind": "tcp",
                                                       "bind": bind, "status": "starting", "sessions_count": 0})
            lid = listener.id
        if self.server is not None and getattr(self.backend, "kind", "") == "remote-docker":
            # Listener runs inside the Kali container on the remote VPS (host
            # network) so internet targets can dial back to the server IP.
            await self._open_remote_listener(port, lid)
            callback = f"{self.server.host}:{port}"
            status = "listening"
        else:
            from .live import get_listener_manager
            status = await get_listener_manager().start(lid)
            callback = f"{settings.callback_host}:{port}"
        await self._event("listener", "net", f"listener {bind} ({status}); reverse-shell callback -> {callback}")
        return {"listenerId": lid, "bind": bind, "status": status, "callback": callback,
                "note": "Use this callback address (host:port) in the reverse-shell payload."}

    async def _open_remote_listener(self, port: int, listener_id: str) -> None:
        """Arm a listener in the remote Kali container and bridge a caught reverse
        shell to a Terminal over the run's SSH connection."""
        async with session_scope() as s:
            await listeners_repo.set_status(s, listener_id, "listening")
            shell = await shells_repo.create(s, {"session_id": self.session_id, "kind": "reverse",
                                                 "label": f"revsh :{port} @ {self.server.host}",
                                                 "status": "running", "host": self.server.host, "pty": True})
            shell_id = shell.id
        self._listener_tasks.append(
            asyncio.create_task(self._remote_listener_bridge(port, listener_id, shell_id)))

    async def _remote_listener_bridge(self, port: int, listener_id: str, shell_id: str) -> None:
        import base64
        try:
            conn = await self.backend.connection()
            b64 = base64.b64encode(_REMOTE_LISTENER_PY.encode()).decode()
            inner = f"import base64;exec(base64.b64decode('{b64}'))"
            from .execution import _shq
            cmd = f"docker exec -i {self.backend.name} python3 -c {_shq(inner)} {int(port)}"
            proc = await conn.create_process(cmd, encoding=None)
        except Exception as exc:
            await self._event("listener", "steer", f"remote listener failed: {exc}")
            async with session_scope() as s:
                await shells_repo.set_status(s, shell_id, "closed")
            return

        async def pump_out() -> None:
            while True:
                data = await proc.stdout.read(4096)
                if not data:
                    break
                await self.bus.publish(shell_channel(shell_id), data.decode(errors="replace"))

        async def pump_in() -> None:
            async for keys in self.bus.subscribe(shell_input_channel(shell_id)):
                try:
                    proc.stdin.write(keys.encode())
                    await proc.stdin.drain()
                except Exception:
                    break

        async def watch() -> None:
            buf = b""
            while True:
                data = await proc.stderr.read(1024)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    text = line.decode(errors="replace").strip()
                    if text.startswith("CONNECT"):
                        remote = text[7:].strip()
                        async with session_scope() as s:
                            sh = await shells_repo.get(s, shell_id)
                            if sh:
                                sh.label = f"revsh {remote}"
                                sh.remote_addr = remote
                            lst = await listeners_repo.get(s, listener_id)
                            if lst:
                                lst.sessions_count += 1
                        await self._event("listener", "net",
                                          f"caught reverse shell from {remote} on {self.server.host}:{port}")

        out_t = asyncio.create_task(pump_out())
        in_t = asyncio.create_task(pump_in())
        try:
            await watch()
            await proc.wait()
        except asyncio.CancelledError:
            raise
        finally:
            out_t.cancel()
            in_t.cancel()
            try:
                proc.close()
            except Exception:
                pass
            async with session_scope() as s:
                await shells_repo.set_status(s, shell_id, "closed")

    async def _prepare_source(self) -> None:
        """For a code-scan run, make the source available at /src in the backend:
        clone a public git repo, or rely on the read-only mount for a local folder."""
        if not self.source:
            await self._event("orchestrator", "steer", "no source configured for the code scan")
            return
        if not _safe_source(self.source):
            await self._event("orchestrator", "steer", "source path rejected (unsafe characters)")
            return
        if _is_source_url(self.source):
            await self._event("recon", "tool", f"cloning {self.source}")
            try:
                res = await self.backend.run(
                    f"rm -rf /src && git clone --depth 1 {self.source} /src && "
                    f"echo CLONED && (find /src -type f | wc -l) ",
                    on_output=lambda line: self._event("recon", "tool", line.rstrip()))
                ok = "CLONED" in (res.output or "")
                await self._event("recon", "steer",
                                  "source ready at /src" if ok else "clone may have failed; check output")
            except Exception as exc:
                await self._event("orchestrator", "steer", f"clone failed: {exc}")
        else:
            await self._event("recon", "steer", f"reviewing mounted source at /src ({self.source})")

    async def _seed_targets(self) -> None:
        """Seed the attack surface with the in-scope targets."""
        import urllib.parse
        for t in self.targets:
            host = urllib.parse.urlparse(t).hostname or t
            try:
                async with session_scope() as s:
                    if not await hosts_repo.exists(s, self.session_id, host):
                        await hosts_repo.create(s, {"session_id": self.session_id, "host": host,
                                                    "tech": [], "ports": [], "source": "target"})
            except Exception:
                pass

    async def _complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        """LLM call that books token/cost usage onto the run."""
        out = await self.llm.complete(messages, tools=tools)
        tok = int(out.get("usage_tokens") or 0)
        cost = float(out.get("cost") or 0.0)
        if tok or cost:
            async with session_scope() as s:
                await runs_repo.set_meters(s, self.run_id, tok, cost, 0)
        return out

    async def _status(self, text: str) -> None:
        await self._event("orchestrator", "steer", text)

    async def _shell_out(self, shell_id: str, line: str) -> None:
        await self.bus.publish(shell_channel(shell_id), line)

    async def _event(self, source: str, typ: str, text: str) -> None:
        from .. import events as events_bus
        await events_bus.emit(self.bus, self.run_id, source, typ, text)

    @staticmethod
    def _assistant_msg(msg: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {"role": "assistant", "content": msg.get("content") or ""}
        if msg.get("tool_calls"):
            out["tool_calls"] = [
                {"id": tc["id"], "type": "function",
                 "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                for tc in msg["tool_calls"]
            ]
        return out


def _parse_args(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {}
