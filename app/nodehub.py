from __future__ import annotations
import base64, hashlib, html, json, re
from urllib.parse import parse_qs, parse_qsl, urlencode, unquote, urlsplit

SUPPORTED_PROTOCOLS = ("ss", "vmess", "vless", "trojan", "hysteria2", "hy2", "tuic", "anytls")
JSON_ONLY_PROTOCOLS = ("shadowtls",)
UDP_PREFLIGHT_PROTOCOLS = ("hysteria2", "tuic")
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

def _truthy(value) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")

def _required_tls(q: dict, server: str) -> dict:
    qq = dict(q)
    qq["security"] = "tls"
    return _tls(qq, server, default_enabled=True)

def _json_tls(value, server: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError("NODE_JSON_TLS_REQUIRED")
    if value.get("enabled") is False:
        raise ValueError("NODE_JSON_TLS_REQUIRED")
    out = {"enabled": True, "server_name": str(value.get("server_name") or server)}
    if value.get("insecure") is True:
        out["insecure"] = True
    alpn = value.get("alpn")
    if isinstance(alpn, list):
        clean = [str(x) for x in alpn if str(x).strip()][:8]
        if clean:
            out["alpn"] = clean
    utls = value.get("utls")
    if isinstance(utls, dict) and utls.get("enabled") is True:
        fp = str(utls.get("fingerprint") or "").strip()
        if fp:
            out["utls"] = {"enabled": True, "fingerprint": fp[:64]}
    return out

def _transport(q: dict) -> dict | None:
    typ = (q.get("type") or q.get("net") or "").lower()
    legacy_ws = str(q.get("ws") or "").lower() in ("1", "true", "yes") or bool(q.get("wspath"))
    if not typ:
        typ = "ws" if legacy_ws else "tcp"
    if typ in ("tcp", "none", ""):
        header = str(q.get("headerType") or q.get("headertype") or "").lower()
        if header == "http":
            typ = "http"
        else:
            return None
    if typ == "ws":
        path = unquote(q.get("path") or q.get("wspath") or "/")
        ed = str(q.get("ed") or "").strip()
        eh = unquote(str(q.get("eh") or "")).strip()
        if "?" in path:
            base, query = path.split("?", 1)
            pairs = parse_qsl(query, keep_blank_values=True)
            kept = []
            for k, v in pairs:
                if k == "ed" and not ed:
                    ed = v
                else:
                    kept.append((k, v))
            path = base + (("?" + urlencode(kept)) if kept else "")
        out = {"type": "ws", "path": path or "/"}
        host = q.get("host")
        if host:
            out["headers"] = {"Host": host}
        if ed:
            try:
                early = int(ed)
            except ValueError as exc:
                raise ValueError("NODE_WS_EARLY_DATA_INVALID") from exc
            if not 1 <= early <= 8192:
                raise ValueError("NODE_WS_EARLY_DATA_INVALID")
            out["max_early_data"] = early
            header = eh or "Sec-WebSocket-Protocol"
            if len(header) > 128 or "\r" in header or "\n" in header:
                raise ValueError("NODE_WS_EARLY_HEADER_INVALID")
            out["early_data_header_name"] = header
        return out
    if typ in ("http", "h2"):
        out = {"type": "http", "path": unquote(q.get("path", "/") or "/")}
        hosts = [x.strip() for x in str(q.get("host") or "").split(",") if x.strip()]
        if hosts:
            out["host"] = hosts
        return out
    if typ == "grpc":
        return {"type": "grpc", "service_name": unquote(q.get("serviceName") or q.get("service_name") or "")}
    if typ == "httpupgrade":
        out = {"type": "httpupgrade", "path": unquote(q.get("path", "/") or "/")}
        host = q.get("host")
        if host:
            out["host"] = host
        return out
    if typ == "quic":
        return {"type": "quic"}
    raise ValueError("NODE_TRANSPORT_UNSUPPORTED_" + typ.upper())

def _tls(q: dict, server: str, default_enabled: bool = False) -> dict | None:
    security = (q.get("security") or "").lower()
    if security not in ("tls", "reality"):
        if default_enabled and not security:
            security = "tls"
        else:
            return None
    out = {"enabled": True, "server_name": q.get("sni") or q.get("servername") or q.get("serverName") or server}
    insecure = str(q.get("allowInsecure") or q.get("allowinsecure") or q.get("allow_insecure") or q.get("insecure") or "").lower()
    if insecure in ("1", "true", "yes"):
        out["insecure"] = True
    alpn = [x for x in (q.get("alpn") or "").split(",") if x]
    if alpn:
        out["alpn"] = alpn
    fp = q.get("fp") or q.get("fingerprint")
    if fp:
        out["utls"] = {"enabled": True, "fingerprint": fp}
    if security == "reality":
        pbk = q.get("pbk") or q.get("publicKey") or q.get("publickey") or q.get("public_key")
        if not pbk:
            raise ValueError("NODE_REALITY_PUBLIC_KEY_REQUIRED")
        out["reality"] = {"enabled": True, "public_key": pbk, "short_id": q.get("sid") or q.get("shortId") or q.get("shortid") or q.get("short_id") or ""}
    return out

def parse_uri(uri: str) -> dict:
    raw = str(uri).strip()
    if len(raw) > 8192:
        raise ValueError("NODE_URI_TOO_LARGE")
    scheme = raw.split(":", 1)[0].lower() if ":" in raw else ""
    if scheme not in SUPPORTED_PROTOCOLS:
        raise ValueError("NODE_PROTOCOL_UNSUPPORTED")
    if scheme == "hy2":
        scheme = "hysteria2"

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
    elif scheme == "tuic":
        parts = urlsplit(raw)
        server, port = _host_port(parts)
        q = _q(parts)
        uid = unquote(parts.username or "").strip()
        password = unquote(parts.password or "").strip()
        if not uid or not password:
            raise ValueError("TUIC_CREDENTIALS_REQUIRED")
        cc = str(q.get("congestion_control") or "cubic").lower()
        if cc not in ("cubic", "new_reno", "bbr"):
            raise ValueError("TUIC_CONGESTION_CONTROL_INVALID")
        relay = str(q.get("udp_relay_mode") or "native").lower()
        if relay not in ("native", "quic"):
            raise ValueError("TUIC_UDP_RELAY_MODE_INVALID")
        node = {
            "protocol": "tuic", "name": _name(parts.fragment, f"TUIC {server}"),
            "server": server, "port": port, "uuid": uid, "password": password,
            "congestion_control": cc, "udp_relay_mode": relay,
            "zero_rtt_handshake": _truthy(q.get("reduce_rtt") or q.get("zero_rtt_handshake")),
            "tls": _required_tls(q, server), "transport": None,
        }
    elif scheme == "anytls":
        parts = urlsplit(raw)
        if not parts.hostname:
            raise ValueError("NODE_HOST_PORT_REQUIRED")
        try:
            port = int(parts.port or 443)
        except ValueError as e:
            raise ValueError("NODE_PORT_INVALID") from e
        if not 1 <= port <= 65535:
            raise ValueError("NODE_PORT_INVALID")
        server = parts.hostname
        q = _q(parts)
        password = unquote(parts.username or "").strip()
        if not password:
            raise ValueError("ANYTLS_PASSWORD_REQUIRED")
        node = {
            "protocol": "anytls", "name": _name(parts.fragment, f"AnyTLS {server}"),
            "server": server, "port": port, "password": password,
            "tls": _required_tls(q, server), "transport": None,
        }
    else:
        parts = urlsplit(raw)
        server, port = _host_port(parts)
        q = _q(parts)
        user = unquote(parts.username or "").strip()
        if not user:
            raise ValueError("NODE_CREDENTIAL_REQUIRED")
        if scheme == "hysteria2":
            tls = {"enabled": True, "server_name": q.get("sni") or server}
            insecure = str(q.get("insecure") or q.get("allowInsecure") or "").lower()
            if insecure in ("1", "true", "yes"):
                tls["insecure"] = True
            node = {
                "protocol": "hysteria2", "name": _name(parts.fragment, f"Hysteria2 {server}"),
                "server": server, "port": port, "password": user, "tls": tls, "transport": None,
            }
            obfs = str(q.get("obfs") or "").strip().lower()
            obfs_password = str(q.get("obfs-password") or q.get("obfs_password") or "").strip()
            if obfs:
                if obfs not in ("salamander", "gecko"):
                    raise ValueError("HYSTERIA2_OBFS_UNSUPPORTED")
                if not obfs_password:
                    raise ValueError("HYSTERIA2_OBFS_PASSWORD_REQUIRED")
                node["obfs"] = {"type": obfs, "password": obfs_password}
        else:
            node = {
                "protocol": scheme, "name": _name(parts.fragment, f"{scheme.upper()} {server}"),
                "server": server, "port": port, "tls": _tls(q, server, default_enabled=(scheme == "trojan")), "transport": _transport(q),
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

_URI_RE = re.compile(r"(?i)(?:vmess|vless|trojan|ss|hysteria2|hy2|tuic|anytls)://[^\s<>\"']+")

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

def _singbox_json_node(outbound: dict) -> dict:
    if not isinstance(outbound, dict):
        raise ValueError("NODE_JSON_OUTBOUND_INVALID")
    typ = str(outbound.get("type") or "").lower()
    if typ not in ("tuic", "anytls", "shadowtls"):
        raise ValueError("NODE_JSON_PROTOCOL_UNSUPPORTED")
    if outbound.get("detour") or outbound.get("dialer_proxy"):
        raise ValueError("NODE_JSON_DETOUR_UNSUPPORTED")
    server = str(outbound.get("server") or "").strip()
    try:
        port = int(outbound.get("server_port"))
    except Exception as e:
        raise ValueError("NODE_PORT_INVALID") from e
    if not server or not 1 <= port <= 65535:
        raise ValueError("NODE_HOST_PORT_REQUIRED")
    node = {
        "protocol": typ,
        "name": str(outbound.get("tag") or f"{typ.upper()} {server}")[:120],
        "server": server,
        "port": port,
        "tls": _json_tls(outbound.get("tls"), server),
        "transport": None,
    }
    if typ == "tuic":
        uid = str(outbound.get("uuid") or "").strip()
        password = str(outbound.get("password") or "").strip()
        if not uid or not password:
            raise ValueError("TUIC_CREDENTIALS_REQUIRED")
        cc = str(outbound.get("congestion_control") or "cubic").lower()
        relay = str(outbound.get("udp_relay_mode") or "native").lower()
        if cc not in ("cubic", "new_reno", "bbr"):
            raise ValueError("TUIC_CONGESTION_CONTROL_INVALID")
        if relay not in ("native", "quic"):
            raise ValueError("TUIC_UDP_RELAY_MODE_INVALID")
        node.update(uuid=uid, password=password, congestion_control=cc, udp_relay_mode=relay,
                    zero_rtt_handshake=bool(outbound.get("zero_rtt_handshake", False)))
    elif typ == "anytls":
        password = str(outbound.get("password") or "").strip()
        if not password:
            raise ValueError("ANYTLS_PASSWORD_REQUIRED")
        node["password"] = password
        for key in ("idle_session_check_interval", "idle_session_timeout", "client_metadata"):
            if outbound.get(key) not in (None, ""):
                node[key] = str(outbound[key])[:512]
        if outbound.get("min_idle_session") is not None:
            try:
                node["min_idle_session"] = max(0, min(64, int(outbound["min_idle_session"])))
            except Exception as e:
                raise ValueError("ANYTLS_MIN_IDLE_SESSION_INVALID") from e
    else:
        try:
            version = int(outbound.get("version") or 1)
        except Exception as e:
            raise ValueError("SHADOWTLS_VERSION_INVALID") from e
        if version not in (1, 2, 3):
            raise ValueError("SHADOWTLS_VERSION_INVALID")
        password = str(outbound.get("password") or "").strip()
        if version in (2, 3) and not password:
            raise ValueError("SHADOWTLS_PASSWORD_REQUIRED")
        node["version"] = version
        if password:
            node["password"] = password
    node["id"] = _id(node)
    node["raw"] = json.dumps(outbound, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    node["favorite"] = False
    node["pinned"] = False
    node["rating"] = 0
    node["tags"] = []
    node["note"] = ""
    node["source"] = "import"
    return node

def _singbox_json_nodes(text: str) -> tuple[list[dict], list[str]]:
    candidates = [str(text)]
    compact = "".join(str(text).split())
    try:
        decoded = _b64decode(compact).decode("utf-8-sig")
        if decoded.lstrip().startswith(("{", "[")):
            candidates.append(decoded)
    except Exception:
        pass
    for raw in candidates:
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("outbounds"), list):
            rows = obj["outbounds"]
        elif isinstance(obj, dict) and obj.get("type"):
            rows = [obj]
        elif isinstance(obj, list):
            rows = obj
        else:
            return [], []
        nodes, errors = [], []
        for row in rows:
            if not isinstance(row, dict) or str(row.get("type") or "").lower() not in ("tuic", "anytls", "shadowtls"):
                continue
            try:
                nodes.append(_singbox_json_node(row))
            except ValueError as e:
                errors.append(str(e))
        return nodes, errors
    return [], []

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
    json_nodes, json_errors = _singbox_json_nodes(text)
    for n in json_nodes:
        if len(nodes) >= MAX_NODES:
            break
        if n["id"] in seen:
            continue
        seen.add(n["id"])
        n["source"] = source[:120]
        nodes.append(n)
    errors.extend(json_errors)
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
        if old.get("history"):
            x["history"] = list(old["history"])[-20:]
        if old.get("performance_test"):
            x["performance_test"] = old["performance_test"]
        if old.get("performance_history"):
            x["performance_history"] = list(old["performance_history"])[-12:]
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
        "performance_test": node.get("performance_test") if isinstance(node.get("performance_test"), dict) else None,
        "history": list(node.get("history", []) or [])[-20:],
        "performance_history": list(node.get("performance_history", []) or [])[-12:],
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
    elif proto == "hysteria2":
        base["password"] = node["password"]
        if node.get("obfs"):
            base["obfs"] = node["obfs"]
    elif proto == "tuic":
        base.update(uuid=node["uuid"], password=node["password"],
                    congestion_control=node.get("congestion_control", "cubic"),
                    udp_relay_mode=node.get("udp_relay_mode", "native"),
                    zero_rtt_handshake=bool(node.get("zero_rtt_handshake", False)))
    elif proto == "anytls":
        base["password"] = node["password"]
        for key in ("idle_session_check_interval", "idle_session_timeout", "client_metadata", "min_idle_session"):
            if node.get(key) not in (None, ""):
                base[key] = node[key]
    elif proto == "shadowtls":
        base["version"] = int(node.get("version", 1))
        if node.get("password"):
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
