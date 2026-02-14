from django.shortcuts import render
from django.views import View
from django.shortcuts import render
from students.models import *
from django.utils.timezone import now
from django.utils import timezone

# Create your views here.
from ..tasks import index 

 


def texte(request):
    
   
   
    return render(request, 'global_data/texte.html', {'result': 'redis'})



def index(request):
    affectations = AffectationEnseignant.objects.select_related('enseignant', 'classe', 'matiere').all()
    enseignants = User.objects.filter(role=Role.ENSEIGNANT)
    
    # nombre total
    total_enseignants = enseignants.count() 
    # Récupérer les dernières activités (notes saisies) par les enseignants
    recent_activities = Note.objects.select_related('saisi_par', 'matiere', 'etudiant') \
                            .filter(saisi_par__role='PROF', created__gte=now()-timezone.timedelta(days=1)) \
                            .order_by('-created')[:10]  # limite à 10 dernières activités

    return render(request, 'index.html', {'enseignants': affectations, 'total':total_enseignants, 'recent_activities': recent_activities})



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

