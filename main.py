from fastapi import FastAPI
import app.Routers.Review as Review
import app.Routers.Zoho as Zoho
from app.Utils.Get_email_content import start
from app.Utils.Pinecone import get_context
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
msg="""
You received a new message from your online store's contact form.
Country Code:
US
Name:
Amy Bates
Email:
amyhbates@gmail.com
Phone Number:
9194140474
Comment:
I have a 6.8 oz bottle of Do Nothing Very Sensitive & Strong Mousse which I have loved. It is a great product. 
I can feel the can is still very full and yet when I push down the top nozzle, no foam. Nothing comes out except a little drip. I want more, but this is a malfunction that makes me wonder about ordering again.  The numbers in pink on the bottom of the can I have are 13:59.   20106. 
Can you help? 
Thank you.
Amy Bates
"""
get_context(msg)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
