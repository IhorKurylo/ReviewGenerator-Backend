from langchain.schema import Document
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import CSVLoader, PyPDFLoader, TextLoader, Docx2txtLoader
import nltk

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
        chunk_size=1000,
        chunk_overlap=20,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents([doc])
    return chunks


def train_txt(threshold: str):
    start_time = time.time()
    # loader = TextLoader(file_path=f"./train-data/{namespace}-{filename}")
    # documents = loader.load()
    doc = Document(page_content=threshold, metadata={"source": threshold})
    print("threshold: -----------------------_________________", threshold)
    chunks = split_document(doc)
    Pinecone.from_documents(
        chunks, embeddings, index_name=index_name)
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)
    return True


def get_context(msg: str):
    # delete_all_data()
    # print("message---------------------------" + msg)
    similarity_value_limit = 0.76
    results = tuple()
    # print("here")
    db = Pinecone.from_existing_index(
        index_name=index_name, embedding=embeddings)
    results = db.similarity_search_with_score(msg, k=1)
    # print(results)
    context = ""
    for result in results:
        context += ''
        if result[1] >= similarity_value_limit:
            context += result[0].metadata['source']
    # tokens = 0
    # for result in results:
    #     print(result)
    #     if result[1] >= similarity_value_limit:
    #         tokens += len(nltk.word_tokenize(result[0].page_content))
    # print("token: ", tokens)
    # print("context --------------------- ", context)
    get_answer(context, msg)
    return {"context": context}


def get_answer(context, msg):
    global prompt

    instructor = f"""
      You should write the reply for user provided email.
      You can refer to sample replys.
      Below are sample emails and replys.
      Please provide quite similar replies to user provided email.
      These are kinds of conversation of emails and its replies.
      The most important thing is writing style.
      Writing style should be same with sample replies below.
      {context}
    """
    try:
        response = openai.ChatCompletion.create(
            model='gpt-4',
            max_tokens=2000,
            messages=[
                {'role': 'system', 'content': instructor},
                {'role': 'user', 'content': msg }
            ],
            # stream=True
        )
        print("answer --------------:\n", response.choices[0].message.content)
        # for chunk in response:
        #     if 'content' in chunk.choices[0].delta:
        #         string = chunk.choices[0].delta.content
        #         # print("string: ", string)
        #         yield string
        #         final += string
    except Exception as e:
        print(e)
    


