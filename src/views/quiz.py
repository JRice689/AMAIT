from django.shortcuts import render

def as_view(request):
    return render(request, 'quiz.html')