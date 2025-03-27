import chromadb
from sentence_transformers import SentenceTransformer

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

def store_vector(user_input, embedding, vector_id):
    client = chromadb.PersistentClient()
    try :
        collection = client.get_collection(name="log_vector")
    except:
        collection = client.create_collection(name="log_vector")
    collection.add(documents=user_input, embeddings=embedding[0], ids=f"{vector_id}")

    data = collection.get(include=['embeddings', 'documents'])
    print('--------------------------------------')
    print(data)
    print('--------------------------------------')

def search_vector_store(embedding):
    client = chromadb.PersistentClient()
    try :
        collection = client.get_collection(name="log_vector")
    except:
        collection = client.create_collection(name="log_vector")
    result = collection.query(embedding, n_results=5)
    print(result)
    return result

def delete_vector(vector_id):
    client = chromadb.PersistentClient()
    try :
        collection = client.get_collection(name="log_vector")
    except:
        collection = client.create_collection(name="log_vector")
    collection.delete(ids=[f'{vector_id}'])
    data = collection.get()
    print('--------------------------------------')
    print(data)
    print('--------------------------------------')