const dgram=require('dgram'),dns=require('dns').promises,crypto=require('crypto');
const localIp=process.argv[2], localPort=Number(process.argv[3]), peerIp=process.argv[4], peerPort=Number(process.argv[5]), label=process.argv[6]||'peer';
const MAGIC=0x2112A442, stunHost='stun.cloudflare.com', stunPort=3478;
function stunMap(s){
  return dns.resolve4(stunHost).then(addrs=>new Promise((resolve,reject)=>{
    const tx=crypto.randomBytes(12), req=Buffer.alloc(20);
    req.writeUInt16BE(1,0); req.writeUInt16BE(0,2); req.writeUInt32BE(MAGIC,4); tx.copy(req,8);
    const timer=setTimeout(()=>reject(new Error('stun-timeout')),2500);
    const onmsg=(msg,rinfo)=>{
      if(rinfo.address!==addrs[0] && rinfo.port!==stunPort) return;
      let pos=20,mlen=msg.readUInt16BE(2),mapped=null;
      while(pos+4<=20+mlen&&pos+4<=msg.length){
        const type=msg.readUInt16BE(pos),len=msg.readUInt16BE(pos+2);pos+=4;
        const val=msg.subarray(pos,pos+len);pos+=(len+3)&~3;
        if(type===0x0020&&len>=8&&val[1]===1){
          const mp=val.readUInt16BE(2)^(MAGIC>>>16),c=Buffer.alloc(4);c.writeUInt32BE(MAGIC,0);
          mapped={ip:[val[4]^c[0],val[5]^c[1],val[6]^c[2],val[7]^c[3]].join('.'),port:mp};break;
        }
      }
      if(mapped){clearTimeout(timer);s.off('message',onmsg);resolve(mapped);}
    };
    s.on('message',onmsg); s.send(req,stunPort,addrs[0]);
  }));
}
(async()=>{
  const s=dgram.createSocket('udp4'); const events=[];
  await new Promise((res,rej)=>{s.once('error',rej);s.bind(localPort,localIp,res)});
  s.on('message',(msg,rinfo)=>{
    const text=msg.toString('utf8');
    if(text.startsWith('FNH-R34-HOLE-')){
      events.push({from:rinfo.address+':'+rinfo.port,data:text});
      console.log(JSON.stringify({state:'RECEIVED',label,from:rinfo.address+':'+rinfo.port,data:text}),flush=true);
    }
  });
  const mapped=await stunMap(s);
  console.log(JSON.stringify({state:'READY',label,local:localIp+':'+localPort,mapped,peer:peerIp+':'+peerPort}));
  const end=Date.now()+9000; let seq=0;
  while(Date.now()<end){
    const b=Buffer.from('FNH-R34-HOLE-'+label+'-'+(++seq));
    await new Promise((res,rej)=>s.send(b,peerPort,peerIp,e=>e?rej(e):res()));
    await new Promise(r=>setTimeout(r,250));
  }
  await new Promise(r=>setTimeout(r,1200));
  console.log(JSON.stringify({state:'DONE',label,receivedCount:events.length,events:events.slice(0,10)}));
  s.close();
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
