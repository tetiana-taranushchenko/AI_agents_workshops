"""
RAG Setup — YOUR FILE
======================

Set up a vector store knowledge base from coding standards documents.

Steps:
1. Load documents from knowledge_base/ folder
2. Split them into chunks
3. Create embeddings and store in a vector database
4. Create a retriever tool for the agent
"""

from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import KNOWLEDGE_BASE_PATH

load_dotenv()


# ============================================================
# Step 1: Load documents
# ============================================================

loader = DirectoryLoader(
    str(KNOWLEDGE_BASE_PATH),
    glob="*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
)
docs = loader.load()


# ============================================================
# Step 2: Split into chunks
# ============================================================

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)


# ============================================================
# Step 3: Create vector store
# ============================================================

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


# ============================================================
# Step 4: Create RAG tool
# ============================================================

@tool
def search_knowledge_base(query: str) -> str:
    """Search the coding standards knowledge base.
    Use this to find best practices, code review rules, and testing guidelines.

    Args:
        query: What to search for (e.g., "naming conventions", "error handling", "test coverage")
    """
    results = retriever.invoke(query)
    if not results:
        return "No relevant standards found."
    return "\n\n---\n\n".join(doc.page_content for doc in results)


# ============================================================
# Step 5: Test it!
# ============================================================
# Run this file directly to check that RAG works:
#   uv run python rag.py

if __name__ == "__main__":
    print(f"Loaded {len(docs)} documents")
    print(f"Split into {len(chunks)} chunks")
    print(f"Vector store ready")
    print(f"\n--- Test search: 'error handling' ---\n")
    print(search_knowledge_base.invoke("error handling"))
