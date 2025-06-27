import asyncio
import platform
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize components
embeddings = OpenAIEmbeddings(api_key=os.environ["OPENAI_API_KEY"])
vectorstore = PineconeVectorStore.from_existing_index(index_name="health-data", embedding=embeddings)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.environ["OPENAI_API_KEY"])


# Agents
class TriageAgent:
    def __init__(self, llm):
        self.llm = llm

    async def classify(self, query):
        prompt = ChatPromptTemplate.from_template(
            "Classify this query into 'fitness', 'nutrition', 'sleep', or 'general': {query}")
        chain = prompt | self.llm | StrOutputParser()
        return await chain.ainvoke({"query": query})


class RetrievalAgent:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore

    async def retrieve(self, query):
        embedded_query = await self.vectorstore._embedding.aembed_query(query)
        results = self.vectorstore.similarity_search(query, k=5, filter={
            "category": {"$in": [query.lower().split()[0] if query.lower().split() else "general"]}})
        if not results:
            results = self.vectorstore.similarity_search(query, k=5)  # Fallback
        return results


class ResponseAgent:
    def __init__(self, llm):
        self.llm = llm

    async def generate(self, query, context):
        context_text = "\n".join([doc.page_content for doc in context])
        prompt = ChatPromptTemplate.from_template("Respond to: {query} using context: {context}")
        chain = prompt | self.llm | StrOutputParser()
        return await chain.ainvoke({"query": query, "context": context_text or "No specific data available"})


# Main function
async def main():
    triage_agent = TriageAgent(llm)
    retrieval_agent = RetrievalAgent(vectorstore)
    response_agent = ResponseAgent(llm)

    # Example query (replace with user input as needed)
    #query = "How much exercise should I do weekly?"
    query = "What should I eat for a balanced diet?"

    category = await triage_agent.classify(query)
    context = await retrieval_agent.retrieve(query)
    response = await response_agent.generate(query, context)

    print(f"Category: {category}")
    print(f"Context: {context}")
    print(f"Response: {response}")


if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())