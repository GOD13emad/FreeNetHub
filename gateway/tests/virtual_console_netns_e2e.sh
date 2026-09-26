#!/usr/bin/env bash
set -euo pipefail

C="fnhc$$"
G="fnhg$$"
W="fnhw$$"
TMP="$(mktemp -d)"
BEFORE="$TMP/routes.before"
AFTER="$TMP/routes.after"
SERVER="$TMP/wan_echo.py"
SERVER_OUT="$TMP/wan.json"
CLIENT_OUT="$TMP/client.json"

cleanup() {
  sudo ip netns del "$C" 2>/dev/null || true
  sudo ip netns del "$G" 2>/dev/null || true
  sudo ip netns del "$W" 2>/dev/null || true
}
trap 'cleanup; rm -rf "$TMP"' EXIT

ip route show table all | sort > "$BEFORE"
cleanup

sudo ip netns add "$C"
sudo ip netns add "$G"
sudo ip netns add "$W"

sudo ip link add c0 type veth peer name g0
sudo ip link set c0 netns "$C"
sudo ip link set g0 netns "$G"
sudo ip link add g1 type veth peer name w0
sudo ip link set g1 netns "$G"
sudo ip link set w0 netns "$W"

for ns in "$C" "$G" "$W"; do sudo ip -n "$ns" link set lo up; done
sudo ip -n "$C" addr add 10.203.1.2/24 dev c0
sudo ip -n "$C" link set c0 up
sudo ip -n "$C" route add default via 10.203.1.1

sudo ip -n "$G" addr add 10.203.1.1/24 dev g0
sudo ip -n "$G" addr add 10.203.2.1/24 dev g1
sudo ip -n "$G" link set g0 up
sudo ip -n "$G" link set g1 up
sudo ip netns exec "$G" sysctl -q -w net.ipv4.ip_forward=1

sudo ip -n "$W" addr add 10.203.2.2/24 dev w0
sudo ip -n "$W" link set w0 up

if command -v iptables >/dev/null 2>&1; then
  sudo ip netns exec "$G" iptables -t nat -A POSTROUTING -s 10.203.1.0/24 -o g1 -j MASQUERADE
  NAT_BACKEND=iptables
else
  sudo ip netns exec "$G" nft add table ip fnh
  sudo ip netns exec "$G" nft 'add chain ip fnh postrouting { type nat hook postrouting priority 100; }'
  sudo ip netns exec "$G" nft add rule ip fnh postrouting ip saddr 10.203.1.0/24 oifname '"g1"' masquerade
  NAT_BACKEND=nft
fi

cat > "$SERVER" <<'PY'
import json, socket
TCP=("10.203.2.2",18080); UDP=("10.203.2.2",18081)
ts=socket.socket(); ts.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); ts.bind(TCP); ts.listen(1); ts.settimeout(10)
us=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); us.bind(UDP); us.settimeout(10)
c,a=ts.accept(); data=c.recv(4096); c.sendall(b"WAN:"+data); c.close()
udata,ua=us.recvfrom(4096); us.sendto(b"WAN:"+udata,ua)
print(json.dumps({"tcpPeer":a[0],"udpPeer":ua[0],"tcpPayload":data.decode(),"udpPayload":udata.decode()}),flush=True)
PY

sudo ip netns exec "$W" python3 "$SERVER" > "$SERVER_OUT" &
SPID=$!
sleep 1

sudo ip netns exec "$C" python3 - <<'PY' > "$CLIENT_OUT"
import json,socket
t=socket.socket(); t.settimeout(5); t.connect(("10.203.2.2",18080)); t.sendall(b"console-tcp"); tr=t.recv(4096); t.close()
u=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); u.settimeout(5); u.sendto(b"console-udp",("10.203.2.2",18081)); ur,_=u.recvfrom(4096); u.close()
print(json.dumps({"tcpReply":tr.decode(),"udpReply":ur.decode()}))
PY
wait "$SPID"

python3 - "$SERVER_OUT" "$CLIENT_OUT" <<'PY'
import json,sys
s=json.load(open(sys.argv[1])); c=json.load(open(sys.argv[2]))
checks={
 "tcp_nat_source":s["tcpPeer"]=="10.203.2.1",
 "udp_nat_source":s["udpPeer"]=="10.203.2.1",
 "tcp_payload":s["tcpPayload"]=="console-tcp" and c["tcpReply"]=="WAN:console-tcp",
 "udp_payload":s["udpPayload"]=="console-udp" and c["udpReply"]=="WAN:console-udp",
}
out={"schema":1,"level":"KERNEL_NETNS_NAT","checks":checks,"observed":{"wan":s,"console":c}}
out["status"]="PASS" if all(checks.values()) else "FAIL"
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["status"]=="PASS" else 1)
PY

cleanup
trap 'rm -rf "$TMP"' EXIT
ip route show table all | sort > "$AFTER"
cmp -s "$BEFORE" "$AFTER"
echo "HOST_ROUTE_TABLE_UNCHANGED=PASS"
echo "NAT_BACKEND=$NAT_BACKEND"
