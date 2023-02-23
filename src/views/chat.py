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
from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer
import base64


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
            try:
                #Students input from form
                student_input = request.POST["studentInput"]

                #Finds correct section of study guide based on student input
                prompt = find_vector(student_input)

                #Get a shorted chat history to add to the AI prompt
                short_history = manage_history_chat(chat_list)

                #OpenAI's API
                full_response = get_openAI_full_response(prompt, short_history, student_input)
                text_response = full_response.choices[0].text
                token_prompt = full_response.usage.prompt_tokens
                token_completion = full_response.usage.completion_tokens
                token_total = full_response.usage.total_tokens
               

                #Saves the students question and AI response
                new_question = Question()
                new_question.question = student_input
                new_question.response = text_response
                new_question.submitted_by = current_user
                new_question.instructor = getattr(current_profile, 'user_instructor')
                new_question.from_study_guide = prompt
                new_question.token_prompt = token_prompt
                new_question.token_completion = token_completion
                new_question.token_total = token_total
                new_question.save()
                current_profile.user_question.add(new_question)

                #Updates chat list with new question and response
                chat_list = list(current_chat_history.values_list('question', 'response'))   

                audio_response = response_to_speech(text_response)    

            #If API or Question fails
            except:
                error = "Submission Failed"

        #When max token limit is reached
        else:
            error = "Max daily questions reached"

    #Data passed to html template
    context = {
        'historyChat' : chat_list,
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


'''
Input:
response - string response from OpenAI

Return:
audio_base64 - WAV audio file to play on client side

Converts the text response to a playable audio file for the client
'''
def response_to_speech(response):
    subscription_key = os.getenv("AZURE_SPEECH")
    region = os.getenv("AZURE_REGION")

    speech_config = SpeechConfig(subscription=subscription_key, region=region)
    synthesizer = SpeechSynthesizer(speech_config=speech_config)

    #Removed 'AI Tutor: ' from response
    clean_response = response[10:].strip()

    audio = synthesizer.speak_text_async(clean_response).get()
    audio_base64 = base64.b64encode(audio.audio_data).decode('utf-8')
    
    return audio_base64


'''
Input:
prompt - related section from study guide
history - shorted down history for reference
input - students input from form

Return:
response - OpenAI's reponse to the student to include token count

This uses OpenAI's davinci completion model to answer the students question
'''
def get_openAI_full_response(prompt, history, input):
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


'''
Input:
prompt - related section from study guide
history - shorted down history for reference
input - students input from form

Returns combines text for OpenAI's completion model
'''
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
    filePath = Path(settings.BASE_DIR, 'src', 'static', 'studyGuides', 'fundies.csv')    
    df = pd.read_csv(filePath)
    df['embedding'] = df['embedding'].apply(eval).apply(np.array)

    #Use OpenAI's embedding model to change the student's input into vectors
    search_vector = get_embedding(search_text, engine='text-embedding-ada-002')
    
    #Use cosine similarity against each section of the study guide
    df["similarities"] = df['embedding'].apply(lambda x: cosine_similarity(x, search_vector))
    
    #Finds the best matched vector
    found_vectors = df.sort_values("similarities", ascending=False).head(1)
    
    #Selected the text for the best match
    found_text = found_vectors.iloc[0]["text"]
    
    return found_text


'''
Input:
history - full chat history between user and AI

Returns
short_history_str - string of text containing the last 4 conversation pieces

This gets the most recent chat history and passes to the prompt so they can ask follow up questions
'''
def manage_history_chat(history):
    deq = deque(maxlen=4)
    for i in history:
        deq.append(i)
    short_history_pairs = list(deq)

    short_history_str = ""
    for i in short_history_pairs:
        short_history_str += f" Student: {i[0]} {i[1]}"

    return short_history_str


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
    

