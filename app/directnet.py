from __future__ import annotations
import http.client, ipaddress, os, socket, ssl, struct, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET

MAGIC = 0x2112A442
DOH_BOOTSTRAPS = (("76.76.10.11", "/p0"), ("76.76.2.11", "/p0"))


def _dns_name_wire(name: str):
    labels = name.rstrip(".").split(".")
    if not labels or any(not x or len(x.encode("idna")) > 63 for x in labels):
        raise ValueError("INVALID_DNS_NAME")
    return b"".join(bytes([len(x.encode("idna"))]) + x.encode("idna") for x in labels) + b"\x00"


def _skip_dns_name(data: bytes, pos: int):
    seen = 0
    while pos < len(data):
        n = data[pos]
        if n & 0xC0 == 0xC0:
            if pos + 1 >= len(data):
                raise ValueError("TRUNCATED_DNS_POINTER")
            return pos + 2
        if n == 0:
            return pos + 1
        if n > 63 or pos + 1 + n > len(data):
            raise ValueError("INVALID_DNS_LABEL")
        pos += 1 + n
        seen += 1
        if seen > 127:
            raise ValueError("DNS_NAME_TOO_DEEP")
    raise ValueError("TRUNCATED_DNS_NAME")


def _parse_dns_a(data: bytes, txid: bytes):
    if len(data) < 12 or data[:2] != txid:
        return []
    flags, qd, an, ns, ar = struct.unpack("!HHHHH", data[2:12])
    if not (flags & 0x8000) or (flags & 0x000F):
        return []
    pos = 12
    for _ in range(qd):
        pos = _skip_dns_name(data, pos)
        if pos + 4 > len(data):
            return []
        pos += 4
    ips = []
    for _ in range(an + ns + ar):
        try:
            pos = _skip_dns_name(data, pos)
            if pos + 10 > len(data):
                break
            rtype, rclass, _ttl, rdlen = struct.unpack("!HHIH", data[pos:pos + 10])
            pos += 10
            if pos + rdlen > len(data):
                break
            rdata = data[pos:pos + rdlen]
            pos += rdlen
            if rtype == 1 and rclass == 1 and rdlen == 4:
                ip = socket.inet_ntoa(rdata)
                addr = ipaddress.ip_address(ip)
                if addr.is_global and ip not in ips:
                    ips.append(ip)
        except (ValueError, OSError):
            break
    return ips


def doh_a(host: str, timeout: float = 2.5):
    host = str(host or "").strip().lower()
    if not host or len(host) > 253:
        return {"ips": [], "endpoint": "", "errors": ["INVALID_HOST"]}
    try:
        qname = _dns_name_wire(host)
    except ValueError as exc:
        return {"ips": [], "endpoint": "", "errors": [str(exc)]}
    errors = []
    for ip, path in DOH_BOOTSTRAPS:
        started = time.monotonic()
        txid = os.urandom(2)
        wire = txid + b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00" + qname + struct.pack("!HH", 1, 1)
        conn = None
        try:
            conn = http.client.HTTPSConnection(ip, 443, timeout=timeout, context=ssl.create_default_context())
            conn.request("POST", path, body=wire, headers={
                "Host": ip,
                "Content-Type": "application/dns-message",
                "Accept": "application/dns-message",
                "User-Agent": "FreeNetHub-DirectDNS/1.0",
                "Connection": "close",
            })
            resp = conn.getresponse()
            body = resp.read(65536)
            ctype = str(resp.getheader("content-type") or "").lower()
            if resp.status != 200 or "application/dns-message" not in ctype:
                raise RuntimeError(f"DOH_HTTP_{resp.status}")
            ips = _parse_dns_a(body, txid)
            if not ips:
                raise RuntimeError("DOH_NO_GLOBAL_A")
            return {
                "ips": ips[:8],
                "endpoint": f"https://{ip}{path}",
                "seconds": round(time.monotonic() - started, 3),
                "validatedTls": True,
                "errors": errors,
            }
        except Exception as exc:
            errors.append(f"{ip}: {type(exc).__name__}: {exc}")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
    return {"ips": [], "endpoint": "", "validatedTls": False, "errors": errors}


def dns_interception_probe(host: str):
    system = []
    try:
        for row in socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM):
            ip = row[4][0]
            if ip not in system:
                system.append(ip)
    except OSError:
        pass
    secure = doh_a(host)
    sys_global = []
    sys_non_global = []
    for ip in system:
        try:
            (sys_global if ipaddress.ip_address(ip).is_global else sys_non_global).append(ip)
        except ValueError:
            sys_non_global.append(ip)
    secure_ips = list(secure.get("ips") or [])
    interception = bool(sys_non_global and secure_ips)
    mismatch = bool(sys_global and secure_ips and not set(sys_global).intersection(secure_ips))
    return {
        "host": host,
        "systemIps": system,
        "systemGlobalIps": sys_global,
        "systemNonGlobalIps": sys_non_global,
        "secureDoH": secure,
        "interceptionConfirmed": interception,
        "answerMismatch": mismatch,
    }
