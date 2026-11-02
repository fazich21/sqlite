
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

from auth import get_current_user, require_admin, router as auth_router

app = FastAPI()

# Adds /auth/register, /auth/login and /auth/me
app.include_router(auth_router)

# Authorization rules for documents:
#   - Logged-in users (any role) can READ and SEARCH documents.
#   - Only admins can CREATE, UPDATE and DELETE documents.

FILE_NAME = "data.json"


class Document(BaseModel):
    title: str
    content: str


# Read data from JSON file
def read_data():
    if not os.path.exists(FILE_NAME):
        return []

    with open(FILE_NAME, "r", encoding="utf-8") as file:
        return json.load(file)


# Save data to JSON file
def save_data(documents):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(documents, file, indent=4)


# CREATE a new document (admins only)
@app.post("/documents")
def create_document(document: Document, user: dict = Depends(require_admin)):
    documents = read_data()

    if documents:
        new_id = max(item["id"] for item in documents) + 1
    else:
        new_id = 1

    new_document = {
        "id": new_id,
        "title": document.title,
        "content": document.content
    }

    documents.append(new_document)
    save_data(documents)

    return {
        "message": "Document created successfully",
        "document": new_document
    }


# READ all documents
@app.get("/documents")
def get_documents(user: dict = Depends(get_current_user)):
    return read_data()


# SEARCH documents by title
@app.get("/documents/search")
def search_documents(title: str, user: dict = Depends(get_current_user)):
    documents = read_data()
    results = []

    for document in documents:
        if title.lower() in document["title"].lower():
            results.append(document)

    return {
        "search_query": title,
        "total_results": len(results),
        "documents": results
    }



# READ one document by ID
@app.get("/documents/{document_id}")
def get_document(document_id: int, user: dict = Depends(get_current_user)):
    documents = read_data()

    for document in documents:
        if document["id"] == document_id:
            return document

    raise HTTPException(
        status_code=404,
        detail="Document not found"
    )


# UPDATE a document (admins only)
@app.put("/documents/{document_id}")
def update_document(document_id: int, updated_document: Document, user: dict = Depends(require_admin)):
    documents = read_data()

    for document in documents:
        if document["id"] == document_id:
            document["title"] = updated_document.title
            document["content"] = updated_document.content

            save_data(documents)

            return {
                "message": "Document updated successfully",
                "document": document
            }

    raise HTTPException(
        status_code=404,
        detail="Document not found"
    )


# DELETE a document (admins only)
@app.delete("/documents/{document_id}")
def delete_document(document_id: int, user: dict = Depends(require_admin)):
    documents = read_data()

    for document in documents:
        if document["id"] == document_id:
            documents.remove(document)
            save_data(documents)

            return {
                "message": "Document deleted successfully",
                "document": document
            }

    raise HTTPException(
        status_code=404,
        detail="Document not found"
    )
