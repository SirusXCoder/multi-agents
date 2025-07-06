import asyncio
import os
import platform
import locale
import sys
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import unicodedata
import re
import json
import openai

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

# Set locale to handle UTF-8 properly
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass  # Use default locale

# Function to clean text and remove problematic characters
def clean_text(text):
    """Clean text by removing or replacing problematic Unicode characters."""
    if not isinstance(text, str):
        return str(text)
    
    # Replace various problematic Unicode characters
    replacements = {
        '\u2014': '--',  # em dash
        '\u2013': '-',   # en dash
        '\u2019': "'",   # right single quotation mark
        '\u2018': "'",   # left single quotation mark
        '\u201c': '"',   # left double quotation mark
        '\u201d': '"',   # right double quotation mark
        '\u2026': '...',  # horizontal ellipsis
        '\u00a0': ' ',   # non-breaking space
        '\u00b7': '*',   # middle dot
        '\u2022': '*',   # bullet
        '\u2010': '-',   # hyphen
        '\u2011': '-',   # non-breaking hyphen
        '\u2012': '-',   # figure dash
        '\u2015': '--',  # horizontal bar
    }
    
    # Apply replacements
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Normalize Unicode to NFC form
    text = unicodedata.normalize('NFC', text)
    
    # Remove any remaining non-printable characters except common whitespace
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\t\n\r')
    
    # Ensure ASCII-safe encoding
    text = text.encode('ascii', errors='ignore').decode('ascii')
    
    return text.strip()

# Initialize Pinecone client
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index_name = "support-data"

# Delete and recreate index
if index_name in pc.list_indexes().names():
    pc.delete_index(index_name)
pc.create_index(
    name=index_name,
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

# Initialize embeddings and vectorstore with explicit encoding handling
embeddings = OpenAIEmbeddings(
    api_key=os.environ["OPENAI_API_KEY"],
    client=None,  # Let it use default client
    model="text-embedding-ada-002"
)
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=index_name, 
    embedding=embeddings
)

# Manual approach using direct API calls
def manual_add_documents(pc, index_name, documents):
    """Manually add documents using direct Pinecone API calls."""
    successful_count = 0
    
    # Get the index
    index = pc.Index(index_name)
    
    # Initialize OpenAI client with custom headers to avoid encoding issues
    import httpx
    
    # Create a custom HTTP client with UTF-8 handling
    http_client = httpx.Client(
        headers={
            "User-Agent": "python-openai/1.0.0"  # Simple ASCII user agent
        }
    )
    
    openai_client = openai.OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        http_client=http_client
    )
    
    for i, doc in enumerate(documents):
        try:
            # Clean the text content aggressively
            safe_content = clean_text(doc.page_content)
            # Double check - remove any non-ASCII characters
            safe_content = ''.join(c for c in safe_content if ord(c) < 128)
            
            if not safe_content.strip():
                print(f"Debug: Skipping empty document {i+1}")
                continue
            
            # Clean metadata
            safe_metadata = {}
            for key, value in doc.metadata.items():
                safe_key = ''.join(c for c in str(key) if ord(c) < 128)
                if isinstance(value, str):
                    safe_value = ''.join(c for c in value if ord(c) < 128)
                else:
                    safe_value = str(value)
                safe_metadata[safe_key] = safe_value
            
            print(f"Debug: Processing document {i+1}: {safe_content[:50]}...")
            
            # Get embeddings directly from OpenAI
            response = openai_client.embeddings.create(
                input=safe_content,
                model="text-embedding-ada-002"
            )
            
            embedding = response.data[0].embedding
            
            # Upsert to Pinecone directly
            vector_id = f"doc_{i+1}"
            index.upsert([
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "text": safe_content,
                        **safe_metadata
                    }
                }
            ])
            
            print(f"Debug: Successfully added document {i+1}: {safe_content[:50]}...")
            successful_count += 1
            
        except Exception as e:
            print(f"Debug: Failed to add document {i+1}: {e}")
            print(f"Debug: Document content: {doc.page_content[:100]}...")
            continue
    
    return successful_count

# Ingest data from CSV with validation and error handling
async def ingest_data(vectorstore):
    try:
        # Read CSV file with explicit encoding and error handling
        df = pd.read_csv("order_data.csv", encoding="utf-8", on_bad_lines="skip")
        print("Debug: Raw DataFrame:\n", df)

        # Validate and clean data
        documents = []
        for index, row in df.iterrows():
            if pd.isna(row["text"]) or not isinstance(row["text"], str):
                print(f"Debug: Skipping invalid row {index} with text: {row['text']}")
                continue
            try:
                metadata = eval(row["metadata"]) if pd.notna(row["metadata"]) else {}
                # Clean any string values in metadata
                cleaned_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, str):
                        cleaned_metadata[clean_text(key)] = clean_text(value)
                    else:
                        cleaned_metadata[clean_text(key)] = value
                metadata = cleaned_metadata
            except (SyntaxError, NameError):
                print(f"Debug: Skipping row {index} due to invalid metadata: {row['metadata']}")
                continue
            
            # Clean text content to handle encoding issues
            text_content = clean_text(row["text"])
            
            # Debug: Check for problematic characters in cleaned text
            try:
                text_content.encode('ascii')
                print(f"Debug: Text content is ASCII-safe: {text_content}")
            except UnicodeEncodeError as e:
                print(f"Debug: Text content still has encoding issues: {e}")
                print(f"Debug: Problematic text: {repr(text_content)}")
                # Force ASCII conversion
                text_content = text_content.encode('ascii', errors='ignore').decode('ascii')
            
            doc = Document(page_content=text_content, metadata=metadata)
            documents.append(doc)
            print(f"Debug: Processed document {index}: {doc.page_content}")

        if not documents:
            print("Error: No valid documents to ingest!")
            return

        # Upsert documents using manual approach to bypass encoding issues
        successful_count = manual_add_documents(pc, index_name, documents)
        print(f"Debug: Successfully ingested {successful_count}/{len(documents)} order documents")
        await asyncio.sleep(5)  # Ensure index updates
    except FileNotFoundError:
        print("Error: 'order_data.csv' not found in the current directory!")
    except pd.errors.ParserError as e:
        print(f"Error: CSV parsing failed: {str(e)}. Check file format and ensure no extra commas.")
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