import re
TERMS={'diabetes':'Condition','hypertension':'Condition','cardiovascular':'Condition','metformin':'Medication','insulin':'Medication','blood pressure':'Clinical measure','glucose':'Clinical measure','randomized trial':'Research','angiography':'Procedure'}
def clean(text): return re.sub(r'\s+',' ',text).strip()
def entities(text): return [term for term in TERMS if term in text.lower()]
def category(text):
 found=entities(text)
 return TERMS[found[0]] if found else 'General'
