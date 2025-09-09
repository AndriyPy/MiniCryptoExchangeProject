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



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=1489)
