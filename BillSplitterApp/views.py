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
        db = backendservice.database()
        db.connect_db()
        email = data.get('email')
        password = data.get('pass')
        db.insert_data('test',{'email':email, 'pass':password})
    return render(request, 'login.html')
