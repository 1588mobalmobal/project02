from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

embed_instance = None

def init_embed():
    global embed_instance
    if embed_instance is None:
        embed_instance = SentenceTransformer("jhgan/ko-sroberta-multitask")
    return embed_instance

def get_embedding(user_input):
    model = init_embed()
    embedding = model.encode([user_input])
    return embedding

def store_vector(embedding):
    dimension = 768
    index = faiss.IndexFlatL2(dimension) # 왜 L2 기반 인덱스인지?
    
    try:
        index = faiss.read_index("vector_store.index")
    except:
        pass
    index.add(np.array(embedding))
    faiss.write_index(index, 'vector_store.index')

    return index.ntotal - 1

def search_vector_store(embedding):
    dimension = 768
    index = faiss.IndexFlatL2(dimension) # 왜 L2 기반 인덱스인지?
    try:
        index = faiss.read_index("vector_store.index")
    except:
        pass
    k = 5
    distances, indices = index.search(np.array(embedding), k)

    return distances, indices




