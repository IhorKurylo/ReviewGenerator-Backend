from fastapi import FastAPI
import app.Routers.Review as Review
import app.Routers.Zoho as Zoho
from app.Utils.Zoho_mails import start

import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(Review.router, tags=["review"])
app.include_router(Zoho.router, tags=["zoho"])

# start()


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
