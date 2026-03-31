from fastapi import FastAPI
from TrabajoPractico1.Hit6.NodoD import router1
from TrabajoPractico2.Hit1.server import router2
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router1)
app.include_router(router2)


@app.get("/")
def root():
    return {"message": "ok"}