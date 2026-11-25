from backend.evaluation.metrics import precision_recall
from backend.agents.memory_evaluation_agent import run
def test_metrics(store):
 assert precision_recall([1,2],[2,3],2)=={'precision':.5,'recall':.5}
 id=store.add('Diabetes glucose evidence')
 result=run(store,[{'query':'diabetes glucose','expected_ids':[id]}],1)
 assert result['metrics'][0]['recall']==1
