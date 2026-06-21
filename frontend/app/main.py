from fastapi import FastAPI

app = FastAPI(title="TF2Hub")

@app.get("/")
def read_root():
    return {"status": "TF2Hub API ativa!"}
