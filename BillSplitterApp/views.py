from django.shortcuts import redirect, render
from django.http import HttpResponse
import BillSplitterApp.backend.mongodb as backendservice
import datetime

# test with current_datetime

auth = backendservice.Authenticator()
def current_datetime(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)


def login(request):
    data = request.GET
    if 'email' in data and 'pass' in data:
        email = data.get('email')
        password = data.get('pass')
        auth_success = auth.login(email, password)
        if not auth_success:
            return render(request, 'login.html', {'auth_success': auth_success})
        else:
            response = redirect(f'/landing/?name={auth.get_name()}&groups=')
            return response
    return render(request, 'login.html')


def signup(request):
    data = request.GET
    if 'email' in data and 'pass' in data and 'name' in data and 'confirmpass' in data:
        email = data.get('email')
        password = data.get('pass')
        nickname = data.get('name')
        confirmpass = data.get('confirmpass')
        auth_success = auth.sign_up(email, password, confirmpass, nickname)
        if not auth_success[0]:
            return render(request, 'signup.html', {'auth_success': auth_success[0], 'reason': auth_success[1]})
        else:
            response = redirect(f'/landing/?name={auth.get_name(email)}')
            return response
    return render(request, 'signup.html')

def landing(request):
    data = request.GET
    if 'groupname' in data:   # create group operation
        auth.create_group(data.get('groupname'))
    elif 'groupcode' in data:   # join group operation
        errormsg = auth.join_group(data.get('groupcode'))
    groups = auth.get_groups()
    name = auth.get_name()
    return render(request, 'landing.html', {'groups': groups, 'name': name})

# view to display when user clicks on one specific group
def grouppage(request):
    pass
    