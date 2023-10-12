import os
import openai
import dotenv
import pandas as pd
# import Levenshtein
import chardet
import asyncio
import time
import random
from datetime import datetime, timedelta


dotenv.load_dotenv()

number_of_reviews = 50
openai.api_key = os.getenv("OPENAI_API_KEY")
unit = 6
long_unit = 3

body = []
emails = []
names = []
titles = []
keywords_to_focus_on = ""
products_list = []
products_percent = 30


new_reviews = ""
new_emails = ""
new_names = ""
new_rates = []
total_tokens = 0

# def check_unique(new_review: str):
#     global body
#     for review in body:
#         distance = Levenshtein.distance(review, new_review)
#         print(distance)


def init():
    global new_reviews, new_emails, new_names, total_tokens, new_rates
    new_reviews = ""
    new_emails = ""
    new_names = ""
    new_rates = []
    total_tokens = 0


def clean(content: str):
    return content.replace('"', "").strip()


def str2date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%d")


def choose_rate(rate: list):
    percent = sum(rate)
    rand = random.randint(1, percent)
    for i in range(0, 6):
        if rand <= sum(rate[:(i+1)]):
            return i


async def read_csv_file(filename: str, rate: list):
    global body, emails, names, titles, unit, long_unit

    print("here1")
    with open(f"data/{filename}", 'rb') as f:
        result = chardet.detect(f.read())  # or readline if the file is large
        print(result['encoding'])

    review = pd.read_csv(f"data/{filename}", encoding=result['encoding'])
    titles = review["title"].head(5).to_numpy()
    body = review["body"].to_numpy()
    emails = review["reviewer_email"].head(10).to_numpy()
    names = review["reviewer_name"].head(5).to_numpy()
    examples = ""
    length = len(body)

    for i in range(0, min(5, length)):
        examples += f"Sample Review {i}: \n {str(body[i])}\n\n"
    with open("./data/reviews.txt", "w") as txt_file:
        txt_file.write(examples.strip())

    tasks = []
    medium = int(number_of_reviews * 0.3 / unit)
    long = int(number_of_reviews * 0.2 / long_unit)
    short = int((number_of_reviews - medium*unit -
                long*long_unit - 1) / unit + 1)

    for i in range(long):
        current_rate = choose_rate(rate)
        tasks.append(create_reviews(
            examples, 100, 150, current_rate, True))
        print("long: ", current_rate)
        print("long: ", current_rate)
    for i in range(medium):
        current_rate = choose_rate(rate)
        tasks.append(create_reviews(
            examples, 30, 75, current_rate))
        print("medium: ", current_rate)
        print("medium: ", current_rate)
    for i in range(short):
        current_rate = choose_rate(rate)
        tasks.append(create_reviews(
            examples, 25, 30, current_rate))
        print("short: ", current_rate)
        print("short: ", current_rate)

    print(short, medium, long)
    tasks.extend([create_emails(number_of_reviews),
                 create_names(number_of_reviews)])
    await asyncio.gather(*tasks)


async def create_reviews(examples: str, low: int, high: int, current_rate: int, is_long: bool = False):
    global new_reviews, total_tokens, new_rates, products_list
    threshold = 10 * products_percent / 100
    rand = random.randint(1, 10)
    product_prompt = ""
    if rand <= threshold:
        product_name = random.choice(products_list)
        print("product_name: ", product_name)
        product_prompt = f"{product_name} is name of product. You have to write the review of this product'. Review should contain exact name of this product."
        print(product_prompt)
    emoji_prompt = "Then insert emoji suitable for whole meaning of reviews, not for meaning of one word at the front of some words of review but that words shouldn't be the last word of any sentences." if random.randint(
        1, 5) == 3 else ""
    print(emoji_prompt)
    current_unit = unit
    if is_long:
        current_unit = long_unit
    instructor = f"""
        {product_prompt}
        Each review contains {low}-{high} words.
        You have to write {current_unit} reviews rating of {current_rate} stars, so your final output should contain {low*current_unit}-{high*current_unit} words.
        0 means very poor review, 1 or 2 rates mean bad, 3 means not bad and not good(normal), 4 means good and 5 means excellent.
        More stars means better review.
        Write {current_unit} reviews based on user provided sample reviews below.
        When you write reviews, you must focus on one of below topics.
        topics: {keywords_to_focus_on}
        {emoji_prompt}
        I hope also some of the reviews to write about how products are good for users.
        And I hope some reivews to have a bit grammer or spell errors like human-written-reviews.
        Don't forget that each review should contain {low}-{high} words.
        Based on generated reviews, you will generate attention-grabbing title seems like human written.
        Split title and content of each review with "/" like sample format.
        Please split {current_unit} reviews with character '|'.
        ----------------
        Sample Format(don't output this line)
        A Magical Change /
        I was looking for something to ✨ boost the color of my hair.
        | (This is character that is split reviews. Remember this!)
        Hydrated colored hair /
        Very easy to use, it lathers very quickly.
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
                Don't forget to split {current_unit} reviews with character '|'.
             """
             }
        ]
    )
    total_tokens += completion.usage["total_tokens"]
    new_reviews += completion.choices[0].message["content"] + "\n |"
    new_rates += [current_rate] * current_unit
    with open("./data/reviews.txt", "w") as txt_file:
        txt_file.write(completion.choices[0].message["content"])


