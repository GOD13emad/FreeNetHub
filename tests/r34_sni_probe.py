import json, socket, ssl, time

LOCAL="192.168.20.5"
HOSTS=["www.youtube.com","www.google.com","chatgpt.com"]
out=[]
for host in HOSTS:
    try:
        ips=socket.getaddrinfo(host,443,socket.AF_INET,socket.SOCK_STREAM)
        ip=ips[0][4][0]
    except Exception as e:
        out.append({"host":host,"resolveError":type(e).__name__+": "+str(e)})
        continue
    for mode in ("sni","no_sni"):
        t=time.time(); row={"host":host,"ip":ip,"mode":mode}
        try:
            raw=socket.socket(socket.AF_INET,socket.SOCK_STREAM);raw.settimeout(4);raw.bind((LOCAL,0));raw.connect((ip,443))
            row["tcp"]=True
            ctx=ssl.create_default_context()
            if mode=="no_sni":
                ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE; server_name=None
            else: server_name=host
            ss=ctx.wrap_socket(raw,server_hostname=server_name)
            row["tls"]=True;row["tlsVersion"]=ss.version();row["cipher"]=ss.cipher()[0];row["seconds"]=round(time.time()-t,3)
            ss.close()
        except Exception as e:
            row["tls"]=False;row["seconds"]=round(time.time()-t,3);row["error"]=type(e).__name__+": "+str(e)
            try: raw.close()
            except Exception: pass
        out.append(row)
print(json.dumps(out,indent=2))
