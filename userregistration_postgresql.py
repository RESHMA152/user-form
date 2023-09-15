from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgres_db"

app = FastAPI()


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String, unique=True)

    profile = relationship("Profile", back_populates="owner")

class Profile(Base):
    __tablename__ = "Profiles"

    id = Column(Integer, primary_key=True, index=True)
    profile_picture = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="profile")

Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: str

@app.post("/register/")
async def register_user(user: UserCreate):
    db = SessionLocal()
    existing_user = db.query(User).filter_by(email=user.email).first() or db.query(User).filter_by(phone=user.phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.get("/user/{user_id}/")
async def get_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter_by(id=user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
