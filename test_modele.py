"""Test si BGE-M3 est vraiment chargé et fonctionne."""
from sentence_transformers import SentenceTransformer
import numpy as np

print("Chargement du modèle BGE-M3...")
modele = SentenceTransformer("BAAI/bge-m3")

# Test sémantique de base
requete = "message insultant"
doc1 = "nique la police"
doc2 = "bonne nuit"

print(f"\nRequête: '{requete}'")
print(f"Doc1: '{doc1}'")
print(f"Doc2: '{doc2}'")

# Encoder
emb_req = modele.encode([requete], normalize_embeddings=True)[0]
emb_doc1 = modele.encode([doc1], normalize_embeddings=True)[0]
emb_doc2 = modele.encode([doc2], normalize_embeddings=True)[0]

# Similarité cosine
sim1 = np.dot(emb_req, emb_doc1)
sim2 = np.dot(emb_req, emb_doc2)

print(f"\nSimilarite '{requete}' <-> '{doc1}': {sim1:.3f}")
print(f"Similarite '{requete}' <-> '{doc2}': {sim2:.3f}")

if sim1 > sim2:
    print(f"\nCORRECT: '{doc1}' est plus proche de '{requete}'")
else:
    print(f"\nPROBLEME: Le modele ne fonctionne pas correctement")

print(f"\nDimensions: {modele.get_sentence_embedding_dimension()}")
print(f"Modèle chargé: {modele._modules['0'].auto_model.config.name_or_path}")

