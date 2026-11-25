import os
from sklearn.feature_extraction.text import TfidfVectorizer
def encode(texts):
 if os.getenv('CLINMEM_EMBEDDINGS')=='sentence-transformers':
  try:
   from sentence_transformers import SentenceTransformer
   return SentenceTransformer('all-MiniLM-L6-v2',local_files_only=True).encode(texts)
  except (ImportError,OSError): pass
 return TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5)).fit_transform(texts)
