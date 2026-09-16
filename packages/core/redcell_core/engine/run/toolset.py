"""Structured toolset integrations (nmap, nuclei, ffuf, metasploit) mixed into
LiveRunner. Each parses tool output into recorded hosts/findings and returns a
compact summary instead of raw text."""

from __future__ import annotations

from typing import Any

from .. import msf, nmap, pivot, webscan


class ToolsetMixin:
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
        if (blocked := await self._scope_block(target)):
            return blocked
        pivoting = self._pivot is not None and self._pivot.active
        cmd = nmap.build_nmap_command(target, ports=args.get("ports"),
                                      service_detection=bool(args.get("service_detection")),
                                      scripts=bool(args.get("scripts")),
                                      connect_scan=pivoting)
        # Through a pivot, tunnel the connect scan over the SOCKS proxy so internal
        # hosts are reachable; discovered hosts are tagged as pivot-sourced.
        cmd = pivot.proxychains_wrap(cmd, pivoting)
        res = await self._exec(cmd)
        if self._was_interrupted(res):
            return {"interrupted": True}
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
        if (blocked := await self._scope_block(target)):
            return blocked
        cmd = webscan.build_nuclei_command(target, severity=args.get("severity"))
        res = await self._exec(cmd)
        if self._was_interrupted(res):
            return {"interrupted": True}
        findings = webscan.parse_nuclei_jsonl(getattr(res, "output", "") or "", target=target)
        for f in findings:
            await self._record_finding(f)
        return {"ok": True, "findings": len(findings), "titles": [f["title"] for f in findings[:20]]}

    async def _run_web_discover(self, args: dict[str, Any]) -> dict[str, Any]:
        url = str(args.get("url", "")).strip()
        if not url:
            return {"error": "url required"}
        if (blocked := await self._scope_block(url)):
            return blocked
        cmd = webscan.build_ffuf_command(url, wordlist=args.get("wordlist"),
                                         vhost=(args.get("mode") == "vhost"))
        res = await self._exec(cmd)
        if self._was_interrupted(res):
            return {"interrupted": True}
        results = webscan.parse_ffuf_json(getattr(res, "output", "") or "")
        return {"ok": True, "found": len(results), "results": results[:50]}

    async def _run_msf_search(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query", "")).strip()
        if not query:
            return {"error": "query required"}
        res = await self._exec(msf.build_msf_search(query))
        if self._was_interrupted(res):
            return {"interrupted": True}
        modules = msf.parse_msf_search(getattr(res, "output", "") or "")
        return {"ok": True, "count": len(modules), "modules": modules[:40]}

    async def _run_msf_run(self, args: dict[str, Any]) -> dict[str, Any]:
        module = str(args.get("module", "")).strip()
        if not msf.valid_module(module):
            return {"error": "invalid module path"}
        options = args.get("options") if isinstance(args.get("options"), dict) else {}
        rhosts = options.get("RHOSTS") or options.get("RHOST") or options.get("rhosts")
        if rhosts:
            for tok in str(rhosts).replace(",", " ").split():
                if (blocked := await self._scope_block(tok)):
                    return blocked
        cmd = msf.build_msf_run(module, {str(k): str(v) for k, v in options.items()})
        res = await self._exec(cmd)
        if self._was_interrupted(res):
            return {"interrupted": True}
        return {"ok": True, "output": (getattr(res, "output", "") or "")[-3000:]}
