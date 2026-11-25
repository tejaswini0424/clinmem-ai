import pandas as pd
def frame(rows):
 return pd.DataFrame([{'ID':m.id,'Content':m.content,'Type':m.memory_type,'Category':m.category,'Source':m.source,'Page':m.page,'Created':m.created,'Updated':m.updated,'Version':m.version,'Status':m.status,'Quality':m.quality,'Source date':m.source_date} for m in rows])
