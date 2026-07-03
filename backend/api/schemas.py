from pydantic import BaseModel, Field 
from typing import Optional

# ---------------------------------
# Auth
# ---------------------------------

class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

    
# ---------------------------------
# Upload
# ---------------------------------

class UploadResponse(BaseModel):
    file_paths:list[str]
    file_names:list[str]
    count:int

# ---------------------------------
# Chat
# ---------------------------------

class ChatRequest(BaseModel):
    query:str=Field(..., min_length=1,max_length=10000)
    file_paths:list[str]=Field(default_factory=list)
    thread_id:Optional[str]=None

class ChatResponse(BaseModel):
    thread_id:str
    final_answer:str
    task:str

# ---------------------------------
# Stream events
# ---------------------------------

class StatusEvent(BaseModel):
    type:str="status"
    node:str
    message:str

class TokenEvent(BaseModel):
    type:str="token"
    content:str

class DoneEvent(BaseModel):
    type:str="done"
    thread_id:str
    task:str

class ErrorEvent(BaseModel):
    type:str="error"
    message:str


# ---------------------------------
# Reset
# ---------------------------------

class ResetRequest(BaseModel):
    thread_id:str

class ResetResponse(BaseModel):
    thread_id:str
    success:bool
    message:str