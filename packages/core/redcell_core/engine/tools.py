"""Tool schemas exposed to the models (OpenAI function-calling shape; LiteLLM
passes them through to every provider)."""

from __future__ import annotations

ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "delegate",
            "description": "Assign an objective to a specialised executor agent (recon, web-exploit, auth-tester, idor-hunter, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "description": "Executor name, e.g. 'web-exploit'."},
                    "objective": {"type": "string", "description": "What the executor should achieve."},
                },
                "required": ["agent", "objective"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_finding",
            "description": "Record a confirmed or candidate vulnerability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                    "cvss": {"type": "number", "description": "CVSS 3.1 base score 0-10 (e.g. 9.8 for an unauthenticated RCE/SQLi, 6.1 reflected XSS). Set it so the operator sees a real score."},
                    "location": {"type": "string"},
                    "cwe": {"type": "string"},
                    "status": {"type": "string", "enum": ["candidate", "verified"]},
                    "remediation": {"type": "string"},
                },
                "required": ["title", "severity", "location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_loot",
            "description": "Record collected loot: a credential, hash, token/key, or a file the agents obtained. Populates the Loot & Creds panel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["credential", "hash", "token", "key", "file", "other"]},
                    "label": {"type": "string", "description": "What it is, e.g. 'admin@juice-sh.op' or 'JWT (admin)'."},
                    "value": {"type": "string", "description": "The value, or a short description for files."},
                    "source": {"type": "string", "description": "Where it came from, e.g. an endpoint or dump."},
                },
                "required": ["kind", "label"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_host",
            "description": "Record a discovered host/service in the attack surface (subdomains, IPs, endpoints, open ports, detected tech).",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "ip": {"type": "string"},
                    "ports": {"type": "array", "items": {
                        "type": "object",
                        "properties": {"port": {"type": "integer"}, "service": {"type": "string"}, "version": {"type": "string"}},
                    }},
                    "tech": {"type": "array", "items": {"type": "string"}},
                    "source": {"type": "string"},
                },
                "required": ["host"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_listener",
            "description": "Start a TCP listener on the operator host to catch a reverse shell. Returns the address the payload must call back to. Call this BEFORE triggering a reverse-shell payload.",
            "parameters": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "Port to listen on (e.g. 4444)."},
                },
                "required": ["port"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_pivot",
            "description": "Route tool traffic through a caught reverse shell so hosts only reachable from the compromised machine become scannable. Pass the reverse shell's id (from the Terminals panel / the caught-shell event). After this succeeds, delegate executors to scan or reach the internal network; record discovered internal hosts with record_host (source 'pivot').",
            "parameters": {
                "type": "object",
                "properties": {
                    "shellId": {"type": "string", "description": "Id of the caught reverse shell to pivot through."},
                },
                "required": ["shellId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_pivot",
            "description": "Tear down the active network pivot and route tool traffic directly again.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_operator",
            "description": "Pause and ask the human operator a question before a sensitive or scope-affecting action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Conclude the run with a short summary of what was achieved.",
            "parameters": {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            },
        },
    },
]

EXECUTOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command in the engagement's execution environment (Kali container or ops VPS).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "rationale": {"type": "string", "description": "One line: why run this."},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report",
            "description": "Report the executor's result back to the orchestrator, optionally with a finding.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "finding": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                            "cvss": {"type": "number", "description": "CVSS 3.1 base score 0-10."},
                            "location": {"type": "string"},
                            "cwe": {"type": "string"},
                        },
                    },
                },
                "required": ["summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_open",
            "description": "Open a URL in a real browser. Use the browser (not curl) for JS-rendered apps and SPAs, login and multi-step flows, and client-side bugs where raw HTTP cannot see the page.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "Click the first element matching a CSS selector in the open browser page.",
            "parameters": {
                "type": "object",
                "properties": {"selector": {"type": "string", "description": "CSS selector."}},
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_type",
            "description": "Type text into the element matching a CSS selector. Set submit to press Enter after (useful for search boxes and logins).",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector."},
                    "text": {"type": "string"},
                    "submit": {"type": "boolean"},
                },
                "required": ["selector", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_read",
            "description": "Read the current page: visible text plus notable links and input fields. Use it to see what rendered after navigation or a click.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_screenshot",
            "description": "Capture a screenshot of the current page as evidence.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "nmap_scan",
            "description": "Port/service scan with nmap. Results are parsed and recorded onto the Attack Surface automatically; you get a concise summary, not raw text. Prefer this over running nmap via run_command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Host, IP, hostname, or CIDR."},
                    "ports": {"type": "string", "description": "Port spec, e.g. '80,443,8080' or '1-1000'. Optional."},
                    "service_detection": {"type": "boolean", "description": "Detect service versions (-sV)."},
                    "scripts": {"type": "boolean", "description": "Run default NSE scripts (-sC)."},
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "nuclei_scan",
            "description": "Run nuclei templates against a URL. Matches are recorded as findings (with CVSS where nuclei provides it). Returns a summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "URL to scan, e.g. https://app.example.com."},
                    "severity": {"type": "string", "description": "Optional filter, e.g. 'critical,high,medium'."},
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_discover",
            "description": "Directory or vhost discovery with ffuf. Returns the discovered paths (or vhosts) with status codes, structured. Record notable exposures with report/record_finding yourself.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Base URL, e.g. https://app.example.com."},
                    "mode": {"type": "string", "enum": ["dir", "vhost"], "description": "Directory brute force or virtual-host discovery. Default dir."},
                    "wordlist": {"type": "string", "description": "Optional wordlist path in the container."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "msf_search",
            "description": "Search Metasploit modules by keyword. Returns matching module paths.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "e.g. 'apache struts' or a CVE id."}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "msf_run",
            "description": "Run a Metasploit module with options and return its output. Use msf_search first to find the exact module path. Set RHOSTS and other options via options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "module": {"type": "string", "description": "Full module path, e.g. auxiliary/scanner/http/http_version."},
                    "options": {"type": "object", "description": "Module options, e.g. {\"RHOSTS\": \"10.0.0.5\", \"RPORT\": \"8080\"}."},
                },
                "required": ["module"],
            },
        },
    },
]


