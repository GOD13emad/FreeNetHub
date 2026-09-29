import json, socket, struct, ipaddress

LOCAL_IP = "192.168.20.5"
GATEWAY = "192.168.20.1"
PORT = 5351
out = {"localIp": LOCAL_IP, "gateway": GATEWAY, "pcpAnnounce": None, "natPmpPublicAddress": None}

# PCP ANNOUNCE (read-only discovery; no mapping requested)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.5)
    s.bind((LOCAL_IP, 0))
    client_ip = ipaddress.IPv6Address("::ffff:" + LOCAL_IP).packed
    req = bytes([2, 0, 0, 0]) + struct.pack("!I", 0) + client_ip
    s.sendto(req, (GATEWAY, PORT))
    data, addr = s.recvfrom(2048)
    if len(data) >= 24:
        out["pcpAnnounce"] = {
            "from": f"{addr[0]}:{addr[1]}",
            "version": data[0],
            "response": bool(data[1] & 0x80),
            "opcode": data[1] & 0x7F,
            "resultCode": data[3],
            "lifetime": struct.unpack("!I", data[4:8])[0],
            "epochTime": struct.unpack("!I", data[8:12])[0],
            "bytes": len(data),
        }
    else:
        out["pcpAnnounce"] = {"from": f"{addr[0]}:{addr[1]}", "bytes": len(data), "hex": data.hex()}
except Exception as e:
    out["pcpAnnounce"] = {"error": type(e).__name__ + ": " + str(e)}
finally:
    try: s.close()
    except Exception: pass

# NAT-PMP public-address request (read-only)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.5)
    s.bind((LOCAL_IP, 0))
    s.sendto(b"\x00\x00", (GATEWAY, PORT))
    data, addr = s.recvfrom(2048)
    if len(data) >= 12:
        out["natPmpPublicAddress"] = {
            "from": f"{addr[0]}:{addr[1]}",
            "version": data[0],
            "opcode": data[1],
            "resultCode": struct.unpack("!H", data[2:4])[0],
            "epochTime": struct.unpack("!I", data[4:8])[0],
            "externalIp": socket.inet_ntoa(data[8:12]),
            "bytes": len(data),
        }
    else:
        out["natPmpPublicAddress"] = {"from": f"{addr[0]}:{addr[1]}", "bytes": len(data), "hex": data.hex()}
except Exception as e:
    out["natPmpPublicAddress"] = {"error": type(e).__name__ + ": " + str(e)}
finally:
    try: s.close()
    except Exception: pass

print(json.dumps(out, indent=2))
