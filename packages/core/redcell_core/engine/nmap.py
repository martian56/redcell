"""Build a safe nmap command and parse its XML output into structured hosts.
Pure and unit-testable; the runner runs the command in the container and records
the parsed hosts onto the attack surface."""

from __future__ import annotations

import shlex
import xml.etree.ElementTree as ET
from typing import Any


def build_nmap_command(target: str, ports: str | None = None,
                       service_detection: bool = False, scripts: bool = False,
                       connect_scan: bool = False) -> str:
    """`nmap -oX -` (XML to stdout) with a curated, shell-quoted flag set. Every
    argument is quoted so a garbled or hostile target cannot inject shell.

    connect_scan forces a TCP connect scan (-sT), required when the scan is
    tunneled through a SOCKS proxy (proxychains), which cannot carry raw SYN
    packets."""
    parts = ["nmap", "-oX", "-", "-T4", "-Pn", "--max-retries", "2", "--host-timeout", "10m"]
    if connect_scan:
        parts.append("-sT")
    if service_detection:
        parts.append("-sV")
    if scripts:
        parts.append("-sC")
    if ports:
        parts += ["-p", ports]
    parts.append(target)
    return " ".join(shlex.quote(p) for p in parts)


def parse_nmap_xml(xml: str) -> list[dict[str, Any]]:
    """Return up hosts with their open ports/services from nmap -oX output."""
    hosts: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return hosts
    for host in root.findall("host"):
        status = host.find("status")
        if status is not None and status.get("state") == "down":
            continue
        addr = ""
        for a in host.findall("address"):
            if a.get("addrtype") in ("ipv4", "ipv6"):
                addr = a.get("addr", "")
                break
        hostnames = [hn.get("name", "") for hn in host.findall("./hostnames/hostname") if hn.get("name")]
        ports: list[dict[str, Any]] = []
        for p in host.findall("./ports/port"):
            st = p.find("state")
            if st is None or st.get("state") not in ("open", "open|filtered"):
                continue
            svc = p.find("service")
            service = svc.get("name", "") if svc is not None else ""
            product = svc.get("product", "") if svc is not None else ""
            version = svc.get("version", "") if svc is not None else ""
            ver = " ".join(x for x in (product, version) if x)
            ports.append({
                "port": int(p.get("portid", 0) or 0),
                "protocol": p.get("protocol", "tcp"),
                "service": service,
                "version": ver,
            })
        if addr or hostnames or ports:
            hosts.append({"ip": addr, "hostnames": hostnames, "ports": ports})
    return hosts
