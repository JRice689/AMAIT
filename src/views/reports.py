from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from src.models.question import Question




@login_required(login_url='/login')
def as_view(request):

    questions = Question.objects.all()
    print(questions)


    return render(request, 'reports.html', {'questions': questions})


