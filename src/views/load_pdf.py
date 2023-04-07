import numpy as np
import openai
import pandas as pd
import time
import PyPDF2
import dotenv
from src.models.study_guide import Study_Guide

from openai.embeddings_utils import get_embedding
from openai.embeddings_utils import cosine_similarity

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Open the PDF file in read-binary mode
def read_pdf(pdf_file):
    with open(pdf_file, 'rb') as pdf_file:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Loop through the pages and extract the first line of each page
        sections = []
        for page_number, page in enumerate(pdf_reader.pages):
            # Get the text content of the page
            text = page.extract_text()

            # Extract the first line of the page
            first_line = text.split('\n')[0]

            # Strip head and footer off page
            remaining_text = '\n'.join(text.split('\n')[1:])

            # Normalize the white space on the first line
            block = ' '.join(first_line.strip().split())
            if block.startswith("Block "):
                # Add the page number and first line to the sections list
                sections.append((block, page_number + 1, remaining_text))

    return sections
    

def put_in_dataframe(data):
    df = pd.DataFrame(data, columns=['block', 'page', 'text'])
    return df


def embed_df(df):
    print("Embedding text")
    # Sleep for 2 becuase of API limit
    df['embedding'] = df['text'].apply(lambda x: time.sleep(2) or get_embedding(x, engine='text-embedding-ada-002'))

    # Instead of saving to CSV, save to study guide models
    df.to_csv('thisCSV.csv')


    for index, row in df.iterrows():
        study_guide = Study_Guide(
            block=row['block'],
            page=row['page'],
            text=row['text'],
            embeddings=row['embeddings']
        )
        study_guide.save()


    print("Text embedding c/w")



data = read_pdf()
df = put_in_dataframe(data)
embed_df(df)