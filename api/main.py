from fastapi import FastAPI
from TrabajoPractico1.Hit6.NodoD import router1


app = FastAPI()

app.include_router(router1)



@app.get("/")
def root():
    return {"message": "ok"}