from django.shortcuts import render
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

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


@login_required(login_url='/login')
def as_view(request):
    token_prompt = 0
    token_completion = 0
    token_total = 0
    error = ""

    current_user = request.user
    username = getattr(current_user, "username")
    current_profile = Profile.objects.get(user_profile_id = current_user)
    current_chat_history = Question.objects.filter(submitted_by__profile=current_profile)
    chat_list = list(current_chat_history.values_list('question', 'response'))
    

    user_tokens = sum(list(current_chat_history.values_list('token_total', flat=True)))

    



    if request.method == "POST":
        if check_user_tokens(current_user):
            try:
                studentInput = request.POST["studentInput"]
                prompt = find_vector(studentInput)
                short_history = manageHistoyChat(chat_list)

                full_response = get_openfull_response(prompt, short_history, studentInput)
                text_response = full_response.choices[0].text
                token_prompt = full_response.usage.prompt_tokens
                token_completion = full_response.usage.completion_tokens
                token_total = full_response.usage.total_tokens

                new_question = Question()
                new_question.question = studentInput
                new_question.response = text_response
                new_question.submitted_by = current_user
                new_question.instructor = getattr(current_profile, 'user_instructor')
                new_question.from_study_guide = prompt
                new_question.token_prompt = token_prompt
                new_question.token_completion = token_completion
                new_question.token_total = token_total
                new_question.save()
                current_profile.user_question.add(new_question)

                chat_list = list(current_chat_history.values_list('question', 'response'))       

            except:
                error = "Submission Failed"
        else:
            error = "Max daily questions reached"

    context = {
        'historyChat' : chat_list,
        'username' : username,
        'userTokens' : user_tokens,
        'tokenPrompt' : token_prompt,
        'tokenCompletion' : token_completion,
        'tokenTotal' : token_total,
        'error' : error
    }    

    return render(request, 'chat.html', context)


def get_openfull_response(prompt, history, input):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=generate_prompt(prompt, history, input),
        temperature=0.6,
        max_tokens=400,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response


def find_vector(search_text):
    # Change is ready from DB later
    filePath = Path(settings.BASE_DIR, 'src', 'static', 'studyGuides', 'fundies.csv')    
    df = pd.read_csv(filePath)
    df['embedding'] = df['embedding'].apply(eval).apply(np.array)

    search_vector = get_embedding(search_text, engine='text-embedding-ada-002')
    df["similarities"] = df['embedding'].apply(lambda x: cosine_similarity(x, search_vector))
    found_vectors = df.sort_values("similarities", ascending=False).head(1)
    found_text = found_vectors.iloc[0]["text"]
    return found_text


def generate_prompt(prompt, history, input):
    return """The following is a conversation with an AI tutor for high school graduates 
    trying to become aircraft mechanics. The AI is professional and will answer the student's 
    questions correctly.  If the student asks a question that does not pertain to aircraft or 
    mechanics please remind them to stay on topic.  Only use the following information given 
    below when helping the student. \n""" + prompt + """\nStudent: I need help understanding 
    aircraft mechanics AI Tutor: I am an AI created by OpenAI. What do you need help with 
    today?""" + history + """
    Student: {}
    """.format(input)


# Grabs the last 8 chats from history
# Used to pass to prompt in generate_prompt()
def manageHistoyChat(history):
    deq = deque(maxlen=4)
    for i in history:
        deq.append(i)
    short_history_pairs = list(deq)

    short_history_str = ""
    for i in short_history_pairs:
        short_history_str += f" Student: {i[0]} {i[1]}"

    return short_history_str


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
        return True 
    else:
        return False
    