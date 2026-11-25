from config.settings import DISCLAIMER
def generate(query,results):
 if not results: return 'Sufficient supporting knowledge is unavailable in your stored evidence. '+DISCLAIMER
 lines=['Evidence-grounded extractive summary (retrieval relevance is not clinical confidence):']
 for r in results:
  m=r['memory'];lines.append(f'[{m.id}] {m.content} (Source: {m.source or "Unspecified"}; page: {m.page if m.page else "not available"}; quality: {m.quality}; status: {m.status}; updated: {m.updated}; selection: {r.get("match","Hybrid text relevance")})')
 lines.append('Uncertainty: sources are unverified unless reviewed. Possible conflicts and inferred associations require human assessment. No causal or treatment conclusions are generated.')
 lines.append(DISCLAIMER)
 return '\n\n'.join(lines)
