from backend.retrieval.hybrid_retriever import search
def test_retrieval(store):
 id=store.add('Diabetes glucose insulin evidence',source='A');store.add('Hypertension blood pressure',source='B')
 assert search(store,'diabetes glucose')[0]['memory'].id==id
 assert search(store,'quantum zebra spaceship')==[]
 assert search(store,'diabetes',category='Procedure')==[]
