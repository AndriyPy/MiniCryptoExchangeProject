import uvicorn
from fastapi import FastAPI
from backand.database.database import create_db_and_tables
from backand.routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(router)


# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "null",
    "http://localhost:63342"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=1489)
