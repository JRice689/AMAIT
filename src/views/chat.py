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

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
historyChat = []
recentHistory = []
tokenPrompt = 0
tokenCompletion = 0
tokenTotal = 0

@login_required(login_url='/login')
def as_view(request):

    current_study_guide = Study_Guide.objects.get(course = 'Fundies')
    print(current_study_guide)

    if request.method == "POST":
        studentInput = request.POST["studentInput"]
        historyChat.append("Student: " + studentInput)

        #response = get_openAI_response(studentInput)
        response = "Text"

        current_user = request.user
        current_profile = Profile.objects.get(user_profile_id = current_user)
        new_question = Question()
        new_question.question = studentInput
        new_question.response = response
        new_question.submitted_by = current_user
        new_question.instructor = getattr(current_profile, 'user_instructor')
        new_question.from_study_guide = current_study_guide
        new_question.save()
        current_profile.user_question.add(new_question)


    context = {
        'historyChat' : historyChat,
        'tokenPrompt' : tokenPrompt,
        'tokenCompletion' : tokenCompletion,
        'tokenTotal' : tokenTotal
    }    

    return render(request, 'chat.html', context)

def get_openAI_response(input):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=generate_prompt(input),
        temperature=0.6,
        max_tokens=400,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    historyChat.append(response.choices[0].text)
    tokenPrompt = response.usage.prompt_tokens
    tokenCompletion = response.usage.completion_tokens
    tokenTotal = response.usage.total_tokens

    return response.choices[0].text


# Grabs the last 8 chats from history
# Used to pass to prompt in generate_prompt()
def manageHistoyChat():
    deq = deque(maxlen=8)
    for i in historyChat:
        deq.append(i)
    recentHistory = list(deq)
    return "\n".join(recentHistory)


def readStudyGuide():
    # Used for testing API without wasting tokens
    filePath = Path(settings.BASE_DIR, 'src', 'static', 'studyGuides', 'blank.txt')

    # Reads actual study guide ~2K tokens required
    # filePath = Path(settings.BASE_DIR, 'src', 'static', 'studyGuides', 'blk3Unit1.txt')

    with open(filePath, "r", encoding="utf-8") as file:
        currentStudyGudie = file.read()
        return(currentStudyGudie)
   

def generate_prompt(studentInput):
    return """The following is a conversation with an AI instructor for high school graduates 
    trying to become aircraft mechanics. The AI is professional and will answer the student's 
    questions correctly.  If the student asks a question that does not pertain to aircraft or 
    mechanics please remind them to stay on topic.  Only use the following information given 
    below when helping the student. \n""" + readStudyGuide() + """\nStudent: I need help 
    understanding aircraft mechanics AI Instructor: I am an AI created by OpenAI. What do you 
    need help with today?""" + manageHistoyChat() + """
    Student: {}
    """.format(studentInput)



