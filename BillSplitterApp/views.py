from django.shortcuts import render
from django.http import HttpResponse
import datetime

# test with current_datetime
def current_datetime(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)


def login(request):
    return render(request, 'BillSplitterApp/login-form-v1/login_v1/index.html')