import os
import openai
import dotenv

dotenv.load_dotenv()

words_per_review = 130

openai.api_key = os.getenv("OPENAI_API_KEY")

examples = """
  
"""

completion = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",
         "content": f"""
            Provide me 5 product reviews for hair conditioner.
            There should be more than {words_per_review} words per product review and all reviews should be unique and independent each other.
            Each review can be consist of several sentences but should be consist of more than {words_per_review} words.
            Below sentences are review examples for given hair conditioner that you have to create product reviews about.
            You can refer to these examples.
            {examples}
            Based on these examples please extract the features and advantages of this conditioner and provide good reviews.
        """
         }
    ]
)

print(completion)

with open("./data/reviews.txt", "w") as txt_file:
    txt_file.write(completion.choices[0].message["content"])