SHARED = ipaddress.ip_network("100.64.0.0/10")
STUN_TARGETS = (("stun.cloudflare.com", 3478), ("stun.l.google.com", 19302))


def _parse_stun(data: bytes, txid: bytes):
    if len(data) < 20:
        return None
    mtype, mlen, magic = struct.unpack("!HHI", data[:8])
    if magic != MAGIC or data[8:20] != txid or not (mtype & 0x0100):
        return None
    pos, end = 20, min(len(data), 20 + mlen)
    while pos + 4 <= end:
        atype, alen = struct.unpack("!HH", data[pos:pos + 4])
        pos += 4
        val = data[pos:pos + alen]
        pos += (alen + 3) & ~3
        if atype != 0x0020 or alen < 8:
            continue
        family = val[1]
        port = struct.unpack("!H", val[2:4])[0] ^ (MAGIC >> 16)
        if family == 1 and len(val) >= 8:
            cookie = struct.pack("!I", MAGIC)
            raw = bytes(a ^ b for a, b in zip(val[4:8], cookie))
            return {"ip": socket.inet_ntop(socket.AF_INET, raw), "port": port}
        if family == 2 and len(val) >= 20:
            mask = struct.pack("!I", MAGIC) + txid
            raw = bytes(a ^ b for a, b in zip(val[4:20], mask))
            return {"ip": socket.inet_ntop(socket.AF_INET6, raw), "port": port}
    return None


def stun_mappings(local_ip: str, timeout: float = 1.5):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((local_ip, 0))
    s.settimeout(timeout)
    local_port = s.getsockname()[1]
    rows = []
    try:
        for host, port in STUN_TARGETS:
            try:
                infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_DGRAM)
                if not infos:
                    raise OSError("NO_IPV4")
                dest = infos[0][4]
                txid = os.urandom(12)
                req = struct.pack("!HHI", 0x0001, 0, MAGIC) + txid
                s.sendto(req, dest)
                deadline = time.monotonic() + timeout
                mapped = None
                source = None
                while time.monotonic() < deadline:
                    data, addr = s.recvfrom(4096)
                    candidate = _parse_stun(data, txid)
                    if candidate:
                        mapped, source = candidate, addr
                        break
                if not mapped:
                    raise TimeoutError("NO_STUN_MAPPING")
                rows.append({
                    "target": f"{host}:{port}",
                    "resolved": dest[0],
                    "mappedIp": mapped["ip"],
                    "mappedPort": mapped["port"],
                    "from": f"{source[0]}:{source[1]}",
                })
            except Exception as exc:
                rows.append({"target": f"{host}:{port}", "error": f"{type(exc).__name__}: {exc}"})
    finally:
        s.close()
    good = [(r.get("mappedIp"), r.get("mappedPort")) for r in rows if r.get("mappedIp")]
    return {
        "localPort": local_port,
        "results": rows,
        "mappingStableAcrossTargets": len(good) >= 2 and len(set(good)) == 1,
        "portPreserved": bool(good) and all(p == local_port for _, p in good),
        "publicMappedIp": good[0][0] if good else "",
        "publicMappedPort": good[0][1] if good else None,
    }


def _ssdp_locations(local_ip: str, gateway: str, timeout: float = 0.65):
    locations = []
    for st in (
        "urn:schemas-upnp-org:device:InternetGatewayDevice:2",
        "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
        "urn:schemas-upnp-org:service:WANIPConnection:1",
    ):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            s.settimeout(timeout)
            s.bind((local_ip, 0))
            msg = (
                "M-SEARCH * HTTP/1.1\r\n"
                "HOST: 239.255.255.250:1900\r\n"
                'MAN: "ssdp:discover"\r\n'
                "MX: 1\r\n"
                f"ST: {st}\r\n\r\n"
            ).encode("ascii")
            s.sendto(msg, ("239.255.255.250", 1900))
            end = time.monotonic() + timeout
            while time.monotonic() < end:
                try:
                    data, _ = s.recvfrom(65535)
                except socket.timeout:
                    break
                headers = {}
                for line in data.decode("utf-8", "ignore").split("\r\n")[1:]:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        headers[k.strip().lower()] = v.strip()
                loc = headers.get("location")
                if not loc:
                    continue
                u = urllib.parse.urlparse(loc)
                if u.scheme == "http" and u.hostname == gateway and loc not in locations:
                    locations.append(loc)
        finally:
            s.close()
    return locations


