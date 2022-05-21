"""BillSplitter URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from BillSplitterApp import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login),
    path('signup/', views.signup),
    path('survey/<str:expensename>/<str:groupcode>', views.survey),
    path('landing/<str:page>/<str:groupindex>/', views.landing),
    path('results/<str:groupcode>/<str:expensename>/<str:state>', views.results),
    path('landing/<str:page>/', views.landing),
    path('scanfile/<str:groupcode>', views.scanfile),
]

# TO-DO: way static files and media files are handled need to be changed on deployment
if settings.DEBUG:
    urlpatterns += (static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
