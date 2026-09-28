from __future__ import annotations
import base64, hashlib, html, json, re
from urllib.parse import parse_qs, unquote, urlsplit

SUPPORTED_PROTOCOLS = ("ss", "vmess", "vless", "trojan")
MAX_NODE_TEXT = 2 * 1024 * 1024
MAX_NODES = 2000

def _b64decode(value: str) -> bytes:
    s = "".join(str(value).strip().split()).replace("-", "+").replace("_", "/")
    s += "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(s, validate=False)

def _name(fragment: str, fallback: str) -> str:
    x = unquote(fragment or "").strip()
    x = "".join(c for c in x if ord(c) >= 32)[:120]
    return x or fallback

def _id(node: dict) -> str:
    stable = json.dumps({k: node[k] for k in sorted(node) if k not in ("name", "favorite", "history", "last_test")}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:20]

def _host_port(parts):
    if not parts.hostname or not parts.port:
        raise ValueError("NODE_HOST_PORT_REQUIRED")
    if not 1 <= int(parts.port) <= 65535:
        raise ValueError("NODE_PORT_INVALID")
    return parts.hostname, int(parts.port)

def _q(parts):
    return {k: v[-1] for k, v in parse_qs(parts.query, keep_blank_values=True).items()}

def _transport(q: dict) -> dict | None:
    typ = (q.get("type") or q.get("net") or "tcp").lower()
    if typ in ("tcp", "none", ""):
        return None
    if typ == "ws":
        out = {"type": "ws", "path": unquote(q.get("path", "/") or "/")}
        host = q.get("host")
        if host:
            out["headers"] = {"Host": host}
        return out
    if typ == "grpc":
        return {"type": "grpc", "service_name": unquote(q.get("serviceName") or q.get("service_name") or "")}
    if typ == "httpupgrade":
        out = {"type": "httpupgrade", "path": unquote(q.get("path", "/") or "/")}
        host = q.get("host")
        if host:
            out["host"] = [host]
        return out
    raise ValueError("NODE_TRANSPORT_UNSUPPORTED_" + typ.upper())

def _tls(q: dict, server: str) -> dict | None:
    security = (q.get("security") or "").lower()
    if security not in ("tls", "reality"):
        return None
    out = {"enabled": True, "server_name": q.get("sni") or q.get("servername") or server}
    insecure = str(q.get("allowInsecure") or q.get("insecure") or "").lower()
    if insecure in ("1", "true", "yes"):
        out["insecure"] = True
    alpn = [x for x in (q.get("alpn") or "").split(",") if x]
    if alpn:
        out["alpn"] = alpn
    fp = q.get("fp") or q.get("fingerprint")
    if fp:
        out["utls"] = {"enabled": True, "fingerprint": fp}
    if security == "reality":
        pbk = q.get("pbk") or q.get("publicKey") or q.get("public_key")
        if not pbk:
            raise ValueError("NODE_REALITY_PUBLIC_KEY_REQUIRED")
        out["reality"] = {"enabled": True, "public_key": pbk, "short_id": q.get("sid") or q.get("shortId") or q.get("short_id") or ""}
    return out

def parse_uri(uri: str) -> dict:
    raw = str(uri).strip()
    if len(raw) > 8192:
        raise ValueError("NODE_URI_TOO_LARGE")
    scheme = raw.split(":", 1)[0].lower() if ":" in raw else ""
    if scheme not in SUPPORTED_PROTOCOLS:
        raise ValueError("NODE_PROTOCOL_UNSUPPORTED")

    if scheme == "vmess":
        payload = raw.split("://", 1)[1].split("#", 1)[0]
        try:
            j = json.loads(_b64decode(payload).decode("utf-8-sig"))
        except Exception as e:
            raise ValueError("VMESS_DECODE_FAILED") from e
        server = str(j.get("add") or j.get("server") or "").strip()
        try:
            port = int(j.get("port"))
        except Exception as e:
            raise ValueError("NODE_PORT_INVALID") from e
        uid = str(j.get("id") or "").strip()
        if not server or not uid or not 1 <= port <= 65535:
            raise ValueError("VMESS_REQUIRED_FIELDS")
        q = {
            "type": str(j.get("net") or "tcp"),
            "host": str(j.get("host") or ""),
            "path": str(j.get("path") or ""),
            "sni": str(j.get("sni") or ""),
            "fp": str(j.get("fp") or ""),
            "security": str(j.get("tls") or ""),
            "alpn": str(j.get("alpn") or ""),
            "serviceName": str(j.get("serviceName") or ""),
        }
        node = {
            "protocol": "vmess", "name": str(j.get("ps") or f"VMess {server}"),
            "server": server, "port": port, "uuid": uid,
            "security": str(j.get("scy") or j.get("security") or "auto"),
            "alter_id": int(j.get("aid") or 0), "tls": _tls(q, server), "transport": _transport(q),
        }
    elif scheme == "ss":
        body = raw.split("://", 1)[1]
        main, _, frag = body.partition("#")
        main = main.split("?", 1)[0]
        if "@" in main:
            userinfo, endpoint = main.rsplit("@", 1)
            try:
                decoded = _b64decode(userinfo).decode("utf-8") if ":" not in unquote(userinfo) else unquote(userinfo)
            except Exception:
                decoded = unquote(userinfo)
        else:
            try:
                decoded_all = _b64decode(main).decode("utf-8")
            except Exception as e:
                raise ValueError("SS_DECODE_FAILED") from e
            if "@" not in decoded_all:
                raise ValueError("SS_ENDPOINT_REQUIRED")
            decoded, endpoint = decoded_all.rsplit("@", 1)
        if ":" not in decoded:
            raise ValueError("SS_CREDENTIALS_INVALID")
        method, password = decoded.split(":", 1)
        parts = urlsplit("ss://" + endpoint)
        server, port = _host_port(parts)
        node = {"protocol": "ss", "name": _name(frag, f"SS {server}"), "server": server, "port": port, "method": method, "password": password}
    else:
        parts = urlsplit(raw)
        server, port = _host_port(parts)
        q = _q(parts)
        user = unquote(parts.username or "").strip()
        if not user:
            raise ValueError("NODE_CREDENTIAL_REQUIRED")
        node = {
            "protocol": scheme, "name": _name(parts.fragment, f"{scheme.upper()} {server}"),
            "server": server, "port": port, "tls": _tls(q, server), "transport": _transport(q),
        }
        if scheme == "vless":
            node["uuid"] = user
            if q.get("flow"):
                node["flow"] = q["flow"]
            pe = q.get("packetEncoding") or q.get("packet_encoding")
            if pe:
                node["packet_encoding"] = pe
        else:
            node["password"] = user

    node["id"] = _id(node)
    node["raw"] = raw
    node["favorite"] = False
    node["pinned"] = False
    node["rating"] = 0
    node["tags"] = []
    node["note"] = ""
    node["source"] = "import"
    return node