def orchestrator_system(goal: str, scope: list[str], targets: list[str], roe: str | None) -> str:
    return (
        "You are the orchestrator of an authorized red-team engagement. You plan and "
        "delegate; executors do the hands-on work. Stay strictly within scope, honor the "
        "rules of engagement, and ask the operator before any destructive or scope-expanding "
        "action.\n\n"
        f"Objective: {goal}\n"
        f"Scope: {', '.join(scope) or 'unspecified'}\n"
        f"Targets: {', '.join(targets) or 'unspecified'}\n"
        f"Rules of engagement: {roe or 'standard, no DoS, no data destruction'}\n\n"
        "Work in small steps. Delegate one objective at a time. As you go, record every "
        "confirmed vulnerability with record_finding (always include a realistic cvss score 0-10), "
        "every credential/hash/token/file you obtain with record_loot, and every host/endpoint/service "
        "you discover with record_host. These populate the operator's Findings, Loot, and Attack "
        "Surface panels.\n\n"
        "To catch a reverse shell after finding command execution: FIRST call start_listener with a "
        "port; it returns the exact callback address (host:port) the payload must dial back to. "
        "Use that address verbatim in your reverse-shell one-liner (do NOT hardcode 127.0.0.1). "
        "Then delegate an executor to trigger the payload via the vulnerability. The caught shell "
        "appears in the operator's Terminals panel.\n\n"
        "To reach an internal network only visible from a compromised machine, call open_pivot with "
        "the caught reverse shell's id. That tunnels tool traffic through the foothold; then delegate "
        "executors to scan or reach the internal hosts (nmap_scan is routed through the pivot "
        "automatically) and record what you find with record_host (source 'pivot'). Internal hosts "
        "still need to be in scope. Call close_pivot when the internal work is done.\n\n"
        "The operator may send you steering directives at any time (they appear as '[Operator steer]' "
        "messages); follow them. Call finish when the objective is met or no safe progress remains.\n\n"
        "Write any prose in plain text. Do not use em-dashes; use commas, periods, or parentheses instead."
    )


def executor_system(name: str, objective: str) -> str:
    return (
        f"You are the '{name}' executor on an authorized red-team engagement. Achieve this "
        f"objective using shell tools: {objective}\n"
        "Prefer the structured tools when they fit: nmap_scan for port/service discovery (it records the "
        "attack surface for you), nuclei_scan for template-based vulns (records findings with CVSS), "
        "web_discover for directory/vhost brute forcing, and msf_search then msf_run for Metasploit "
        "modules. Use run_command for anything else.\n"
        "Run one command at a time, read the output, and adapt. Do not run destructive or "
        "out-of-scope commands. When done, call report with a concise summary and any finding."
    )


def codescan_orchestrator_system(goal: str, source: str) -> str:
    return (
        "You are the lead of an AUTHORIZED source-code security review (SAST). The code under review is "
        "checked out at /src in your execution environment. You plan and delegate; executor agents read "
        "files and run analysis tools there.\n\n"
        f"Objective: {goal}\n"
        f"Source: {source or '/src'}\n\n"
        "Delegate focused review objectives one at a time (map the tech stack and entry points first, then "
        "review by vulnerability class). Look for: injection (SQL/command/template/NoSQL), broken "
        "authentication and authorization, IDOR, SSRF, path traversal, insecure deserialization, hardcoded "
        "secrets/keys/tokens, weak or misused crypto, XSS, CSRF, unsafe file uploads, SSTI, and risky "
        "dependencies. For every real issue call record_finding with a PRECISE location (file path and line, "
        "e.g. src/api/users.py:214), a severity, a realistic cvss score (0-10), the CWE, and a concrete "
        "remediation. Record any secret/key you find with record_loot. This is a read-only review: never "
        "modify, delete, or exfiltrate the code. The operator may steer you with '[Operator steer]' messages; "
        "follow them. Call finish when the review is complete.\n\n"
        "Write any prose in plain text. Do not use em-dashes; use commas, periods, or parentheses instead."
    )


def codescan_executor_system(name: str, objective: str) -> str:
    return (
        f"You are the '{name}' code-review executor. The source tree is at /src. Objective: {objective}\n"
        "Use run_command to explore and read code READ-ONLY: 'rg -n <pattern> /src' (or grep -rn), "
        "'sed -n <a,b>p <file>', 'cat', 'find /src -name ...', 'ls', and 'semgrep --config auto /src' if it "
        "is installed. Never modify files. Read enough surrounding code to confirm a real issue before "
        "reporting. When done, call report with a concise summary and, for any confirmed vulnerability, a "
        "finding with a precise file:line location, severity, and cvss."
    )
