from django.shortcuts import redirect, render
from django.http import HttpResponse
from urllib3 import HTTPResponse
import BillSplitterApp.backend.mongodb as backendservice
import datetime

# initialize auth
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
            response = redirect(f'/landing/home/')
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
            response = redirect(f'/landing/home/')
            return response
    return render(request, 'signup.html')

# view to display when user clicks on one specific group (e.g. group code, members etc.)
def landing(request, **kwargs):
    page = kwargs.get('page', None)
    # user is accessing groups[groupindex] at landing page
    groupindex = kwargs.get('groupindex', None)
    groupindex = int(groupindex) if groupindex is not None else None
    data = request.GET
    if 'groupname' in data:   # create group operation
        auth.create_group(data.get('groupname'))
    elif 'groupcode' in data:   # join group operation
        errormsg = auth.join_group(data.get('groupcode'))
    groups = auth.get_groups() # all group names the user belongs to
    name = auth.get_name()
    
    pages = backendservice.PageGenerator(auth).generatepages(page, groupindex)  # represent state of all page, false=page is not on display, true=page is on display.  [home, about, profile, contact, groupcode]
    groupinfo = []
    
    # handle group page request pages[4] is current group code
    if pages[4]:
        groupinfo = auth.get_group_members(pages[4])   # array of [membername, memberemail]

    return render(request, 'landing.html', {'groups': groups, 'name': name, 'pages': pages, 'groupmembers': groupinfo})
