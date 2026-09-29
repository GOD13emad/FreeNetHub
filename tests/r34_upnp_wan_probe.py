import json, socket, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET

LOCAL_IP = "192.168.20.5"
SSDP = ("239.255.255.250", 1900)
TARGETS = [
    "urn:schemas-upnp-org:device:InternetGatewayDevice:2",
    "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
    "urn:schemas-upnp-org:service:WANIPConnection:2",
    "urn:schemas-upnp-org:service:WANIPConnection:1",
]
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
locations = []

for st in TARGETS:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.settimeout(0.6)
    s.bind((LOCAL_IP, 0))
    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 1\r\n"
        f"ST: {st}\r\n\r\n"
    ).encode("ascii")
    s.sendto(msg, SSDP)
    end = time.time() + 1.2
    while time.time() < end:
        try:
            data, addr = s.recvfrom(65535)
        except socket.timeout:
            break
        text = data.decode("utf-8", "ignore")
        headers = {}
        for line in text.split("\r\n")[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        loc = headers.get("location")
        if loc and loc not in locations:
            locations.append(loc)
    s.close()

result = {"localIp": LOCAL_IP, "locations": locations, "externalIps": [], "services": [], "errors": []}
for loc in locations:
    try:
        req = urllib.request.Request(loc, headers={"User-Agent": "FreeNetHub-R34-ReadOnlyProbe/1.0"})
        xml = opener.open(req, timeout=2.0).read()
        root = ET.fromstring(xml)
        base = loc
        for svc in root.iter():
            if svc.tag.endswith("service"):
                fields = {}
                for c in list(svc):
                    fields[c.tag.split("}")[-1]] = (c.text or "").strip()
                stype = fields.get("serviceType", "")
                if "WANIPConnection" not in stype and "WANPPPConnection" not in stype:
                    continue
                control = urllib.parse.urljoin(base, fields.get("controlURL", ""))
                result["services"].append({"type": stype, "controlURL": control})
                body = (
                    '<?xml version="1.0"?>'
                    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
                    's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
                    '<s:Body><u:GetExternalIPAddress xmlns:u="' + stype + '"></u:GetExternalIPAddress>'
                    '</s:Body></s:Envelope>'
                ).encode("utf-8")
                soap = urllib.request.Request(
                    control,
                    data=body,
                    method="POST",
                    headers={
                        "Content-Type": 'text/xml; charset="utf-8"',
                        "SOAPAction": f'"{stype}#GetExternalIPAddress"',
                        "Connection": "close",
                    },
                )
                resp = opener.open(soap, timeout=2.0).read()
                rr = ET.fromstring(resp)
                for node in rr.iter():
                    if node.tag.endswith("NewExternalIPAddress") and node.text:
                        ip = node.text.strip()
                        if ip and ip not in result["externalIps"]:
                            result["externalIps"].append(ip)
    except Exception as e:
        result["errors"].append({"location": loc, "error": type(e).__name__ + ": " + str(e)})

print(json.dumps(result, ensure_ascii=False, indent=2))
