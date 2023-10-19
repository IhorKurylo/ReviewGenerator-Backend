from langchain.schema import Document
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import CSVLoader, PyPDFLoader, TextLoader, Docx2txtLoader
import nltk
import re

from dotenv import load_dotenv
import os
import pinecone
import openai
import tiktoken
import time
# from pinecone import Index

load_dotenv()
tokenizer = tiktoken.get_encoding('cl100k_base')

api_key = os.getenv('PINECONE_API_KEY')

pinecone.init(
    api_key=api_key,  # find at app.pinecone.io
    environment=os.getenv('PINECONE_ENV'),  # next to api key in console
)

index_name = os.getenv('PINECONE_INDEX')
embeddings = OpenAIEmbeddings()
similarity_min_value = 0.5
email_address = ["<info@fourreasons.us>", "<info@nonothing.us>",
                 "<info@kcprofessionalusa.com>", "<tom@fourreasons.us>"]


def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)


def delete_all_data():
    # Initialize Pinecone client
    pinecone.init(api_key=api_key, environment=os.getenv('PINECONE_ENV'))

    if index_name in pinecone.list_indexes():
        # Delete the index
        pinecone.delete_index(index_name)
        print("Index successfully deleted.")
    else:
        print("Index not found.")

    pinecone.create_index(
        index_name,
        dimension=1536,
        metric='cosine',
        pods=1,
        replicas=1,
        pod_type='p1.x1'
    )
    print("new: ", pinecone.list_indexes())


def split_document(doc: Document):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=80,
        chunk_overlap=20,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents([doc])
    return chunks


def train_txt(content: str, threshold: str):
    start_time = time.time()
    # loader = TextLoader(file_path=f"./train-data/{namespace}-{filename}")
    # documents = loader.load()
    doc = Document(page_content=content, metadata={"source": threshold})
    # print("threshold: -----------------------_________________", threshold)
    # print(doc)
    chunks = split_document(doc)
    Pinecone.from_documents(
        chunks, embeddings, index_name=index_name)
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)
    return True


def get_context(msg: str, keywords: str):
    results = tuple()
    db = Pinecone.from_existing_index(
        index_name=index_name, embedding=embeddings)
    results = db.similarity_search_with_score(msg, k=20)
    # print(results)
    context = ""
    facts = ""
    for result in results:
        facts += result[0].page_content
    with open("./data/pinecone.txt", "w") as txt_file:
        for i in range(0, 20):
            context += '\n'
            # txt_file.write('score: ' + str(result[1]))
            # txt_file.write("page_content" + result[0].page_content)
            # txt_file.write("metadata: " + result[0].metadata['source']+'\n')
            # print('score: ', result[1])
            # print("page_content", result[0].page_content)
            # print("metadata: ", result[0].metadata['source'], '\n')
            context += results[i][0].metadata['source']
    # tokens = 0
    # for result in results:
    #     print(result)
    #     if result[1] >= similarity_value_limit:
    #         tokens += len(nltk.word_tokenize(result[0].page_content))
    # print("token: ", tokens)
    # print("context --------------------- ", context)
    # print("_______________________________________")
    context = re.sub(r'\n{2,}', ' ', context)
    context = context[:(min(4000*4, len(context)))]
    token = tiktoken_len(context) + tiktoken_len(facts)
    print(len(context)," ", tiktoken_len(context))
    print(len(facts)/4)
    if token >= 8100:
        context = context[:(3500*4)]
    return get_answer(context, facts, msg, keywords)


def get_answer(context, facts, msg, keywords):
    global prompt

    result = "The most similar response that you already received before: \n\n"

    print(context)

    # These are facts you can refer to.
    # {facts}
    instructor = f"""
        These are sample reponses you can refer to.
        {facts + context}
        The samples given above are not given in the order of emails and responses, and several conversations are listed.
        It can contains a similar response corresponding to the message given below by the user.
        Based on the facts and the sent and received times in the aforementioned samples, you must select and extract the portion that you believe is most comparable to the user's response to the message.
        This response was written by one of these email addresses below.
        {email_address}
        Eliminate unnecessary information, avoid repetitive parts, and try to pick the right parts.
        Additionally, you have to analyze sample responses provided above in detail and based on that, you must answer to user provided question in as much detail as possible.
        Analyze sample responsed give above carefully and then extract valuable data, answer to user's messages.
        Provide me valuable information as a list as much as you can.
        For example, you can extract and provide all ingradients of mentioned product.
        Don't output you can't generate response and facts.
        Don't change extracted response.
        You shouldn't say that you can't generate an appropriate response.

    """

    try:
        response = openai.ChatCompletion.create(
            model='gpt-4',
            max_tokens=800,
            messages=[
                {'role': 'system', 'content': instructor},
                {'role': 'user', 'content': f"""
                    {msg}
                    Split the response and facts with ------------------.
                """}
            ],
            # stream=True
        )
        result += response.choices[0].message.content

        instructor = f"""
        {response.choices[0].message.content}
        The paragraph above is very similar to the response to the message the user received.
        Now modify the given response slightly so that it fully suits the message the user received. You should edit slightly and maintain your writing style.
        """

        response = openai.ChatCompletion.create(
            model='gpt-4',
            max_tokens=500,
            messages=[
                {'role': 'system', 'content': instructor},
                {'role': 'user', 'content': f"""
                    {msg}
                    This is message you have to response.
                    Please modify your given response.
                    When you modify your response, please focus on below keywords.
                    {keywords}
                """}
            ],
            # stream=True
        )
        result += '\n\n-----------------------------------\n'
        result += "Newly generated response based on above one: \n\n"
        result += response.choices[0].message.content

        return result
        # for chunk in response:
        #     if 'content' in chunk.choices[0].delta:
        #         string = chunk.choices[0].delta.content
        #         # print("string: ", string)
        #         yield string
        #         final += string
    except Exception as e:
        print(e)
