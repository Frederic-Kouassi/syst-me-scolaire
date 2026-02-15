from django.shortcuts import render,redirect
from django.views import View
from django.shortcuts import render
from students.models import *
from django.utils.timezone import now
from django.utils import timezone
from django.views import View
from django.contrib import messages
from django.core.exceptions import ValidationError

# Create your views here.
from ..tasks import index 

 
 
 
class Home_texte(View):
    templates=  'global_data/texte.html'
    
    def get(self, request):
       
        context = {'result': 'redis'}
        return render(request, self.templates, context)

 


    
class Home_index(View):
    templates=  'index.html'
    
    def get(self, request):
        affectations = AffectationEnseignant.objects.select_related('enseignant', 'classe', 'matiere').all()
        enseignants = User.objects.filter(role=Role.ENSEIGNANT)
        inscription = Inscription.objects.count()
        classe= Classe.objects.count()
        # nombre total
        total_enseignants = enseignants.count() 
    # Récupérer les dernières activités (notes saisies) par les enseignants
        recent_activities = Note.objects.select_related('saisi_par', 'matiere', 'etudiant') \
                            .filter(saisi_par__role='PROF', created__gte=now()-timezone.timedelta(days=1)) \
                            .order_by('-created')[:10]  # limite à 10 dernières activités

       
        context = {'enseignants': affectations, 
                   'total':total_enseignants,
                   'recent_activities': recent_activities,
                   'inscrit': inscription,
                   'classe':classe}
        return render(request, self.templates, context)





class Home_user(View):
    templates=   'global_data/users.html'
    
    def get(self,request):
        all_users = User.objects.all()
        users_count = User.objects.all().count() 
        invite = User.objects.filter(role=Role.INVITE).count()
        enseignant = User.objects.filter(role=Role.ENSEIGNANT).count()
    
        inscription = Inscription.objects.count()
    
        context = { 'users': all_users,
                'user_count': users_count,
                'inscrit': inscription,
                'invite': invite,
                'matiere': enseignant}
        return render(request, self.templates, context)



class Home_analytic(View):
    templates=  'global_data/analytics.html'
    
    def get(self, request):
       
        context = {}
        return render(request, self.templates, context)

 



class Home_setting(View):
    templates=  'global_data/settings.html'
    
    def get(self, request):
       
        context = {}
        return render(request, self.templates, context)

 
class Home_inbox(View):
    templates=  'global_data/inbox.html'
    
    def get(self, request):
       
        context = {}
        return render(request, self.templates, context)





 
class Home_etudiant(View):
    templates=  'global_data/etudiant.html'
    
    def get(self, request):
        inscriptions = Inscription.objects.select_related('etudiant', 'classe').all()
        etu_inscrit = Inscription.objects.count()
        invite = User.objects.filter(role=Role.INVITE).count()
        for inscription in inscriptions:
        # Récupérer toutes les affectations pour la classe
            affectations = AffectationEnseignant.objects.filter(classe=inscription.classe).select_related('enseignant')

            # Liste des noms d'enseignants uniques
            enseignants = list({f"{a.enseignant.first_name} {a.enseignant.last_name}" for a in affectations})
            inscription.enseignants = enseignants

            # On peut aussi garder les matières si nécessaire
            matieres = [a.matiere.nom for a in affectations]
            inscription.matieres = matieres
        
            context = { 'etu_inscrit': inscriptions, 'inscrit': etu_inscrit, 'visiteurs':invite}
        return render(request, self.templates, context)









class inscrit_etu(View):
    templates=  'manager/inscription_etu.html'
    
    def get(self, request):
        etudiants = User.objects.filter(role=Role.INVITE).order_by('last_name')
         
        classes = Classe.objects.all().order_by('nom')
        annees = AnneeAcademique.objects.filter(actif=True).order_by('libelle')
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
        #  Changer le rôle de l'utilisateur en ETUDIANT # adapte le chemin si nécessaire
        user = User.objects.get(id=etudiant_id)
        user.role = Role.ETUDIANT
        user.save()  # n'oublie pas de sauvegarder !

        messages.success(request, "Inscription effectuée avec succès et rôle défini sur Étudiant !")
        return redirect('user')



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
    
    
    def post(self, request):
        enseignant_id = request.POST.get('enseignant')
        matiere_id = request.POST.get('matiere')
        classe_id = request.POST.get('classe')

        if not enseignant_id or not matiere_id or not classe_id:
            messages.error(request, "Tous les champs sont obligatoires !")
            return redirect('affectation')

        # Récupération des objets
        enseignant = User.objects.get(id=enseignant_id)
        matiere = Matiere.objects.get(id=matiere_id)
        classe = Classe.objects.get(id=classe_id)

        # Vérifier si l'affectation existe déjà
        if AffectationEnseignant.objects.filter(enseignant=enseignant, matiere=matiere, classe=classe).exists():
            messages.error(request, "Cet enseignant est déjà affecté à cette matière et classe !")
            return redirect('affectation')

        # Création de l'affectation
        AffectationEnseignant.objects.create(
            enseignant=enseignant,
            matiere=matiere,
            classe=classe
        )

        #  Mettre le rôle de l'utilisateur en ENSEIGNANT
        enseignant.role = Role.ENSEIGNANT
        enseignant.save()

        messages.success(request, "Affectation effectuée avec succès et rôle défini sur Enseignant !")
        return redirect('user')

    
    
    
class ajouter_cls(View):
    templates=  'manager/ajouter_cls.html'
    
    def get(self, request):
        
         annees = AnneeAcademique.objects.filter(actif=True).order_by('libelle')
         context = {
            'annees': annees
        }
         return render(request, self.templates, context)
    
    
    def post(self, request):
        nom = request.POST.get('nom')
        niveau = request.POST.get('niveau')
        annee_id = request.POST.get('annee')

        if not nom or not niveau or not annee_id:
            messages.error(request, "Tous les champs sont obligatoires !")
            return redirect('ajout_classe')  # remplace par ton nom d'URL

        try:
            annee = AnneeAcademique.objects.get(id=annee_id)
        except AnneeAcademique.DoesNotExist:
            messages.error(request, "L'année sélectionnée est invalide !")
            return redirect('classe')

        # Vérifier l'unicité (nom + année)
        if Classe.objects.filter(nom=nom, annee=annee).exists():
            messages.error(request, f"La classe '{nom}' existe déjà pour l'année {annee.libelle}.")
            return redirect('classe')

        # Création
        Classe.objects.create(
            nom=nom,
            niveau=niveau,
            annee=annee
        )

        messages.success(request, f"La classe '{nom}' a été ajoutée avec succès !")
        return redirect('user')
    
    
    


class Ajouter_annee(View):
    templates=  'manager/ajouter_ann.html'
    
    def get(self, request):
       
        context = {}
        return render(request, self.templates, context)
    
    
    def post(self, request, *args, **kwargs):

        libelle = request.POST.get("libelle")
        date_debut = request.POST.get("date_debut")
        date_fin = request.POST.get("date_fin")
        actif = True if request.POST.get("actif") else False

        annee = AnneeAcademique(
            libelle=libelle,
            date_debut=date_debut,
            date_fin=date_fin,
            actif=actif
        )

        try:
            annee.full_clean()   # exécute clean()
            annee.save()
            messages.success(request, "Année académique ajoutée avec succès !")
            return redirect("user")

        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)

        return render(request, self.templates)