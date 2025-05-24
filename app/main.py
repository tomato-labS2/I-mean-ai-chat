from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "I mean chat is running!"}