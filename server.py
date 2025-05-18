from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime
from typing import List
import sqlite3
import uuid
import hashlib

app = FastAPI()

conn = sqlite3.connect('test_results.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_results (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        test_name TEXT,
        score REAL,
        date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
''')
conn.commit()

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class TestResultCreate(BaseModel):
    test_name: str
    score: float

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str, role: str):
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    cursor.execute('INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)',
                   (user_id, username, password_hash, role))
    conn.commit()
    return user_id

def get_user_by_username(username: str):
    cursor.execute('SELECT id, username, password_hash, role FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    return row if row else None

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user or user[2] != hash_password(password):
        return None
    return user

def create_test_result(user_id: str, test_result: TestResultCreate):
    result_id = str(uuid.uuid4())
    date = datetime.now().isoformat()
    cursor.execute('INSERT INTO test_results (id, user_id, test_name, score, date) VALUES (?, ?, ?, ?, ?)',
                   (result_id, user_id, test_result.test_name, test_result.score, date))
    conn.commit()
    return result_id

def get_all_test_results():
    cursor.execute('''
        SELECT test_results.test_name, users.username, test_results.score, test_results.date 
        FROM test_results
        JOIN users ON test_results.user_id = users.id
    ''')
    return cursor.fetchall()

@app.post("/register")
async def register(user_create: UserCreate):
    if get_user_by_username(user_create.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    create_user(user_create.username, user_create.password, user_create.role)
    return {"message": "User created successfully"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": user[0], "token_type": "bearer"}

@app.post("/results")
async def save_test_result(result: TestResultCreate, token: str = Depends(oauth2_scheme)):
    cursor.execute('SELECT role FROM users WHERE id = ?', (token,))
    user = cursor.fetchone()
    if not user or user[0] != 'student':
        raise HTTPException(status_code=403, detail="Only students can save results")
    create_test_result(token, result)
    return {"message": "Result saved successfully"}

@app.get("/results", response_model=List[dict])
async def get_results(token: str = Depends(oauth2_scheme)):
    cursor.execute('SELECT role FROM users WHERE id = ?', (token,))
    user = cursor.fetchone()
    if not user or user[0] != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can view results")
    return [{"test_name": r[0], "username": r[1], "score": r[2], "date": r[3]} for r in get_all_test_results()]

@app.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    cursor.execute('SELECT username, role FROM users WHERE id = ?', (token,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user[0], "role": user[1]}