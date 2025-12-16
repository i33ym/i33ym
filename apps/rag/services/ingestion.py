from django.conf import settings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from apps.rag.models import IngestionLog


CONNECTION_STRING = (
    f"postgresql+psycopg://{settings.DATABASES['default']['USER']}:"
    f"{settings.DATABASES['default']['PASSWORD']}@"
    f"{settings.DATABASES['default']['HOST']}:"
    f"{settings.DATABASES['default']['PORT']}/"
    f"{settings.DATABASES['default']['NAME']}"
)

COLLECTION_NAME = "multicard_docs"


def get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY
    )


def get_vector_store():
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )


def ingest_documents(docs_path: str, clear_existing: bool = False):
    vector_store = get_vector_store()
    
    if clear_existing:
        vector_store.delete_collection()
        vector_store = get_vector_store()
    
    loader = DirectoryLoader(
        docs_path,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    chunks = splitter.split_documents(documents)
    
    vector_store.add_documents(chunks)
    
    IngestionLog.objects.create(
        source=docs_path,
        chunks_count=len(chunks)
    )
    
    return len(chunks)