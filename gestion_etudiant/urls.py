
from django.contrib import admin
from django.urls import path
from students.views.home import *
from students.views.registration_views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('index', index, name="index"),
    path('user/', user, name="user"),
    path('analytic/', analytic, name="analytic"),
   
    path('setting/', setting, name="settings"),
    path('', texte, name="texte"),
     path('user/', user, name="user"),
     
     path('inbox', inbox, name="inbox"),
     path('etudiant/', etudiant, name="etudiant"),

    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name='logout'),
]
