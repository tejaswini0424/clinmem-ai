from backend.generative_ai.response_generator import generate
def run(store,query,results): return {'records':len(results),'findings':0,'summary':'Source-linked extractive explanation generated.','answer':generate(query,results)}
