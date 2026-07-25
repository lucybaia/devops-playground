from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Snippet
from app.schemas.schemas import SnippetCreate, SnippetResponse

router = APIRouter()


@router.get("/", response_model=list[SnippetResponse])
def list_snippets(db: Session = Depends(get_db)):
    return db.query(Snippet).order_by(Snippet.updated_at.desc()).all()


@router.post("/", response_model=SnippetResponse, status_code=201)
def create_snippet(data: SnippetCreate, db: Session = Depends(get_db)):
    snippet = Snippet(**data.model_dump())
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    return snippet


@router.get("/{snippet_id}", response_model=SnippetResponse)
def get_snippet(snippet_id: int, db: Session = Depends(get_db)):
    snippet = db.get(Snippet, snippet_id)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return snippet


@router.delete("/{snippet_id}", status_code=204)
def delete_snippet(snippet_id: int, db: Session = Depends(get_db)):
    snippet = db.get(Snippet, snippet_id)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    db.delete(snippet)
    db.commit()