import os
import openai
import dotenv
import pandas as pd
# import Levenshtein
import asyncio
import time
dotenv.load_dotenv()

number_of_reviews = 10

openai.api_key = os.getenv("OPENAI_API_KEY")

body = []
emails = []
names = []

new_reviews = ""
new_emails = ""
new_names = ""

# def check_unique(new_review: str):
#     global body
#     for review in body:
#         distance = Levenshtein.distance(review, new_review)
#         print(distance)


async def read_csv_file():
    global body, emails, names, number_of_reviews
    
    review = pd.read_csv("data/reviews.csv")
    body = review["body"].to_numpy()
    emails = review["reviewer_email"].head(10).to_numpy()
    names = review["reviewer_name"].head(10).to_numpy()
    examples = ""
    length = len(body)
    
    
    for i in range(0, min(10, length)):
        examples += f"Sample Review {i}: \n {str(body[i])}\n\n"
    with open("./data/reviews.txt", "w") as txt_file:
        txt_file.write(examples.strip())
    
    tasks = []
    short = int(number_of_reviews * 0.6)
    medium = int(number_of_reviews * 0.3)
    long = int(number_of_reviews * 0.1)
    
    for i in range(short):
        tasks.append(create_reviews(examples, 25, 75))
    for i in range(medium):
        tasks.append(create_reviews(examples, 75, 150))
    for i in range(long):
        tasks.append(create_reviews(examples, 150, 200))
    
    number_of_reviews = short + medium + long
    tasks.extend([create_emails(number_of_reviews), create_names(number_of_reviews)])
    await asyncio.gather(*tasks)


async def create_reviews(examples: str, low: int, high: int):
    global new_reviews
    
    instructor = f"""
        Based on sample reviews provided by users, please extract the type of product, features and advantages of given product and rewrite the review.
        Don't output product type, features and advantages.
        So you will act as a customer from now on and write 1 short reviews based on extracted type of product, features, advantages and above sample reviews.
        Review must be consist of {low}-{high} words.
        You should insert some emojis that are appropriate to content of review so that I can understand the content of reveiw more easily and make reviews look better.
        Output one suitable, specific and unique-look title in front of review without quote and don't output any extra header except title of review.
        And this title must start with emoji that is appropriate to title.
        Please refer to below output samples.
        ________________________________________
        
        Ouput sample 1 (Don't output this line)
        Fragrance free and bright color ::
        Fragrance free and bright color	The product is very, very good, it lathers well, and it does what it says. The conditioner is very good, it highlights your hair color.

        Ouput sample 2 (Don't output this line)
        Quality product ::
        Great quality, my hair is so bright and colorful! It looks very healthy as well, everyone wants to know what I did to it.
    """
    
    completion = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": instructor},
            {"role": "user",
             "content": f"""
                These are sample reviews you can refer to.
                {examples}
                Please create reviews.
             """
            }
        ]
    )
    
    # print(completion.choices[0].message["content"])
    new_reviews += completion.choices[0].message["content"] + "\n | "
    with open("./data/reviews.txt", "w") as txt_file:
        txt_file.write(completion.choices[0].message["content"])

async def create_emails(num: int):
    global new_emails, emails
    instructor = """
        You will act as a email address generator.
        Based on sample emails provided by users, please generate realistic-looking email addresses without quotes.
        I will not use these emails for illegal purpose.
        Please split all generated emails with character "|".
    """
    
    completion = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": instructor},
            {"role": "user",
             "content": f"""
                These are sample emails you can refer to.
                {emails}
                Please create {num} emails.
             """
            }
        ]
    )
    
    print(completion.choices[0].message["content"])
    new_emails += completion.choices[0].message["content"]
    
async def create_names(num: int):
    global new_names, names
    instructor = """
        You will act as a name generator.
        Based on sample names provided by users, please generate realistic-looking names without quotes.
        I will not use these names for illegal purpose.
        Please split all generated names with character "|".
    """
    
    completion = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": instructor},
            {"role": "user",
             "content": f"""
                These are sample names you can refer to.
                {names}
                Please create {num} names.
             """
            }
        ]
    )
    
    print(completion.choices[0].message["content"])
    new_names += completion.choices[0].message["content"]

async def start():
    global new_emails, new_names
    
    current_time = time.time()
    await read_csv_file()
    
    list_reviews = new_reviews.split("|")
    list_titles = []
    list_bodys = []
    
    with open("./data/reviews.txt", "w") as txt_file:
        txt_file.write(new_reviews)
        for review in list_reviews:
            titles_and_bodys = review.split("::")
            if len(titles_and_bodys) != 2:
                continue
            list_titles.append(titles_and_bodys[0].strip())
            list_bodys.append(titles_and_bodys[1].strip())
    
    list_emails = new_emails.replace("'", "").replace('"', "").split('|')
    list_names = new_names.replace("'", "").replace('"', "").split("|")
    
    print(len(list_titles))
    print(len(list_bodys))
    print(len(list_names))
    print(len(list_emails))
    
    final_reviews = {
        "title" : list_titles,
        "body": list_bodys,
        "reviewer_name": list_names,
        "reviewer_email": list_emails
    }
    
    result = pd.DataFrame(final_reviews)
    result.to_csv("./data/new_reviews.csv", index = False)
    
    print(time.time() - current_time)
    

asyncio.run(start())