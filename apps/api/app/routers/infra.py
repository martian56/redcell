"""Dashboard infrastructure: servers and proxies."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from redcell_core.keys import normalize_private_key
from redcell_core.probe import probe_proxy, probe_server
from redcell_core.repositories import ids
from redcell_core.repositories import proxies as proxies_repo
from redcell_core.repositories import servers as servers_repo
from redcell_core.schemas import (
    CreateProxyInput,
    CreateServerInput,
    Proxy,
    ProxyTestResult,
    Server,
    ServerTestResult,
    UpdateProxyInput,
    UpdateServerInput,
)
from redcell_core.security import current_user
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import ListParams, db, list_params

router = APIRouter(tags=["infra"], dependencies=[Depends(current_user)])


# ---- servers ----
@router.get("/servers", response_model=list[Server])
async def list_servers(s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                       status: str | None = Query(None)) -> list[Server]:
    rows = await servers_repo.list_all(s, status=status, q=p.q, limit=p.limit, offset=p.offset)
    return [Server.model_validate(x) for x in rows]


@router.get("/servers/{sid}", response_model=Server)
async def get_server(sid: str, s: AsyncSession = Depends(db)) -> Server:
    row = await servers_repo.get(s, sid)
    if row is None:
        raise HTTPException(404, "server not found")
    return Server.model_validate(row)


@router.post("/servers", response_model=Server)
async def create_server(body: CreateServerInput, s: AsyncSession = Depends(db)) -> Server:
    secret = normalize_private_key(body.private_key) or body.password
    row = await servers_repo.create(s, {"name": body.name, "host": body.host, "username": body.username,
                                        "region": body.region, "status": "unchecked"}, secret_plain=secret)
    return Server.model_validate(row)


@router.patch("/servers/{sid}", response_model=Server)
async def update_server(sid: str, body: UpdateServerInput, s: AsyncSession = Depends(db)) -> Server:
    data = {k: v for k, v in {"name": body.name, "host": body.host, "username": body.username,
                              "region": body.region}.items() if v is not None}
    secret = normalize_private_key(body.private_key) or body.password
    if secret or data:
        data["status"] = "unchecked"  # config changed; re-test to confirm
    row = await servers_repo.update(s, sid, data, secret_plain=secret)
    if row is None:
        raise HTTPException(404, "server not found")
    return Server.model_validate(row)


@router.post("/servers/{sid}/test", response_model=ServerTestResult)
async def test_server(sid: str, s: AsyncSession = Depends(db)) -> ServerTestResult:
    row = await servers_repo.get(s, sid)
    if row is None:
        raise HTTPException(404, "server not found")
    secret = await servers_repo.get_secret(s, sid)
    result = await probe_server(row.host, row.username, secret)
    ok = bool(result.get("ok"))
    facts = {
        "status": "connected" if ok else "error",
        "last_check": ids.now_iso(),
        "latency_ms": result.get("latency_ms"),
        "last_error": None if ok else (result.get("error") or "connection failed"),
    }
    for key in ("os", "cpu", "ram_gb", "ip"):
        if result.get(key) is not None:
            facts[key] = result[key]
    await servers_repo.update(s, sid, facts)
    return ServerTestResult(
        ok=ok, status=facts["status"], latency_ms=result.get("latency_ms"),
        hostname=result.get("hostname"), os=result.get("os"), cpu=result.get("cpu"),
        ram_gb=result.get("ram_gb"), ip=result.get("ip"),
        output=result.get("output", ""), error=None if ok else facts["last_error"],
    )


@router.delete("/servers/{sid}", status_code=204)
async def remove_server(sid: str, s: AsyncSession = Depends(db)) -> None:
    if not await servers_repo.delete(s, sid):
        raise HTTPException(404, "server not found")


# ---- proxies ----
def _proxy_url(proxy, secret: str | None) -> str:
    url = (proxy.url or "").strip()
    # derive the scheme from the kind when only host:port is given
    if "://" not in url:
        scheme = "socks5" if proxy.kind == "socks5" else "http"
        url = f"{scheme}://{url}"
    if proxy.username and secret and "@" not in url.split("://", 1)[1]:
        scheme, rest = url.split("://", 1)
        return f"{scheme}://{proxy.username}:{secret}@{rest}"
    return url


@router.get("/proxies", response_model=list[Proxy])
async def list_proxies(s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                       kind: str | None = Query(None), status: str | None = Query(None)) -> list[Proxy]:
    rows = await proxies_repo.list_all(s, kind=kind, status=status, q=p.q, limit=p.limit, offset=p.offset)
    return [Proxy.model_validate(x) for x in rows]


@router.get("/proxies/{pid}", response_model=Proxy)
async def get_proxy(pid: str, s: AsyncSession = Depends(db)) -> Proxy:
    row = await proxies_repo.get(s, pid)
    if row is None:
        raise HTTPException(404, "proxy not found")
    return Proxy.model_validate(row)


@router.post("/proxies", response_model=Proxy)
async def create_proxy(body: CreateProxyInput, s: AsyncSession = Depends(db)) -> Proxy:
    row = await proxies_repo.create(s, {"label": body.label, "url": body.url, "kind": body.kind,
                                        "auth": body.auth, "username": body.username, "status": "unchecked"},
                                    secret_plain=body.password)
    return Proxy.model_validate(row)


@router.patch("/proxies/{pid}", response_model=Proxy)
async def update_proxy(pid: str, body: UpdateProxyInput, s: AsyncSession = Depends(db)) -> Proxy:
    data = {k: v for k, v in {"label": body.label, "url": body.url, "kind": body.kind,
                              "auth": body.auth, "username": body.username}.items() if v is not None}
    if data or body.password:
        data["status"] = "unchecked"
    row = await proxies_repo.update(s, pid, data, secret_plain=body.password)
    if row is None:
        raise HTTPException(404, "proxy not found")
    return Proxy.model_validate(row)


@router.post("/proxies/{pid}/test", response_model=ProxyTestResult)
async def test_proxy(pid: str, s: AsyncSession = Depends(db)) -> ProxyTestResult:
    row = await proxies_repo.get(s, pid)
    if row is None:
        raise HTTPException(404, "proxy not found")
    secret = await proxies_repo.get_secret(s, pid)
    result = await probe_proxy(_proxy_url(row, secret))
    ok = bool(result.get("ok"))
    await proxies_repo.update(s, pid, {
        "status": "healthy" if ok else "dead",
        "last_check": ids.now_iso(),
        "latency_ms": result.get("latency_ms"),
        "egress_ip": result.get("egress_ip"),
        "last_error": None if ok else (result.get("error") or "proxy check failed"),
    })
    return ProxyTestResult(
        ok=ok, status="healthy" if ok else "dead", latency_ms=result.get("latency_ms"),
        egress_ip=result.get("egress_ip"), output=result.get("output", ""),
        error=None if ok else (result.get("error") or "proxy check failed"),
    )


@router.delete("/proxies/{pid}", status_code=204)
async def remove_proxy(pid: str, s: AsyncSession = Depends(db)) -> None:
    if not await proxies_repo.delete(s, pid):
        raise HTTPException(404, "proxy not found")
