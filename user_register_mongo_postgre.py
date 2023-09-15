from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
import motor.motor_asyncio


app = FastAPI()

DATABASE_URL = ""
pool = None
MONGODB_URL = "mongodb://localhost:27017"
mongo_client = None

async def create_tables_collections():
    global pool, mongo_client
    
    pool = await asyncpg.create_pool(DATABASE_URL)   # PostgreSQL
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT NOT NULL
        )
        """)
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)              #MongoDB
    db = mongo_client["profile_pictures"]
    await db.create_collection("user_profiles", capped=True, size=10000000)

class UserRegistration(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    profile_picture: str

@app.post("/register")
async def register_user(user: UserRegistration):
    async with pool.acquire() as conn:
       
        existing_user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")

        query = "INSERT INTO users (name, email, password, phone) VALUES ($1, $2, $3, $4) RETURNING user_id"
        user_id = await conn.fetchval(query, user.name, user.email, user.password, user.phone)

    db = mongo_client["profile_pictures"]
    collection = db["user_profiles"]
    await collection.insert_one({"user_id": user_id, "profile_picture": user.profile_picture})

    return {"message": "User registered successfully"}

@app.get("/user/{user_id}")
async def get_user_details(user_id: int):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if user:
            return {
                "user_id": user['user_id'],
                "name": user['name'],
                "email": user['email'],
                "phone": user['phone']
            }
        else:
            raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    import uvicorn
    import asyncio
    asyncio.run(create_tables_collections())
    uvicorn.run(app, host="0.0.0.0", port=8000)
