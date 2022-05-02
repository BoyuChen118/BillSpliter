from django.shortcuts import render
from django.http import HttpResponse
import BillSplitterApp.backend.mongodb as backendservice
import datetime

# test with current_datetime


def current_datetime(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)


def login(request):
    data = request.GET
    if 'email' in data and 'pass' in data:
        auth = backendservice.Authenticator()
        email = data.get('email')
        password = data.get('pass')
        auth_success = auth.login(email, password)
        if not auth_success:
            return render(request, 'login.html', {'auth_success': auth_success})
        else:
            html = "<html><body>Landing page</body></html>"
            return HttpResponse(html)
    return render(request, 'login.html')


def signup(request):
    data = request.GET
    if 'email' in data and 'pass' in data:
        auth = backendservice.Authenticator()
        email = data.get('email')
        password = data.get('pass')
        nickname = data.get('name')
        confirmpass = data.get('confirmpass')
        auth_success = auth.sign_up(email, password, confirmpass, nickname)
        if not auth_success[0]:
            return render(request, 'signup.html', {'auth_success': auth_success[0], 'reason': auth_success[1]})
        else:
            html = "<html><body>Landing page</body></html>"
            return HttpResponse(html)
    return render(request, 'signup.html')
