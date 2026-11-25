const origin=process.argv[2]||'https://clinmem-ai.vercel.app';
async function visitor(){
 const r=await fetch(origin+'/api/auth/guest',{method:'POST',signal:AbortSignal.timeout(60000)});
 const body=await r.json();if(r.status!==200||!body.guest)throw Error('Public visitor bootstrap failed: HTTP '+r.status);
 const cookie=r.headers.get('set-cookie')?.split(';')[0];if(!cookie)throw Error('Visitor cookie missing');
 const response=await fetch(origin+'/api/workspace',{headers:{Cookie:cookie},signal:AbortSignal.timeout(45000)});
 const workspace=await response.json();if(response.status!==200)throw Error('Public workspace failed');
 return {cookie,workspace};
}
(async()=>{
 const first=await visitor();const evidence=first.workspace.memories.filter(m=>['Long-Term','Semantic'].includes(m.memory_type));
 if(evidence.length!==5||!evidence.every(m=>m.content.includes('SYNTHETIC DEMO')))throw Error('Synthetic visitor library missing');
 console.log('No-login dashboard data: passed; five synthetic evidence records available');
 const second=await visitor();const ids=new Set(first.workspace.memories.map(m=>m.id));
 if(second.workspace.memories.some(m=>ids.has(m.id)))throw Error('Visitor isolation failed');
 console.log('Independent visitor isolation: passed');
 const result=await fetch(origin+'/api/assistant',{method:'POST',headers:{Cookie:first.cookie,'Content-Type':'application/json'},body:JSON.stringify({query:'diabetes glucose intervention alpha',k:3}),signal:AbortSignal.timeout(60000)});
 const answer=await result.json();if(result.status!==200||!answer.answer.includes('Conflicting'))throw Error('Guest retrieval failed');
 console.log('Public visitor retrieval and conflict labels: passed');
 console.log('Public dashboard verification complete. No registration or password was required.');
})().catch(e=>{console.error(e.message);process.exitCode=1});
