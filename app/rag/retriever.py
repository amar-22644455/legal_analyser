# src/retriever.py
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EMBEDDINGS_DIR = os.path.join(PROJECT_ROOT, "embeddings")

class Retriever:
    def __init__(self):
        try:
            # 🔄 LOAD THE NEW MASTER DICTIONARY
            with open(os.path.join(EMBEDDINGS_DIR, "document_data.pkl"), "rb") as f:
                self.document_data = pickle.load(f)
        except FileNotFoundError as e:
            raise Exception(f"Embedding file not found. Run embeddings generation first: {str(e)}")
        
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def retrieve(self, query, top_k=10, source_filter=None, group_by_file=False):
        query_emb = self.model.encode([query])
        
        # -------- MODE 1: SINGLE DOCUMENT SEARCH (Used for Query & Compare) --------
        if source_filter:
            if source_filter not in self.document_data:
                print(f"Warning: {source_filter} not found in database.")
                return []
            
            # Isolate just this specific file's data
            doc_info = self.document_data[source_filter]
            scores = cosine_similarity(query_emb, doc_info["embeddings"])[0]
            
            # Get the top chunks for this specific file
            local_top_k = min(top_k, len(scores))
            top_indices = np.argsort(scores)[::-1][:local_top_k]
            
            results = []
            for i in top_indices:
                meta = doc_info["metadata"][i].copy()
                meta["source"] = source_filter
                results.append({
                    "chunk": doc_info["chunks"][i],
                    "source": meta,
                    "score": float(scores[i])
                })
            return results

        # -------- MODE 2: SUMMARY SEARCH (Used for UI Dashboard loading) --------
        elif group_by_file:
            grouped_results = {}
            
            # Iterate through EVERY file, and get the top_k for each one independently
            for filename, doc_info in self.document_data.items():
                scores = cosine_similarity(query_emb, doc_info["embeddings"])[0]
                
                local_top_k = min(top_k, len(scores))
                top_indices = np.argsort(scores)[::-1][:local_top_k]
                
                file_results = []
                for i in top_indices:
                    meta = doc_info["metadata"][i].copy()
                    meta["source"] = filename
                    file_results.append({
                        "chunk": doc_info["chunks"][i],
                        "source": meta,
                        "score": float(scores[i])
                    })
                
                # Store the results under the filename key
                grouped_results[filename] = file_results
                
            return grouped_results

        # -------- MODE 3: GLOBAL CHATBOT SEARCH --------
        else:
            all_scores = []
            all_chunks = []
            all_meta = []
            
            # Pool all chunks from all files together
            for filename, doc_info in self.document_data.items():
                scores = cosine_similarity(query_emb, doc_info["embeddings"])[0]
                
                for i, score in enumerate(scores):
                    meta = doc_info["metadata"][i].copy()
                    meta["source"] = filename
                    all_scores.append(score)
                    all_chunks.append(doc_info["chunks"][i])
                    all_meta.append(meta)
            
            if not all_scores:
                return []
                
            all_scores = np.array(all_scores)
            
            # Sort globally to find the absolute best chunks across the whole database
            top_indices = np.argsort(all_scores)[::-1][:top_k]
            
            results = []
            for i in top_indices:
                results.append({
                    "chunk": all_chunks[i],
                    "source": all_meta[i],
                    "score": float(all_scores[i])
                })
            return results