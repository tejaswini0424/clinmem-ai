def precision_recall(actual,expected,k):
 actual=set(actual[:k]);expected=set(expected);hits=len(actual&expected)
 return {'precision':hits/len(actual) if actual else 0.,'recall':hits/len(expected) if expected else 0.}
