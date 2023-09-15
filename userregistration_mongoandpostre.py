from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pymongo import MongoClient
from typing import List

app = FastAPI()

DB_URL = "postgres_db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String)

mongo_client = MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["mydb"]
mongo_collection = mongo_db["profile_pictures"]

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    profile_picture_id: str

class UserDetail(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    profile_picture_url: str

@app.post("/register/", response_model=UserDetail)
async def register_user(user: UserCreate):
    db_user = SessionLocal().query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db = SessionLocal()
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    profile_picture_id = user.profile_picture_id
    profile_picture = mongo_collection.find_one({"_id": profile_picture_id})
    if not profile_picture:
        raise HTTPException(status_code=400, detail="Profile picture not found")

    
    user_detail = UserDetail(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        phone=db_user.phone,
        profile_picture_url=profile_picture.get("url", ""),
    )

    return user_detail

@app.get("/user/{user_id}", response_model=UserDetail)
async def get_user(user_id: str):
    db_user = SessionLocal().query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    
    profile_picture_id = db_user.id 
    profile_picture = mongo_collection.find_one({"_id": profile_picture_id})
    if not profile_picture:
        raise HTTPException(status_code=400, detail="Profile picture not found")

    
    user_detail = UserDetail(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        phone=db_user.phone,
        profile_picture_url=profile_picture.get("url", ""),
    )

    return user_detail
