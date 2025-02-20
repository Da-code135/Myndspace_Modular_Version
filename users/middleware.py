from django.shortcuts import redirect

class LoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Redirect logged-in users to the dashboard when visiting the landing page
        if request.user.is_authenticated and request.path == '/':
            return redirect('dashboard')
        return self.get_response(request)