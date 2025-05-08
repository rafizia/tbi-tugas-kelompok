import ir_datasets
from elasticsearch import Elasticsearch, helpers
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_es_index(es_client, index_name=os.getenv("INDEX_NAME", "msmarco_passages")):
    mapping = {
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "text": {
                    "type": "text",
                    "analyzer": "english",
                    "similarity": "my_bm25",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256}
                    }
                },
                "msmarco_document_id": {"type": "keyword"},
                "doc_length": {"type": "integer", "doc_values": True},
                "word_count": {"type": "short", "doc_values": True},
                "vector_embedding": {
                    "type": "dense_vector",
                    "dims": 384,  # For sentence-transformers models
                    "index": True,
                    "similarity": "cosine"
                }
            }
        },
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 0,  # For development
            "refresh_interval": "30s",
            "similarity": {  # BM25 parameters
                "my_bm25": {
                    "type": "BM25",
                    "b": 0.75,      # field-length normalization (Elasticsearch default)
                    "k1": 1.2       # term frequency scaling  (Elasticsearch default)
                }
            }
        }
    }

    if es_client.indices.exists(index=index_name):
        es_client.indices.delete(index=index_name)
    es_client.indices.create(index=index_name, body=mapping)
    print(f"Created index: {index_name}")

def count_words(text):
    """Count the number of words in a text"""
    return len(text.split())

def index_msmarco_passages(es_client, batch_size=200, max_passages=1000000, index_name=None):
    """Index MS MARCO passages in batches"""
    # Environment variables
    if index_name is None:
        index_name = os.getenv("INDEX_NAME", "msmarco_passages-v2")
    
    max_passages_env = os.getenv("MAX_PASSAGES")
    if max_passages_env:
        max_passages = int(max_passages_env)
    
    # Load the dataset
    dataset = ir_datasets.load("msmarco-passage-v2")
    
    # Check if index exists, create if not
    if not es_client.indices.exists(index=index_name):
        create_es_index(es_client, index_name)
    
    # Initialize counters
    total_indexed = 0
    current_batch = []
    failed_batches = 0
    
    print("Beginning indexing process...")
    
    # Iterate through documents
    for doc in dataset.docs_iter():
        # Calculate document length metrics
        char_length = len(doc.text)
        word_count = count_words(doc.text)
        
        # Create document for indexing
        es_doc = {
            "_index": index_name,
            "_id": doc.doc_id,
            "_source": {
                "doc_id": doc.doc_id,
                "text": doc.text,
                "msmarco_document_id": doc.msmarco_document_id,
                "doc_length": char_length,
                "word_count": min(word_count, 32767)  # Add word count, capped at Short max value
            }
        }
        
        current_batch.append(es_doc)
        
        # Process batch when it reaches the specified size
        if len(current_batch) >= batch_size:
            try:
                success, failed = helpers.bulk(es_client, current_batch, stats_only=True)
                total_indexed += success
                current_batch = []
                
                # Print progress more frequently
                if total_indexed % 10000 == 0:
                    print(f"Indexed {total_indexed} passages")
                
                # Stop if we've reached the maximum number of passages
                if max_passages and total_indexed >= max_passages:
                    break
            except Exception as e:
                failed_batches += 1
                print(f"Error indexing batch: {str(e)}")
                print(f"Failed batches so far: {failed_batches}")
                current_batch = []
    
    # Index any remaining documents
    if current_batch:
        try:
            success, failed = helpers.bulk(es_client, current_batch, stats_only=True)
            total_indexed += success
        except Exception as e:
            print(f"Error indexing final batch: {str(e)}")
    
    print(f"Indexing complete. Total indexed: {total_indexed} passages")
    if failed_batches > 0:
        print(f"Warning: {failed_batches} batches failed during indexing")
    return total_indexed

if __name__ == "__main__":
    # Get Elasticsearch host from environment variables, default to localhost:9200 (my local server port, change if needed)
    es_host = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
    
    # Get batch size from environment variables or use default
    batch_size = int(os.getenv("BATCH_SIZE", "1000"))
    
    try:
        es = Elasticsearch(
            es_host,
            retry_on_timeout=True,
            max_retries=5,
            request_timeout=60
        )
        
        # Check connection
        if not es.ping():
            print(f"Failed to connect to Elasticsearch")
            sys.exit(1)
        
        print(f"Connected to Elasticsearch at {es_host}")
    except Exception as e:
        print(f"Elasticsearch connection error: {str(e)}")
        sys.exit(1)
    
    # Use parameters from environment variables
    index_msmarco_passages(
        es, 
        batch_size=batch_size,
        # max_passages will be read from environment variable in the function
    )