from django.shortcuts import render
from django.http import JsonResponse
from pathlib import Path
from django.conf import settings
from django.contrib.auth.decorators import login_required
from src.models.question import Question
from src.models.profile import Profile
from src.models.study_guide import Study_Guide
import os
import openai
from dotenv import load_dotenv
from collections import deque
import numpy as np
import pandas as pd
from openai.embeddings_utils import get_embedding
from openai.embeddings_utils import cosine_similarity
from datetime import datetime
import azure.cognitiveservices.speech as speechsdk
import random



load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

@login_required(login_url='/login')
def as_view(request):


    #Gets current username and profile
    current_user = request.user
    username = getattr(current_user, "username")
    current_profile = Profile.objects.get(user_profile_id = current_user)

    #testting
    r_text = random_vector()

    full_response = get_openAI_response(r_text)
    text_response = full_response["choices"][0]["message"]["content"]

    
    #Gets user's daily useage, limit and checks
    user_daily_tokens, user_daily_limit, user_within_limits = check_user_tokens(current_user)
    
    #When the user presses submit
    if request.method == "POST":
        #Checks to see if user has reached token limit
        if user_within_limits:
            try:

                print("do stuff")

            #If API or Question fails
            except:
                error = "Submission Failed"

        #When max token limit is reached
        else:
            error = "Max daily questions reached"

    #Data passed to html template
    context = {
        'r_text' : r_text,
        'text_response' : text_response

    }    

    return render(request, 'quiz.html', context)



def get_openAI_response(study_guide):

    prompt = """Create a multiple choice question only using the following informations below
                with 4 answers labled A. B. C. and D. but only one of them is correct.
                Then tell me which of the 4 was correct by giving me the output "Answer: " 
                followed by the correct letter choice. Also give the reasoning behind the correct
                answer by starting with "Reason: " and then your reasoning.
                """

    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": study_guide}
        ]
    )
    return response


def random_vector():
    #Reads static CSV file that contains pre-embedded text and vectors for the study guide
    filePath = Path(settings.BASE_DIR, 'src', 'static', 'studyGuides', 'fundies.csv')    
    df = pd.read_csv(filePath)
    df['embedding'] = df['embedding'].apply(eval).apply(np.array)

    df_length = len(df.index)
    random_int = random.randint(1, df_length -1)

    random_vector = df.iloc[random_int]["text"]
    
    
    return random_vector

'''
Input
user - current user loggin in

Return
True - if user has not exeeded their prorated daily token limit
False - if user has exeeded their prorated daily token limit or monthly total
'''
def check_user_tokens(user):
    MAX_DAILY = 30000
    MAX_MONTHLY = 1000000

    current_profile = Profile.objects.get(user_profile_id = user)
    current_chat_history = Question.objects.filter(submitted_by__profile=current_profile)

    monthly_query = current_chat_history.filter(date_created__month=datetime.now().month, date_created__year=datetime.now().year)
    monthly_usage = sum(list(monthly_query.values_list('token_total', flat=True)))

    daily_query = current_chat_history.filter(date_created__day=datetime.now().day, date_created__month=datetime.now().month, date_created__year=datetime.now().year)
    daily_usage = sum(list(daily_query.values_list('token_total', flat=True)))

    prorated_daily = (datetime.now().day * MAX_DAILY) - monthly_usage

    if monthly_usage < MAX_MONTHLY and prorated_daily > 0:
        return daily_usage, prorated_daily, True 
    else:
        return daily_usage, prorated_daily, False
