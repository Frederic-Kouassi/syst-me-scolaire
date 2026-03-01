
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from students.views.home import *
from students.views.registration_views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('',  Home_texte.as_view(), name="texte"),
    path('index', Home_index.as_view(), name="index"),
    path('user/', Home_user.as_view(), name="user"),
    path('analytic/', Home_analytic.as_view(), name="analytic"),
    path('setting/',  Home_setting.as_view(), name="settings"),
     path('inbox',  Home_inbox.as_view(), name="inbox"),
     path('etudiant/', Home_etudiant.as_view(), name="etudiant"),
     path('t_classe', Home_classes.as_view(), name="t_classe"),
     
      path('annee', Ajouter_annee.as_view(), name="annee"),

  
     path('inscrit/', inscrit_etu.as_view(), name="inscrit"),
     path('affectation/', affectation_ens.as_view(), name="affectation"),
     path('classe/', ajouter_cls.as_view(), name="classe"),
    path('matiere/', Ajouter_matieres.as_view(), name="matiere"),
    
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    
    
    path('api/classe/<int:classe_id>/', api_classe_data, name='api_classe_data'),
    path('api/note/ajouter/', api_ajouter_note, name='api_ajouter_note'),


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)