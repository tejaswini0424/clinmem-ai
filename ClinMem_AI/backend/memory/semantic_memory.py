MEMORY_TYPE='Semantic'
def retrieve(store): return store.memories([MEMORY_TYPE])
def remember(store,content,**metadata): return store.add(content,memory_type=MEMORY_TYPE,**metadata)
