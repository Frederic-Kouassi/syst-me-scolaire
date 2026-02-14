from django.shortcuts import render
from django.views import View
from django.shortcuts import render
from students.models import *
# Create your views here.
from ..tasks import index 

 


def texte(request):
    
   
   
    return render(request, 'global_data/texte.html', {'result': 'redis'})

def index(request):
    return render(request, 'index.html')


def user(request):
    all_users = User.objects.all()
    users_count = User.objects.count()
    classe= Classe.objects.count()
    matiere= Matiere.objects.count()
    
    inscription= Inscription.objects.count()
    return render(request, 'global_data/users.html', {'users': all_users, 'user_count':users_count, 'inscrit':inscription, 'classe':classe, 'matiere':matiere})


def analytic(request):
    return render(request, 'global_data/analytics.html')



def setting(request):
    return render(request, 'global_data/settings.html')


def inbox(request):
    return render(request, 'global_data/inbox.html')
def etudiant(request):
    inscriptions = Inscription.objects.select_related('etudiant', 'classe').all()

    for inscription in inscriptions:
        # Récupérer toutes les affectations pour la classe
        affectations = AffectationEnseignant.objects.filter(classe=inscription.classe).select_related('enseignant')

        # Liste des noms d'enseignants uniques
        enseignants = list({f"{a.enseignant.first_name} {a.enseignant.last_name}" for a in affectations})
        inscription.enseignants = enseignants

        # On peut aussi garder les matières si nécessaire
        matieres = [a.matiere.nom for a in affectations]
        inscription.matieres = matieres

    return render(request, 'global_data/etudiant.html', {
        'etu_inscrit': inscriptions,
    })

