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
On Thu, 20 Apr 2023 15:00:00 -0400 No Nothing Very Sensitive (Shopify) <mailer@shopify.com> wrote ---


You received a new message from your online store's contact form.
Country Code:
US
Name:
Shawna Sahs
Email:
shawna.sahs@outlook.com
Phone Number:
402-490-2344
Comment:
I have a very strong and sensitive hairspray that is only spraying air and no product. I also have a very sensitive multispray that the sprayer won't work. It is the only one I have so I can't try another sprayer. Both of these are new even though I have had them a while. I order a lot at one time to save on shipping and to have product on hand. 

"""
get_context(msg)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
