from django.shortcuts import redirect, render
from django.http import HttpResponse
import urllib
from  BillSplitterApp.backend.mongodb import Authenticator, PageGenerator, Util
from BillSplitterApp.backend.mongodb import Database
from BillSplitterApp.backend.scanner import ReceiptScanner
import BillSplitterApp.backend.data as datastructs
import datetime

# initialize auth and scanner
scanner = ReceiptScanner()


def current_datetime(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)


def login(request):
    data = request.GET
    if 'email' in data and 'pass' in data:
        auth = Authenticator(data.get('email'))
        auth_success = auth.login(data.get('pass'), request.session)
        if not auth_success:
            return render(request, 'login.html', {'auth_success': auth_success})
        else:
            response = redirect(f'/landing/home/')
            return response
    return render(request, 'login.html')


def signup(request):
    data = request.GET
    if 'email' in data and 'pass' in data and 'name' in data and 'confirmpass' in data:
        auth = Authenticator(data.get('email'))
        auth_success = auth.sign_up(data.get('email'), data.get('pass'), data.get('confirmpass'), data.get('name'), request.session)
        if not auth_success[0]:
            return render(request, 'signup.html', {'auth_success': auth_success[0], 'reason': auth_success[1]})
        else:
            response = redirect(f'/landing/home/')
            return response
    return render(request, 'signup.html')


def landing(request, **kwargs):
    db = Database(request.session['email'])
    page = kwargs.get('page', None)
    # user is accessing groups[groupindex] at landing page
    groupindex = kwargs.get('groupindex', None)
    groupindex = int(groupindex) if groupindex is not None else None
    data = request.GET
    resolved = data['resolved'] if 'resolved' in data else None
    errormsg = ''
    if 'groupname' in data:   # create group operation
        db.create_group(data.get('groupname'))
    elif 'groupcode' in data:   # join group operation
        errormsg = db.join_group(data.get('groupcode'))
    groups = db.get_groups()  # all group names the user belongs to
    name = db.get_name()
    defaultsplitoption = -1

    # represent state of all page, false=page is not on display, true=page is on display.  [home, about, profile, contact, groupcode]
    pg, util = PageGenerator(db), Util()
    pages = pg.generatepages(page, groupindex)
    groupinfo = []  # array of [membername, memberemail] ---> array of [membername, memberemail, amountowetothisuser]
    tempexpenses = {}  # number of items in temporary expense
    pendexpenses = []  # all pending expenses in the group
    expensename = ''
    # handle group page request pages[4] is current group code
    # view to display when user clicks on one specific group (e.g. group code, members etc.)
    if pages[4]:
        groupinfo = db.get_group_members(pages[4])
        if request.method == 'POST':
            postdata = request.POST
            # -1 is haven't been set, 0 is even split 1 is uneven split
            defaultsplitoption = postdata['itemsplitmode']
            expensename = postdata['expensename']
            # delete tempexpenses[deleteIndex] if deleteindex isn't -1
            deleteIndex = util.extractDelete(dict(postdata))
            # handle user delete item
            if deleteIndex != -1:
                db.delete_tempexpense(pages[4], deleteIndex)
            # handle user submit item to temp expense and submitting temp expense as a whole
            else:
                # update temporary expense
                index = 0
                while index < db.get_tempexpense_length(pages[4]):
                    newitem = datastructs.item(postdata.get(f'itemname{index}'), postdata.get(
                        f'itemprice{index}'), postdata.get(f'itemquantity{index}'), postdata.get(f'itemsplitmode{index}')).toJson()
                    db.update_tempexpenses(pages[4], newitem, index)
                    index += 1
                # user submitted an temporary expense request
                if request.POST.get('submititem'):
                    # submit item AFTER update
                    errormsg = db.submit_tempexpenses(pages[4], datastructs.item(postdata.get('itemname'), postdata.get(
                        'itemprice'), postdata.get('itemquantity'), postdata.get('itemsplitmode')).toJson())
                # user pressed the submit button (submit temp expense as pending expense)
                elif request.POST.get('submitexpense'):
                    errormsg = db.pend_expense(pages[4], expensename)
                elif request.POST.get('submitscan'):
                    return redirect(f'/scanfile/{pages[4]}')
                
                # delete all temp expenses when user clicks cancel
                elif request.POST.get('deletetempexpenses'):
                    print("deleting...")
                    db.get_tempexpense_length(pages[4])
                    for i in range(db.get_tempexpense_length(pages[4])):
                        db.delete_tempexpense(pages[4], 0)
                    print(db.get_tempexpense_length(pages[4]))
        pendexpenses = util.process_pendingexpenses(
            pages[4], groupinfo, db)
        tempexpenses = db.get_tempexpenses(pages[4])
    db.attach_amount_owe(groupinfo)
    return render(request, 'landing.html', {'groups': groups, 'groupindex': groupindex,'name': name, 'pages': pages, 'groupmembers': groupinfo, 'tempexpenses': tempexpenses, 'pendingexpenses': pendexpenses, 'tempitemcount': len(tempexpenses), 'errmsg': errormsg, 'defaultsplitoption': defaultsplitoption, 'expname': expensename, 'infomsg': resolved})

# survey send out to everyone to collect info about who ordered what
def survey(request, **kwargs):
    expensename, groupcode = kwargs.get('expensename'), kwargs.get('groupcode')
    db = Database(request.session['email'])
    finalitems = Util().get_items(db.get_pending_expenses(groupcode), expensename)
    if request.method == 'POST':
        surveydata = request.POST
        db.submit_survey(expensename, groupcode, surveydata)  # submit survey to group
        response = redirect(f'/landing/groups/{db.get_group_index(groupcode)}')
        return response
        
    return render(request, 'survey.html', {'expensename': expensename, 'items': finalitems})


# page to display what each person ordered, user can cancel the pending expense while there're still people who haven't completed their survey
def results(request, **kwargs):
    expensename, groupcode, state = kwargs.get('expensename'), kwargs.get('groupcode'), kwargs.get('state')
    db = Database(request.session['email'])
    surveydata = db.get_survey_data(groupcode, expensename)
    if request.method == 'POST':
        if 'resolve' in request.POST:
            db.resolve_expense(surveydata, groupcode, expensename)
            response = redirect(f'/landing/groups/{db.get_group_index(groupcode)}?resolved=Expense resolved!')
            return response
    return render(request, 'results.html', {'surveydata': surveydata})


def scanfile(request, **kwargs):
    groupcode = kwargs.get('groupcode')
    db = Database(request.session['email'])
    if request.method == 'POST':
        img_string = request.POST['photo']
        urllib.request.urlretrieve(img_string, "photo.png")
        allitems = scanner.aspriceScan("photo.png")
        db.submit_scanneditems(groupcode, allitems)
        result = db.decrement_scans_allowed()
        # PIL.Image.open("photo.png").show()
        
        return redirect(f'/landing/groups/{db.get_group_index(groupcode)}')
        
    return render(request, 'scanfile.html')
    
    
