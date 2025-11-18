"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogpost" collection
- ContactMessage -> "contactmessage" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    """Auth users collection schema
    Collection: "user"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Hashed password")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    is_active: bool = Field(True, description="Whether user is active")

class BlogPost(BaseModel):
    """Blog posts schema
    Collection: "blogpost"
    """
    title: str = Field(...)
    slug: str = Field(..., description="URL-friendly slug")
    summary: Optional[str] = Field(None)
    content: str = Field(...)
    author: str = Field(...)
    tags: List[str] = Field(default_factory=list)
    published: bool = Field(default=True)
    published_at: Optional[datetime] = Field(None)

class ContactMessage(BaseModel):
    """Contact form submissions
    Collection: "contactmessage"
    """
    name: str
    email: EmailStr
    subject: Optional[str] = None
    message: str
