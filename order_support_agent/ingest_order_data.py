import asyncio
import os
import platform
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Initialize embeddings and vectorstore
embeddings = OpenAIEmbeddings(api_key=os.environ["OPENAI_API_KEY"])
vectorstore = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)

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
            except (SyntaxError, NameError):
                print(f"Debug: Skipping row {index} due to invalid metadata: {row['metadata']}")
                continue
            doc = Document(page_content=row["text"].strip(), metadata=metadata)
            documents.append(doc)
            print(f"Debug: Processed document {index}: {doc.page_content}")

        if not documents:
            print("Error: No valid documents to ingest!")
            return

        # Upsert documents to vectorstore
        await vectorstore.aadd_documents(documents)
        print(f"Debug: Ingested {len(documents)} order documents")
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