def upnp_external_ip(local_ip: str, gateway: str):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    out = {"available": False, "externalIp": "", "location": "", "serviceType": "", "errors": []}
    for loc in _ssdp_locations(local_ip, gateway):
        try:
            raw = opener.open(urllib.request.Request(loc, headers={"User-Agent": "FreeNetHub-DirectAudit/1.0"}), timeout=2).read(262144)
            root = ET.fromstring(raw)
            for svc in root.iter():
                if not svc.tag.endswith("service"):
                    continue
                fields = {c.tag.split("}")[-1]: (c.text or "").strip() for c in list(svc)}
                stype = fields.get("serviceType", "")
                if "WANIPConnection" not in stype and "WANPPPConnection" not in stype:
                    continue
                control = urllib.parse.urljoin(loc, fields.get("controlURL", ""))
                u = urllib.parse.urlparse(control)
                if u.scheme != "http" or u.hostname != gateway:
                    continue
                body = (
                    '<?xml version="1.0"?>'
                    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
                    's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
                    f'<s:Body><u:GetExternalIPAddress xmlns:u="{stype}"></u:GetExternalIPAddress></s:Body></s:Envelope>'
                ).encode("utf-8")
                req = urllib.request.Request(control, data=body, method="POST", headers={
                    "Content-Type": 'text/xml; charset="utf-8"',
                    "SOAPAction": f'"{stype}#GetExternalIPAddress"',
                    "Connection": "close",
                })
                resp = opener.open(req, timeout=2).read(262144)
                rr = ET.fromstring(resp)
                for node in rr.iter():
                    if node.tag.endswith("NewExternalIPAddress") and node.text:
                        ip = node.text.strip()
                        ipaddress.ip_address(ip)
                        return {"available": True, "externalIp": ip, "location": loc, "serviceType": stype, "errors": out["errors"]}
        except Exception as exc:
            out["errors"].append(f"{type(exc).__name__}: {exc}")
    return out


def pcp_natpmp(local_ip: str, gateway: str, timeout: float = 0.7):
    result = {"pcp": {"supported": False}, "natPmp": {"supported": False}}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.bind((local_ip, 0))
        client_ip = ipaddress.IPv6Address("::ffff:" + local_ip).packed
        req = bytes([2, 0, 0, 0]) + struct.pack("!I", 0) + client_ip
        s.sendto(req, (gateway, 5351))
        data, addr = s.recvfrom(2048)
        if len(data) >= 24:
            result["pcp"] = {
                "supported": data[0] == 2 and bool(data[1] & 0x80),
                "resultCode": data[3],
                "from": f"{addr[0]}:{addr[1]}",
            }
    except Exception as exc:
        result["pcp"]["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            s.close()
        except Exception:
            pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.bind((local_ip, 0))
        s.sendto(b"\x00\x00", (gateway, 5351))
        data, addr = s.recvfrom(2048)
        if len(data) >= 12:
            result["natPmp"] = {
                "supported": data[0] == 0 and data[1] == 128,
                "resultCode": struct.unpack("!H", data[2:4])[0],
                "externalIp": socket.inet_ntoa(data[8:12]),
                "from": f"{addr[0]}:{addr[1]}",
            }
    except Exception as exc:
        result["natPmp"]["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            s.close()
        except Exception:
            pass
    return result


def classify_nat(wan_ip: str, mapped_ip: str):
    try:
        wan = ipaddress.ip_address(wan_ip)
    except ValueError:
        return "UNKNOWN"
    if wan.version == 4 and wan in SHARED:
        return "CGNAT_CONFIRMED_SHARED_100_64_10"
    if wan.is_private:
        return "UPSTREAM_PRIVATE_NAT"
    if wan.is_global:
        if mapped_ip:
            try:
                mapped = ipaddress.ip_address(mapped_ip)
                if mapped != wan:
                    return "UPSTREAM_NAT_OR_POOL_SUSPECTED"
            except ValueError:
                pass
        return "PUBLIC_WAN_OR_1TO1_NAT"
    return "UNKNOWN"


def audit(local_ip: str, gateway: str):
    ipaddress.ip_address(local_ip)
    ipaddress.ip_address(gateway)
    upnp = upnp_external_ip(local_ip, gateway)
    stun = stun_mappings(local_ip)
    control = pcp_natpmp(local_ip, gateway)
    nat_class = classify_nat(upnp.get("externalIp", ""), stun.get("publicMappedIp", ""))
    return {
        "natClassification": nat_class,
        "cgnatConfirmed": nat_class == "CGNAT_CONFIRMED_SHARED_100_64_10",
        "upnp": upnp,
        "stun": stun,
        "portControl": control,
        "udpTraversalCandidate": bool(stun.get("mappingStableAcrossTargets") and stun.get("portPreserved")),
    }
