import os
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders.parsers.pdf import PyPDFParser
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from langchain_core.documents.base import Blob
from langchain_core.prompts import PromptTemplate
from fastapi.staticfiles import StaticFiles


load_dotenv()

POSTGRES_CONNECTION = os.getenv("POSTGRES_CONNECTION")
if not POSTGRES_CONNECTION:
    raise ValueError("POSTGRES_CONNECTION environment variable is not set.")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.2)


vector_store = PGVector(
    connection=POSTGRES_CONNECTION,
    embeddings=embeddings,
    collection_name="legal_chunks",
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(SessionMiddleware, secret_key="RANDOM_SECRET_KEY")

templates = Jinja2Templates(directory="templates")

@app.get("/",response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile):
    document_id = str(uuid.uuid4())
    user_id = "demo_user"
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    request.session['document_id'] = document_id
    request.session['user_id'] = user_id

    file_location = f"uploaded_{file.filename}"

    with open(file_location, "wb") as f:
        f.write(await file.read())
    
    blob = Blob.from_path(file_location)
    parser = PyPDFParser()
    docs = list(parser.lazy_parse(blob))

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=30)

    chunks = text_splitter.split_documents(docs)

    chunk_docs = []
    for chunk in chunks:
        chunk_docs.append(
            chunk.model_copy(update={"metadata": {
                "document_id": document_id,
                "user_id": user_id}})
        )
    vector_store.add_documents(chunk_docs)

    summary_chunks = vector_store.similarity_search(
        "Summarize the deatiled overview of the document.",
        k=50,
        filter={"user_id": user_id, "document_id": document_id}
    )

    if not summary_chunks:
        raise HTTPException(status_code=404, detail="No relevant chunks found for summary.")

    summary_context = " ".join([doc.page_content for doc in summary_chunks])
    summary_template = PromptTemplate.from_template("""
        You are a helpful legal expert.
        Summarize the following legal document in a detailed overview.
        Your summary should be comprehensive and cover all key aspects.
        Do not include any personal opinions or interpretations.
        Use ONLY the following context. If you don't find enough info, say: "I don't know."

        Context:
        {context}
        """)
    summary_prompt = summary_template.format(context=summary_context)
    summary_response = llm.invoke(summary_prompt)
    if not summary_response:
        raise HTTPException(status_code=500, detail="Failed to generate summary.")

    return JSONResponse(content={
        "message": "File uploaded and processed successfully.",
        "document_id": document_id,
        "summary": summary_response.content
    })

@app.post("/query")
async def query(request: Request, query: str = Form(...)):
    user_id = request.session.get('user_id')
    document_id = request.session.get('document_id')

    if not user_id or not document_id:
        raise HTTPException(status_code=400, detail="Session expired or invalid.")

    results = vector_store.similarity_search(query, k=20, filter={"user_id": user_id, "document_id": document_id})

    if not results:
        return JSONResponse(content={"message": "No relevant chunks found."})

    context = " ".join([doc.page_content for doc in results])

    query_template = PromptTemplate.from_template("""
        You are a helpful legal expert.
        Answer the following question based on the provided context.
        Use ONLY the context provided. If you don't find enough info, say: "I don't know."

        Context:
        {context}

        Question:
        {question}
        """)
    query_prompt = query_template.format(context=context, question=query)
    response = llm.invoke(query_prompt)
    if not response:
        raise HTTPException(status_code=500, detail="Failed to generate response.")

    return JSONResponse(content={
        "message": "Query processed successfully.",
        "response": response.content,
        "context": context
    })

