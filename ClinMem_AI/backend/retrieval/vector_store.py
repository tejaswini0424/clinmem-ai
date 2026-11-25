from sklearn.metrics.pairwise import cosine_similarity
def similarities(matrix): return cosine_similarity(matrix[-1:],matrix[:-1]).ravel()
