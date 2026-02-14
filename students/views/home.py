from django.shortcuts import render,redirect
from django.views import View
from django.shortcuts import render
from students.models import *
from django.utils.timezone import now
from django.utils import timezone
from django.views import View
from django.contrib import messages

# Create your views here.
from ..tasks import index 

 


def texte(request):
    
   
   
    return render(request, 'global_data/texte.html', {'result': 'redis'})



def index(request):
    affectations = AffectationEnseignant.objects.select_related('enseignant', 'classe', 'matiere').all()
    enseignants = User.objects.filter(role=Role.ENSEIGNANT)
    users_count = User.objects.count()
    classe= Classe.objects.count()
    # nombre total
    total_enseignants = enseignants.count() 
    # Récupérer les dernières activités (notes saisies) par les enseignants
    recent_activities = Note.objects.select_related('saisi_par', 'matiere', 'etudiant') \
                            .filter(saisi_par__role='PROF', created__gte=now()-timezone.timedelta(days=1)) \
                            .order_by('-created')[:10]  # limite à 10 dernières activités

    return render(request, 'index.html', {'enseignants': affectations, 'total':total_enseignants, 'recent_activities': recent_activities, })


def user(request):
    all_users = User.objects.all()
    users_count = User.objects.all().count() 
    invite = User.objects.filter(role=Role.INVITE).count()
    enseignant = User.objects.filter(role=Role.ENSEIGNANT).count()
    
    inscription = Inscription.objects.count()
    
    return render(
        request, 
        'global_data/users.html', 
        {
            'users': all_users,
            'user_count': users_count,
            'inscrit': inscription,
            'invite': invite,
            'matiere': enseignant
        }
    )


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






class inscrit_etu(View):
    templates=  'manager/inscription_etu.html'
    
    def get(self, request):
        etudiants = User.objects.filter(role=Role.INVITE).order_by('last_name')
         
        classes = Classe.objects.all().order_by('nom')
        annees = AnneeAcademique.objects.all().order_by('date_debut')
        context = {
            'etudiants': etudiants,
            'classes': classes,
            'annees': annees
        }
        return render(request, self.templates, context)
    
    
    def post(self, request):
        etudiant_id = request.POST.get('etudiant')
        classe_id = request.POST.get('classe')

        if not etudiant_id or not classe_id:
            messages.error(request, "Tous les champs sont obligatoires !")
            return redirect('inscrit')

        classe = Classe.objects.get(id=classe_id)

        # Vérifier si l'étudiant est déjà inscrit cette année
        if Inscription.objects.filter(etudiant_id=etudiant_id, annee=classe.annee).exists():
            messages.error(request, "Cet étudiant est déjà inscrit pour cette année !")
            return redirect('inscrit')

        # Création de l'inscription
        Inscription.objects.create(
            etudiant_id=etudiant_id,
            classe=classe,
            annee=classe.annee
        )
        messages.success(request, "Inscription effectuée avec succès !")
        return redirect('inscrit')


class affectation_ens(View):
    templates= 'manager/affectation_ens.html'
    
    def get(self, request):
        enseignants = User.objects.filter(role=Role.ENSEIGNANT).order_by('last_name')
        matieres = Matiere.objects.all().order_by('nom')
        classes = Classe.objects.all().order_by('nom')
        context = {
            'enseignants': enseignants,
            'matieres': matieres,
            'classes': classes
        }
        return render(request, self.templates, context)
    
    
    
class ajouter_cls(View):
    templates=  'manager/ajouter_cls.html'
    
    def get(self, request):
       
        context = {}
        return render(request, self.templates, context)