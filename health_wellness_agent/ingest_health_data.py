import asyncio
import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import platform
import sys
import locale
import unicodedata
import re

# Load environment variables
load_dotenv()

# Monkey-patch httpx to handle encoding issues in headers
import httpx._models
original_normalize = httpx._models._normalize_header_value

def patched_normalize_header_value(value, encoding=None):
    """Patched version that handles Unicode characters gracefully."""
    if isinstance(value, str):
        # Replace problematic Unicode characters
        value = value.replace('\u2014', '--')  # em dash
        value = value.replace('\u2013', '-')   # en dash
        value = value.replace('\u2019', "'")   # right single quotation mark
        value = value.replace('\u201c', '"')   # left double quotation mark
        value = value.replace('\u201d', '"')   # right double quotation mark
        # Remove any remaining non-ASCII characters
        value = ''.join(c for c in value if ord(c) < 128)
    return original_normalize(value, encoding)

httpx._models._normalize_header_value = patched_normalize_header_value

# Set up proper encoding environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['LANG'] = 'en_US.UTF-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize Pinecone client
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index_name = "health-data"

# Delete and recreate index
if index_name in pc.list_indexes().names():
    pc.delete_index(index_name)
pc.create_index(
    name=index_name,
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

# Initialize embeddings and vectorstore
embeddings = OpenAIEmbeddings(api_key=os.environ["OPENAI_API_KEY"])
vectorstore = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)

# Ingest data from CSV with validation and correction
async def ingest_data(vectorstore):
    try:
        # Read CSV file with explicit delimiter and error handling
        df = pd.read_csv("health_data.csv", encoding="utf-8", on_bad_lines="skip")
        print("Debug: Raw DataFrame:\n", df)

        # Clean and validate data
        documents = []
        for index, row in df.iterrows():
            # Handle potential split content
            content_parts = [str(row["content"]).strip()]
            if pd.notna(row.get("content_1", None)):  # Check for additional columns
                content_parts.append(str(row["content_1"]).strip())
            content = " ".join(filter(None, content_parts))

            if not content or not isinstance(content, str):
                print(f"Debug: Skipping invalid row {index} with content: {content}")
                continue
            if pd.isna(row["category"]) or not isinstance(row["category"], str):
                print(f"Debug: Skipping row {index} due to invalid category: {row['category']}")
                continue
            doc = Document(page_content=content, metadata={"category": row["category"].strip()})
            documents.append(doc)
            print(f"Debug: Processed document {index}: {doc.page_content}")

        if not documents:
            print("Error: No valid documents to ingest!")
            return

        # Upsert documents to vectorstore
        await vectorstore.aadd_documents(documents)
        print(f"Debug: Ingested {len(documents)} health documents")
        await asyncio.sleep(5)  # Ensure index updates
    except FileNotFoundError:
        print("Error: 'health_data.csv' not found in the current directory!")
    except pd.errors.ParserError as e:
        print(f"Error: CSV parsing failed: {str(e)}. Check file format.")
    except Exception as e:
        print(f"Error during ingestion: {str(e)}")

# Main function
async def main():
    await ingest_data(vectorstore)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())