from django.shortcuts import redirect, render
from django.http import HttpResponse
from urllib3 import HTTPResponse
import BillSplitterApp.backend.mongodb as backendservice
import BillSplitterApp.backend.data as datastructs
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
    errormsg = ''
    if 'groupname' in data:   # create group operation
        auth.create_group(data.get('groupname'))
    elif 'groupcode' in data:   # join group operation
        errormsg = auth.join_group(data.get('groupcode'))
    groups = auth.get_groups() # all group names the user belongs to
    name = auth.get_name()
    
    pages = backendservice.PageGenerator(auth).generatepages(page, groupindex)  # represent state of all page, false=page is not on display, true=page is on display.  [home, about, profile, contact, groupcode]
    groupinfo = [] # array of [membername, memberemail]
    tempexpenses = {} # number of items in temporary expense
    # handle group page request pages[4] is current group code
    if pages[4]:
        groupinfo = auth.get_group_members(pages[4])
        if request.method == 'POST':
            postdata = request.POST
            deleteIndex = backendservice.Util().extractDelete(dict(postdata)) # delete tempexpenses[deleteIndex] if deleteindex isn't -1
            if request.POST.get('submititem'): # user submitted an temporary expense request
                errormsg = auth.update_tempexpenses(pages[4], datastructs.item(postdata.get('itemname'), postdata.get('itemprice'), postdata.get('itemquantity')).toJson())
            elif deleteIndex != -1:
                auth.delete_tempexpense(pages[4], deleteIndex)
            elif request.POST.get('submitexpense'): # user pressed the submit button (submit temp expense as permanent expense)
                pass
        tempexpenses = auth.get_tempexpenses(pages[4])
    return render(request, 'landing.html', {'groups': groups, 'name': name, 'pages': pages, 'groupmembers': groupinfo, 'tempexpenses': tempexpenses, 'tempitemcount': len(tempexpenses)})
