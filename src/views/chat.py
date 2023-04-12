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
import base64
import logging


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


@login_required(login_url='/login')
def as_view(request):
    token_prompt = 0
    token_completion = 0
    token_total = 0
    audio_response = ""
    error = ""

    #Gets current username and profile
    current_user = request.user
    username = getattr(current_user, "username")
    current_profile = Profile.objects.get(user_profile_id = current_user)

    #Gets full chat history and put it in a list
    current_chat_history = Question.objects.filter(submitted_by__profile=current_profile)
    chat_list = list(current_chat_history.values_list('question', 'response'))
    
    #Gets user's daily useage, limit and checks
    user_daily_tokens, user_daily_limit, user_within_limits = check_user_tokens(current_user)
    
    #When the user presses submit
    if request.method == "POST":
        #Checks to see if user has reached token limit
        if user_within_limits:
            # try:
            #Students input from form
            student_input = request.POST["studentInput"]

            #Finds correct section of study guide based on student input
            found_study_guide = find_vector(student_input)

            #Saves the students question BEFORE AI response
            new_question = Question()
            new_question.question = student_input
            new_question.response = "..." #temp response
            new_question.submitted_by = current_user
            new_question.instructor = getattr(current_profile, 'user_instructor')
            new_question.from_study_guide = found_study_guide
            new_question.token_prompt = token_prompt
            new_question.token_completion = token_completion
            new_question.token_total = token_total
            new_question.save()
            current_profile.user_question.add(new_question)
                
                #Backend python text to speech
                #audio_response = response_to_speech(text_response, username)   


            #If API or Question fails
            # except:
            #     error = "Submission Failed"

        #When max token limit is reached
        else:
            error = "Max daily questions reached"

    #Data passed to html template
    context = {
        'username' : username,
        'userTokens' : user_daily_tokens,
        'userLimit' : user_daily_limit,
        'tokenPrompt' : token_prompt,
        'tokenCompletion' : token_completion,
        'tokenTotal' : token_total,
        'audioResponse' : audio_response,
        'error' : error
    }    

    return render(request, 'chat.html', context)


def get_answer(request):
    current_user = request.user
    current_profile = Profile.objects.get(user_profile_id=current_user)

    current_chat_history = Question.objects.filter(submitted_by__profile=current_profile)
    chat_list = list(current_chat_history.values_list('question', 'response'))

    # try:
    #Updates chat list with new question and temp response
    updated_chat_history = Question.objects.filter(submitted_by__profile=current_profile)
    last_question = updated_chat_history.last() 
    found_study_guide = getattr(last_question, "from_study_guide")
    student_input = getattr(last_question, "question")

    #Get a shorted chat history to add to the AI prompt
    short_history = shorten_history_chat(chat_list)

    #OpenAI's GPT Tubrbo 3.5 API
    full_response = get_openAI_response(found_study_guide, short_history, student_input)
    text_response = full_response["choices"][0]["message"]["content"]
    token_prompt = full_response["usage"]["prompt_tokens"]
    token_completion = full_response["usage"]["completion_tokens"]
    token_total = full_response["usage"]["total_tokens"]

    #Update last question with AI response and tokens
    last_question.response = text_response
    last_question.token_prompt = token_prompt
    last_question.token_completion = token_completion
    last_question.token_total = token_total
    last_question.save()
    
    # except:
    #     print("ERROR ON GET ANSWER")


    return JsonResponse({'chat_list': chat_list})

'''
Input:
response - string response from OpenAI

Return:
audio_base64 - WAV audio file to play on client side

Converts the text response to a playable audio file for the client
'''
def response_to_speech(response, username):
    try:

        subscription_key = os.getenv("AZURE_SPEECH")
        region = os.getenv("AZURE_REGION")

        speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
        speech_config.speech_synthesis_voice_name='en-US-JennyNeural'
        file_name = username + "-audio.wav"
        file_config = speechsdk.audio.AudioOutputConfig(filename=file_name)
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)


        audio = speech_synthesizer.speak_text_async(response).get()

        with open(file_name, 'rb') as f:
            audio_bytes = f.read()

        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

    except Exception as ex:
        logging.error("An error occurred: {}".format(ex))    
        
    return audio_base64


'''
Input:
study_guide - related section from study guide
history - shorted down history for reference
input - students input from form

Return:
response - OpenAI's reponse to the student to include token count

This uses OpenAI's GPT Turbo 3.5 completion model to answer the students question
'''
def get_openAI_response(study_guide, history, input):

    prompt = """You are an AI tutor for high school graduates trying to become aircraft mechanics. 
    The AI is professional and will answer the student's questions correctly.
    If the student asks a question that does not pertain to aircraft or mechanics please remind 
    them to stay on topic.  Only use the following information given below when helping the student."""

    messages = [
        {"role": "system", "content": prompt},
        {"role": "system", "content": study_guide},
    ]

    for i in range(len(history)):
        messages.append({"role": "user", "content": history[i][0]})
        messages.append({"role": "assistant", "content": history[i][1]})

    messages.append({"role": "user", "content": input})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    return response


'''
Input:
search_text - student's input from form

Return:
found_text - Matched study guide section

This uses OpenAI's embedding to search the given Panda's DataFile to find the best matched
section from the study guide that the user was asking.

TODO:
Instead of reading from a static CSV file, read it from the database
'''
def find_vector(search_text):
    #Reads static CSV file that contains pre-embedded text and vectors for the study guide
    filePath = Path(settings.BASE_DIR, 'src', 'static', 'study_guide.csv')    
    df = pd.read_csv(filePath)
    df['embedding'] = df['embedding'].apply(eval).apply(np.array)

    #Use OpenAI's embedding model to change the student's input into vectors
    search_vector = get_embedding(search_text, engine='text-embedding-ada-002')
    
    #Use cosine similarity against each section of the study guide
    df["similarities"] = df['embedding'].apply(lambda x: cosine_similarity(x, search_vector))
    
    #Finds the best matched vector
    found_vectors = df.sort_values("similarities", ascending=False).head(3)
    
    #Selected the text for the best match
    found_text = found_vectors.iloc[0]["text"]
    found_next_text = found_vectors.iloc[1]["text"]

    combined_text = found_text + "\n" + found_next_text

    
    return combined_text


'''
Input:
history - full chat history between user and AI

Returns
short_history - list of pairs of text containing the last 4 conversation pieces

This gets the most recent chat history and passes to the prompt so they can ask follow up questions
'''
def shorten_history_chat(history):
    deq = deque(maxlen=4)
    for i in history:
        deq.append(i)
    short_history = list(deq)

    return short_history


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
    

def get_chat_list(request):
    current_user = request.user
    current_profile = Profile.objects.get(user_profile_id=current_user)
    chat_list = list(Question.objects.filter(submitted_by__profile=current_profile).values('question', 'response'))
    return JsonResponse({'chat_list': chat_list})