import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime

from database import create_document, get_documents, db
from schemas import User as UserSchema, BlogPost as BlogPostSchema, ContactMessage as ContactMessageSchema
import hashlib

app = FastAPI(title="SaaS Landing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Utility ----------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------- Models (Requests/Responses) ----------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class BlogOut(BaseModel):
    title: str
    slug: str
    summary: Optional[str] = None
    content: str
    author: str
    tags: List[str] = []
    published: bool = True
    published_at: Optional[datetime] = None

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: Optional[str] = None
    message: str


# ---------- Root & Health ----------

@app.get("/")
def read_root():
    return {"message": "SaaS Landing API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# ---------- Auth ----------

@app.post("/api/auth/register")
def register(payload: RegisterRequest):
    # Check if user exists
    existing = get_documents("user", {"email": payload.email}, limit=1)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = UserSchema(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        avatar_url=None,
        is_active=True,
    )
    user_id = create_document("user", user_doc)
    return {"ok": True, "user_id": user_id}

@app.post("/api/auth/login")
def login(payload: LoginRequest):
    users = get_documents("user", {"email": payload.email}, limit=1)
    if not users:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = users[0]
    if user.get("password_hash") != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Simple session-less auth response
    return {"ok": True, "name": user.get("name"), "email": user.get("email")}


# ---------- Blog ----------

@app.get("/api/blogs", response_model=List[BlogOut])
def list_blogs():
    posts = get_documents("blogpost", {"published": True})
    if not posts:
        # Seed a couple of example posts if none exist
        examples = [
            BlogPostSchema(
                title="Launching our pastel fintech platform",
                slug="launching-pastel-fintech",
                summary="A soft, modern take on digital banking.",
                content="We are excited to introduce a gentle, human fintech experience...",
                author="Team",
                tags=["announcement", "fintech"],
                published=True,
                published_at=datetime.utcnow(),
            ),
            BlogPostSchema(
                title="How we price simply and fairly",
                slug="simple-fair-pricing",
                summary="Transparent plans that scale with you.",
                content="No hidden fees. Just clear tiers designed for growth...",
                author="Team",
                tags=["pricing", "product"],
                published=True,
                published_at=datetime.utcnow(),
            ),
        ]
        for ex in examples:
            create_document("blogpost", ex)
        posts = get_documents("blogpost", {"published": True})

    # Map Mongo docs to response model
    result: List[BlogOut] = []
    for p in posts:
        result.append(BlogOut(
            title=p.get("title"),
            slug=p.get("slug"),
            summary=p.get("summary"),
            content=p.get("content"),
            author=p.get("author"),
            tags=p.get("tags", []),
            published=p.get("published", True),
            published_at=p.get("published_at")
        ))
    return result


# ---------- Contact ----------

@app.post("/api/contact")
def contact(payload: ContactRequest):
    msg = ContactMessageSchema(
        name=payload.name,
        email=payload.email,
        subject=payload.subject,
        message=payload.message,
    )
    doc_id = create_document("contactmessage", msg)
    return {"ok": True, "message": "Thanks for reaching out! We'll get back to you soon.", "id": doc_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
