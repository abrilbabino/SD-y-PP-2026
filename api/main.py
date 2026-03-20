from fastapi import FastAPI
from TrabajoPractico1.Hit6.NodoD import router1
from TrabajoPractico1.Hit7.NodoD import router2


app = FastAPI()

app.include_router(router1)
app.include_router(router2)


@app.get("/")
def root():
    return {"message": "ok"}