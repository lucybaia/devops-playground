from datetime import datetime

from pydantic import BaseModel


class SnippetCreate(BaseModel):
    title: str
    code: str
    language: str
    tags: str | None = ""
    description: str | None = ""


class SnippetResponse(BaseModel):
    id: int
    title: str
    code: str
    language: str
    tags: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
