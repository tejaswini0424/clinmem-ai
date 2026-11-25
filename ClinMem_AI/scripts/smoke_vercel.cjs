/* Real production verification: synthetic records only, no local account data. */
const crypto = require('node:crypto');
const origin = process.argv[2] || 'https://clinmem-ai.vercel.app';
let cookie='';
async function request(path,method='GET',body){
  const response=await fetch(origin+path,{method,headers:{...(body?{'Content-Type':'application/json'}:{}),...(cookie?{Cookie:cookie}:{})},body:body?JSON.stringify(body):undefined});
  const contentType=response.headers.get('content-type')||'';
  const data=contentType.includes('application/json')?await response.json():await response.text();
  if(!response.ok)throw Error(`${path}: HTTP ${response.status}; ${JSON.stringify(data).slice(0,200)}`);
  if(response.headers.get('set-cookie'))cookie=response.headers.get('set-cookie').split(';')[0];
  return data;
}
(async()=>{
  console.log('Health:',JSON.stringify(await request('/api/health')));
  for(const path of ['/assets/app.js','/assets/styles.css']){
    const r=await fetch(origin+path);if(r.status!==200)throw Error(`Missing asset ${path}`);console.log('Asset:',path,r.status);
  }
  const credentials={username:'deployment-check-'+Date.now(),password:crypto.randomBytes(32).toString('hex')};
  await request('/api/auth/register','POST',{...credentials,confirm:credentials.password});
  await request('/api/auth/login','POST',credentials);
  console.log('Registration and secure-cookie login: passed');
  const seed=await request('/api/sample','POST');
  if(seed.update.findings!==1)throw Error('Expected one synthetic conflict');
  const answer=await request('/api/assistant','POST',{query:'diabetes glucose intervention alpha',k:3});
  if(!answer.answer.includes('Conflicting')||answer.results.length<2)throw Error('Evidence retrieval check failed');
  console.log('Synthetic ingestion, conflict screening and retrieval: passed');
  const evaluation=await request('/api/evaluate?k=3','POST');
  if(evaluation.metrics.length!==4)throw Error('Expected four evaluation queries');
  const avg=key=>evaluation.metrics.reduce((s,m)=>s+m[key],0)/evaluation.metrics.length;
  console.log('Synthetic benchmark:',JSON.stringify({precision:avg('precision'),recall:avg('recall')}));
  const graph=await request('/api/graph');
  if(!graph.edges.some(e=>e.kind.includes('Contradicts')))throw Error('Graph contradiction missing');
  const workspace=await request('/api/workspace');
  if(!workspace.analyses.length||workspace.memories.some(m=>m.memory_type==='Working'))throw Error('History or task cleanup failed');
  for(const format of ['json','csv','pdf']){
    const r=await fetch(origin+'/api/export/'+format,{headers:{Cookie:cookie}});
    const bytes=new Uint8Array(await r.arrayBuffer());
    if(!r.ok||!bytes.length)throw Error('Export failed: '+format);
    if(format==='pdf'&&Buffer.from(bytes.slice(0,4)).toString()!=='%PDF')throw Error('Invalid PDF');
    console.log('Export:',format,r.status,bytes.length+' bytes');
  }
  await request('/api/auth/logout','POST');
  console.log('Logout: passed');
  console.log('Production verification complete. Synthetic-only test account retained; credentials were not logged.');
})().catch(e=>{console.error(e.message);process.exitCode=1});
