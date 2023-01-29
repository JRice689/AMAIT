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

    study_guide_queryset = Study_Guide.objects.all()
    course_list = list(study_guide_queryset.values_list('course', flat=True))



    if request.method == "POST":
        studentInput = request.POST["studentInput"]
        historyChat.append("Student: " + studentInput)

        course_input = request.POST['course']
        block_input = request.POST['block']
        unit_input = request.POST['unit']
        current_study_guide = Study_Guide.objects.get(
            course = course_input, block = block_input, unit = unit_input)    
        current_prompt = getattr(current_study_guide, 'prompt')

        response = get_openAI_response(current_prompt, studentInput)
        #response = "Text"

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
        'course_list' : course_list,
        'tokenPrompt' : tokenPrompt,
        'tokenCompletion' : tokenCompletion,
        'tokenTotal' : tokenTotal
    }    

    return render(request, 'chat.html', context)

def get_openAI_response(prompt, input):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=generate_prompt(prompt, input),
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


def generate_prompt(prompt, input):
    return """The following is a conversation with an AI instructor for high school graduates 
    trying to become aircraft mechanics. The AI is professional and will answer the student's 
    questions correctly.  If the student asks a question that does not pertain to aircraft or 
    mechanics please remind them to stay on topic.  Only use the following information given 
    below when helping the student. \n""" + prompt + """\nStudent: I need help understanding 
    aircraft mechanics AI Instructor: I am an AI created by OpenAI. What do you need help with 
    today?""" + manageHistoyChat() + """
    Student: {}
    """.format(input)


# Grabs the last 8 chats from history
# Used to pass to prompt in generate_prompt()
def manageHistoyChat():
    deq = deque(maxlen=8)
    for i in historyChat:
        deq.append(i)
    recentHistory = list(deq)
    return "\n".join(recentHistory)
