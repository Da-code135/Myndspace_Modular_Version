from django.shortcuts import render
from django.shortcuts import redirect
from .models import ThoughtLog
from .forms import ThoughtLogForm

def breathing_exercise(request):
    """
    Render a page that includes a guided breathing exercise.
    You can use JavaScript for a timer/animation effect.
    """
    return render(request, 'steamroomandselfcare/breathing_exercise.html')

def journaling_prompt(request):
    """
    Display journaling prompts and a form for user input.
    """
    return render(request, 'steamroomandselfcare/journaling.html')


def thought_log(request):
    if request.method == 'POST':
        form = ThoughtLogForm(request.POST)
        if form.is_valid():
            thought = form.save(commit=False)
            thought.user = request.user  # assumes user is authenticated
            thought.save()
            return redirect('steamroomandselfcare:thought_log')
    else:
        form = ThoughtLogForm()
    # Retrieve the user's thought logs
    logs = ThoughtLog.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'steamroomandselfcare/thought_logs.html', {'form': form, 'logs': logs})


def meditation(request):
    """
    Render a page with guided meditation exercises.
    This page could include an HTML5 audio player and visual aids.
    """
    return render(request, 'steamroomandselfcare/meditation.html')

def landing_page(request):
    """
    Render the landing page for the self-care app.
    This page provides links to each of the app's features.
    """
    return render(request, 'steamroomandselfcare/landing.html')