_URI_RE = re.compile(r"(?i)(?:vmess|vless|trojan|ss)://[^\s<>\"']+")

def extract_uris(text: str) -> list[str]:
    s = html.unescape(str(text))
    if len(s.encode("utf-8", "ignore")) > MAX_NODE_TEXT:
        raise ValueError("NODE_INPUT_TOO_LARGE")
    direct = [x.rstrip("),.;]") for x in _URI_RE.findall(s)]
    if direct:
        return direct
    compact = "".join(s.split())
    try:
        decoded = _b64decode(compact).decode("utf-8-sig")
    except Exception:
        return []
    return [x.rstrip("),.;]") for x in _URI_RE.findall(decoded)]

def parse_blob(text: str, source: str = "import") -> dict:
    nodes, errors, seen = [], [], set()
    for raw in extract_uris(text):
        if len(nodes) >= MAX_NODES:
            break
        try:
            n = parse_uri(raw)
            if n["id"] in seen:
                continue
            seen.add(n["id"])
            n["source"] = source[:120]
            nodes.append(n)
        except ValueError as e:
            errors.append(str(e))
    return {"nodes": nodes, "errors": errors[:100], "found": len(nodes)}

def merge(existing: list[dict], incoming: list[dict]) -> list[dict]:
    by_id = {str(n.get("id")): dict(n) for n in existing if n.get("id")}
    for n in incoming:
        old = by_id.get(n["id"], {})
        x = dict(n)
        x["favorite"] = bool(old.get("favorite", x.get("favorite", False)))
        x["pinned"] = bool(old.get("pinned", x.get("pinned", False)))
        x["rating"] = int(old.get("rating", x.get("rating", 0)) or 0)
        x["tags"] = list(old.get("tags", x.get("tags", [])) or [])[:16]
        x["note"] = str(old.get("note", x.get("note", "")) or "")[:500]
        if old.get("last_test"):
            x["last_test"] = old["last_test"]
        if old.get("endpoint_test"):
            x["endpoint_test"] = old["endpoint_test"]
        by_id[n["id"]] = x
    return list(by_id.values())[:MAX_NODES]

def public_node(node: dict) -> dict:
    last = node.get("last_test") if isinstance(node.get("last_test"), dict) else None
    return {
        "id": node.get("id"), "name": node.get("name"), "protocol": node.get("protocol"),
        "server": node.get("server"), "port": node.get("port"), "favorite": bool(node.get("favorite")),
        "pinned": bool(node.get("pinned")), "rating": int(node.get("rating", 0) or 0),
        "tags": list(node.get("tags", []) or [])[:16], "note": str(node.get("note", "") or "")[:500],
        "source": node.get("source", ""), "last_test": last,
        "endpoint_test": node.get("endpoint_test") if isinstance(node.get("endpoint_test"), dict) else None,
    }

def _outbound(node: dict) -> dict:
    proto = node["protocol"]
    base = {"type": {"ss": "shadowsocks"}.get(proto, proto), "tag": "provider", "server": node["server"], "server_port": int(node["port"])}
    if proto == "ss":
        base.update(method=node["method"], password=node["password"])
    elif proto == "vmess":
        base.update(uuid=node["uuid"], security=node.get("security", "auto"), alter_id=int(node.get("alter_id", 0)))
    elif proto == "vless":
        base.update(uuid=node["uuid"])
        if node.get("flow"):
            base["flow"] = node["flow"]
        if node.get("packet_encoding"):
            base["packet_encoding"] = node["packet_encoding"]
    elif proto == "trojan":
        base["password"] = node["password"]
    else:
        raise ValueError("NODE_PROTOCOL_UNSUPPORTED")
    if node.get("tls"):
        base["tls"] = node["tls"]
    if node.get("transport"):
        base["transport"] = node["transport"]
    return base

def sing_box_config(node: dict, listen_port: int = 19460) -> dict:
    if not 1024 <= int(listen_port) <= 65535:
        raise ValueError("NODE_LISTEN_PORT_INVALID")
    return {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": [{"type": "socks", "tag": "node-in", "listen": "127.0.0.1", "listen_port": int(listen_port)}],
        "outbounds": [_outbound(node), {"type": "direct", "tag": "direct"}],
        "route": {"final": "provider", "auto_detect_interface": True},
    }
