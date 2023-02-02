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


@login_required(login_url='/login')
def as_view(request):
    TEST_MODE = True
    token_prompt = 0
    token_completion = 0
    token_total = 0
    error = ""

    current_user = request.user
    username = getattr(current_user, "username")
    current_profile = Profile.objects.get(user_profile_id = current_user)
    current_chat_history = Question.objects.filter(submitted_by__profile=current_profile)
    chat_list = list(current_chat_history.values_list('question', 'response'))
    
    try:
        last_study_guide = getattr(current_chat_history.last(), 'from_study_guide')
        last_course = getattr(last_study_guide, 'course')
        last_block = getattr(last_study_guide, 'block')
        last_unit = getattr(last_study_guide, 'unit')
    except:
        last_study_guide = ""
        last_course = ""
        last_block = ""
        last_unit = ""

    study_guide_queryset = Study_Guide.objects.all()
    course_list = list(study_guide_queryset.values_list('course', flat=True))
    
    if request.method == "POST":
        try:
            studentInput = request.POST["studentInput"]
            course_input = request.POST['course']
            block_input = request.POST['block']
            unit_input = request.POST['unit']

            current_study_guide = Study_Guide.objects.get(
                course = course_input, block = block_input, unit = unit_input)    
            current_prompt = getattr(current_study_guide, 'prompt')
            short_history = manageHistoyChat(chat_list)

            if TEST_MODE == False:
                full_response = get_openfull_response(current_prompt, short_history, studentInput)
                text_response = full_response.choices[0].text
                token_prompt = full_response.usage.prompt_tokens
                token_completion = full_response.usage.completion_tokens
                token_total = full_response.usage.total_tokens
            else:
                text_response = "Non-AI response to: " + studentInput

            new_question = Question()
            new_question.question = studentInput
            new_question.response = text_response
            new_question.submitted_by = current_user
            new_question.instructor = getattr(current_profile, 'user_instructor')
            new_question.from_study_guide = current_study_guide
            new_question.token_prompt = token_prompt
            new_question.token_completion = token_completion
            new_question.token_total = token_completion
            new_question.save()
            current_profile.user_question.add(new_question)

            chat_list = list(current_chat_history.values_list('question', 'response'))       

        except:
           error = "Submission Failed"

    context = {
        'historyChat' : chat_list,
        'username' : username,
        'course_list' : course_list,
        'block' : last_block,
        'unit' : last_unit,
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
    deq = deque(maxlen=8)
    for i in history:
        deq.append(i)
    short_history_pairs = list(deq)

    short_history_str = ""
    for i in short_history_pairs:
        short_history_str += f" Student: {i[0]} {i[1]}"

    return short_history_str
