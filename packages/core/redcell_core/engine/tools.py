"""Tool schemas exposed to the models (OpenAI function-calling shape; LiteLLM
passes them through to every provider)."""

from __future__ import annotations

ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "delegate",
            "description": "Assign an objective to a specialised executor agent (recon, web-exploit, auth-tester, idor-hunter, etc.). Returns immediately: the executor runs in the background and its report arrives as a later '[Executor ... finished]' message. You may delegate several at once (up to the concurrency limit) and keep planning meanwhile.",
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
            "name": "set_phase",
            "description": "Update the engagement phase shown on the operator's console. Phases only move forward (Reconnaissance -> Exploitation -> Post-Exploitation -> Reporting); call it as the engagement progresses, e.g. mark Exploitation once you start attacking a confirmed weakness.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phase": {"type": "string",
                              "enum": ["Reconnaissance", "Exploitation", "Post-Exploitation", "Reporting"]},
                },
                "required": ["phase"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "await_executors",
            "description": "Block until every running executor has finished and return their reports. Use when you have nothing to do until results come back.",
            "parameters": {"type": "object", "properties": {}},
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
            "name": "record_entity",
            "description": (
                "Record an OSINT intel entity and its relationships. Use for subjects that are not hosts: "
                "a person, email, username, org, social profile, phone, or a breach/paste the subject "
                "appears in. Set 'type' (person|email|username|org|profile|breach|phone|domain|other), "
                "'value' (the identifier, e.g. the email address or handle), an optional human 'label', and "
                "'source' (where it came from). To link entities, set 'relatedTo' to the value of an "
                "already-recorded entity and 'relation' to how they relate (e.g. 'owns', 'member of', "
                "'exposed in'), so the Intel panel shows the graph."),
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": [
                        "person", "email", "username", "org", "profile", "breach", "phone", "domain", "other"]},
                    "value": {"type": "string"},
                    "label": {"type": "string"},
                    "source": {"type": "string"},
                    "relatedTo": {"type": "string", "description": "value of an existing entity to link to"},
                    "relation": {"type": "string", "description": "how they relate, e.g. owns / member of / exposed in"},
                },
                "required": ["type", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_listener",
            "description": "Start a TCP listener on the operator host to catch a reverse shell. Returns the address the payload must call back to. Call this BEFORE triggering a reverse-shell payload. When an ngrok token is configured the callback is a public ngrok address, so targets can reach it with no open ports on the server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "Port to listen on. Must be in the configured reachable callback range unless a remote VPS execution host is in use."},
                    "method": {"type": "string", "enum": ["auto", "ngrok", "direct"], "description": "How the target reaches the listener. 'auto' (default) uses ngrok when a token is configured, else a direct port. 'ngrok' forces a tunnel; 'direct' forces the server port."},
                },
                "required": ["port"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shell_exec",
            "description": "Run a shell command on a caught reverse shell (the compromised foothold) and return its output. Use this for post-exploitation: enumerate the box (id, uname -a, sudo -l, SUID binaries, /etc/passwd), read files, hunt for credentials and keys, and set up deeper access. Pass the reverse shell's id (from the Terminals panel or the caught-shell event).",
            "parameters": {
                "type": "object",
                "properties": {
                    "shellId": {"type": "string", "description": "Id of the caught reverse shell to run the command on."},
                    "command": {"type": "string", "description": "The shell command to run on the foothold."},
                    "timeout": {"type": "integer", "description": "Seconds to wait for output (default 30, max 300)."},
                },
                "required": ["shellId", "command"],
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
            "name": "shell_exec",
            "description": "Run a shell command ON a caught reverse shell (the compromised foothold), not in your own Kali container. Use for post-exploitation on the box you compromised: enumerate (id, uname -a, sudo -l, SUID, /etc/passwd), read files, hunt credentials/keys, escalate. Pass the reverse shell's id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "shellId": {"type": "string", "description": "Id of the caught reverse shell to run the command on."},
                    "command": {"type": "string", "description": "The shell command to run on the foothold."},
                    "timeout": {"type": "integer", "description": "Seconds to wait for output (default 30, max 300)."},
                },
                "required": ["shellId", "command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mobile",
            "description": (
                "Drive the running Android device for DYNAMIC analysis via ADB and Frida. Only works in a "
                "mobile session with a device host attached (otherwise the review is static-only). Actions: "
                "'install' (install the session's uploaded APK from /root/assessment), 'packages' (list "
                "installed third-party apps), 'launch' (start an app by package), 'shell' (run an adb shell "
                "command given in 'command', e.g. 'run-as pkg cat databases/x'), 'screencap' (capture the "
                "screen and store it as evidence), 'input' (UI input via 'command', e.g. 'tap 200 400', "
                "'text hello', 'key KEYCODE_HOME'), 'pull' (base64 a device file at 'command'), 'frida_setup' "
                "(push and start a matching frida-server, required once before frida), 'frida_ps' (list device "
                "processes), 'frida_run' (run the Frida JS in 'script' against 'package'), 'ssl_unpin' (disable "
                "TLS certificate pinning for 'package' so you can observe its traffic)."),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": [
                        "install", "packages", "launch", "shell", "screencap", "input", "pull",
                        "frida_setup", "frida_ps", "frida_run", "ssl_unpin"]},
                    "package": {"type": "string", "description": "Target app package name (for launch/frida_run/ssl_unpin)."},
                    "command": {"type": "string", "description": "For shell/input/pull: the adb shell command, input args, or device file path."},
                    "script": {"type": "string", "description": "For frida_run: the Frida JavaScript hook to run."},
                    "timeout": {"type": "integer", "description": "Seconds to wait (default 30, max 300)."},
                },
                "required": ["action"],
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
