from fastapi import FastAPI
import psycopg2

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "API is working!"}