async def create_emails(num: int):
    global new_emails, emails, total_tokens
    instructor = """
        You will act as a email address generator.
        Based on sample emails provided by users, please generate realistic-looking email addresses without "'".
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
    total_tokens += completion.usage["total_tokens"]
    # print(completion.choices[0].message["content"])
    new_emails += completion.choices[0].message["content"]


def regenerate_title(len, list_titles):
    emoji_prompt = f"Then insert emojis at the front of some words of title that is suitable to whole meaning of title for only {len/5} titles but that words shouldn't be the first or last word of any title."
    sample_title = '\n'.join(str(title) for title in titles)
    list_title = '\n'.join(str(title) for title in list_titles)
    print(sample_title)
    instructor = f"""
        These are titles you can refer to that is very similar to human-written.
        {sample_title}
        Based on above title samples, rewrite {len} of user provided titles below so that all titles are completely different each other.
        These are {len} of titles you should rewrite.
        {list_title}
        Almost every words should start with lowercase letters except only 0 or 1 or 2 words you want to emphasize to should be all uppercase letters.
        It is very important that all the titles' should have different capitalization each other.
        There shouldn't be two titles that have same capitalization stucture each other as possible as you can.
        Please keep the title concise and under 20 words without quotes, and ensure that the meaning is maintained.
        {emoji_prompt}
        Split generated titles with character "|".
        -------
        Sample Format
        Elevate ✨your hue | elevate Your hue
    """
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": instructor},
            {"role": "user",
             "content": f"""
                Don't forget to split generated titles with character "|".
             """
             }
        ]
    )
    # print(completion.choices[0].message["content"])
    return completion.choices[0].message["content"]


async def create_names(num: int):
    global new_names, names, total_tokens
    instructor = """
        You will act as a name generator.
        Based on sample names provided by users, please generate realistic-looking names without "'".
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
    total_tokens += completion.usage["total_tokens"]
    # print(completion.choices[0].message["content"])
    new_names += completion.choices[0].message["content"]


def generate_dates(num: int, start_date, end_date):
    result = []
    for i in range(num):
        random_number_of_days = random.randrange((end_date - start_date).days)
        result.append(
            (start_date + timedelta(random_number_of_days)).strftime("%Y-%m-%d"))
    return result


async def start(reviewCount: int, rate: int, From: str, To: str, keywords: str, products: str, percent: int, filename: str):
    global new_emails, new_names, number_of_reviews, rating_right, keywords_to_focus_on, products_list, products_percent
    number_of_reviews = reviewCount
    keywords_to_focus_on = keywords
    products_list = clean(products).split(',')
    products_percent = percent
    print("products_list: ", products_list)
    current_time = time.time()
    init()
    await read_csv_file(filename, rate)

    list_reviews = new_reviews.split("|")
    list_titles = []
    list_bodys = []

    with open("./data/reviews.txt", "w") as txt_file:
        txt_file.write(new_reviews)
    for review in list_reviews:
        titles_and_bodys = review.split("/")
        if len(titles_and_bodys) < 2:
            continue
        # print(clean(titles_and_bodys[0]),
        #       "-----", clean(titles_and_bodys[1]))
        list_titles.append(clean(titles_and_bodys[0]))
        list_bodys.append(clean(titles_and_bodys[1]))

    list_emails = clean(new_emails).split('|')
    list_names = clean(new_names).split('|')
    # print(len(list_emails))
    # print(len(list_names))
    print("list_titles0: ", len(list_titles))
    print("total_tokens: ", total_tokens)

    list_titles = regenerate_title(
        len(list_titles), '\n'.join(list_titles)).split('|')

    print("list_titles: ", len(list_titles))
    print("list_bodys: ", len(list_bodys))

    min_len = min(len(list_titles), len(list_bodys),
                  len(list_names), len(list_emails), number_of_reviews)
    print(min_len)

    list_titles = list_titles[:min_len]
    list_bodys = list_bodys[:min_len]
    list_names = list_names[:min_len]
    list_emails = list_emails[:min_len]
    list_rates = new_rates[:min_len]
    list_dates = generate_dates(min_len, str2date(From), str2date(To))

    reveiws_to_return = []
    for i in range(min_len):
        reveiws_to_return.append({"title": list_titles[i], "body": list_bodys[i], "reviewRating": list_rates[i],
                                 "date": list_dates[i], "reviewerName": list_names[i].replace("'", ""), "reviewerEmail": list_emails[i].replace("'", "")})

    print("total_tokens: ", total_tokens)
    print(time.time() - current_time)

    return reveiws_to_return
