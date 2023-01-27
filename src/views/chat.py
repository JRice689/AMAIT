from django.shortcuts import render
from django.http import request
from pathlib import Path
from django.conf import settings

import os
import openai
from dotenv import load_dotenv
from collections import deque

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
historyChat = []
recentHistory = []

def as_view(request):
    tokenPrompt = 0
    tokenCompletion = 0
    tokenTotal = 0

    if request.method == "POST":
        studentInput = request.POST["studentInput"]
        historyChat.append("Student: " + studentInput)
        
        # openAI API
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(studentInput),
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

    context = {
        'historyChat' : historyChat,
        'tokenPrompt' : tokenPrompt,
        'tokenCompletion' : tokenCompletion,
        'tokenTotal' : tokenTotal
    }    

    return render(request, 'chat.html', context)

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
    # filePath = Path(settings.BASE_DIR, 'src', 'static', 'studyGuides', 'blank.txt')

    # Reads actual study guide ~2K tokens required
    filePath = Path(settings.BASE_DIR, 'src', 'static', 'studyGuides', 'blk3Unit1.txt')

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



