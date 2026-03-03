from django.shortcuts import render,redirect
from django.views import View
from django.shortcuts import render
from students.models import *
from django.utils.timezone import now
from django.utils import timezone
from django.views import View
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Avg, F
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import update_session_auth_hash


# Create your views here.
from ..tasks import index 

 
 
 
class Home_texte(View):
    templates=  'global_data/texte.html'
    
    def get(self, request):
       
        context = {'result': 'redis'}
        return render(request, self.templates, context)
    
class Home_classes(View):
    template_name = 'global_data/classes.html'

    def get(self, request):
        classes = Classe.objects.all()

        for classe in classes:
            inscriptions       = Inscription.objects.filter(classe=classe)
            classe.nb_etudiants = inscriptions.count()
            classe.nb_matieres  = AffectationEnseignant.objects.filter(
                classe=classe
            ).values('matiere').distinct().count()

            moyennes = [m for m in (i.get_moyenne() for i in inscriptions) if m is not None]
            classe.moyenne_classe    = round(sum(moyennes) / len(moyennes), 2) if moyennes else None
            classe.meilleure_moyenne = max(moyennes) if moyennes else None
            classe.pire_moyenne      = min(moyennes) if moyennes else None

        return render(request, self.template_name, {'classes': classes})

def api_classe_data(request, classe_id):
    inscriptions = Inscription.objects.select_related('etudiant').filter(classe_id=classe_id)
    matieres     = AffectationEnseignant.objects.select_related('matiere').filter(classe_id=classe_id)
    annee_active = AnneeAcademique.get_active()
    periodes     = annee_active.periodes.filter(cloturee=False) if annee_active else []

    donnees = []
    for insc in inscriptions:
        moy = insc.get_moyenne()
        donnees.append({
            'insc':    insc,
            'moyenne': moy,
            'notes':   insc.get_notes_par_matiere(),
        })

    # Tri par moyenne décroissante → rang = position
    donnees.sort(
        key=lambda x: x['moyenne'] if x['moyenne'] is not None else -1,
        reverse=True
    )

    eleves = []
    for rang, d in enumerate(donnees, start=1):
        i = d['insc']
        eleves.append({
            'id':      i.etudiant.id,
            'nom':     i.etudiant.get_full_name(),
            'email':   i.etudiant.email,
            'tel':     str(i.etudiant.telephone) if i.etudiant.telephone else '—',
            'moyenne': d['moyenne'],                                # ← moyenne calculée
            'rang':    rang if d['moyenne'] is not None else '—',  # ← rang calculé
            'notes':   d['notes'],                                  # ← notes par matière
        })

    return JsonResponse({
        'eleves':   eleves,
        'matieres': [
            {
                'id':          a.matiere.id,
                'nom':         a.matiere.nom,
                'coefficient': a.matiere.coefficient,
            }
            for a in matieres
        ],
        'periodes': [
            {
                'id':      p.id,
                'libelle': p.libelle,
            }
            for p in periodes
        ],
    })

        
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
    template_name = 'global_data/settings.html'
    
    def get(self, request):
        user = request.user
        context = {'users': user}
        return render(request, self.template_name, context)
    
    def post(self, request):
        user = request.user
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile':
            # Validation email
            email = request.POST.get('email')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, "Cet email est déjà utilisé par un autre compte.")
                return redirect('settings')
            
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = email
            user.telephone = request.POST.get('phone')
            user.bio = request.POST.get('bio')
            
            if 'image' in request.FILES:
                user.image = request.FILES['image']
            
            user.save()
            messages.success(request, "Profil mis à jour avec succès ✅")
        
        return redirect('settings')
    
    # ------------------------------
# Messagerie
# ------------------------------

class Home_inbox(View):
    templates = 'global_data/inbox.html'

    def get(self, request):
        messages_recus = Message.objects.filter(
            recipient=request.user,
            is_archived=False,
            is_deleted_by_recipient=False
        )

        # Stats cards
        total    = Message.objects.filter(recipient=request.user, is_deleted_by_recipient=False).count()
        non_lus  = messages_recus.filter(is_read=False).count()
        envoyes  = Message.objects.filter(sender=request.user, is_deleted_by_sender=False).count()
        archives = Message.objects.filter(recipient=request.user, is_archived=True).count()

        # Premier message affiché par défaut
        premier_message = messages_recus.first()

        context = {
            'messages_recus'  : messages_recus,
            'premier_message' : premier_message,
            'total'           : total,
            'non_lus'         : non_lus,
            'envoyes'         : envoyes,
            'archives'        : archives,
            'utilisateurs'    : User.objects.exclude(id=request.user.id),
        }
        return render(request, self.templates, context)


def lire_message(request, message_id):
    """AJAX — retourne le contenu d'un message en JSON et le marque comme lu"""
    message = Message.objects.get(id=message_id, recipient=request.user)

    if not message.is_read:
        message.is_read = True
        message.save(update_fields=['is_read'])

    # Initiales de l'expéditeur
    sender = message.sender
    if sender.first_name and sender.last_name:
        initials = f"{sender.first_name[0]}{sender.last_name[0]}".upper()
    else:
        initials = sender.username[:2].upper()

    data = {
        'id'              : message.id,
        'subject'         : message.subject,
        'body'            : message.body,
        'sender'          : sender.get_full_name() or sender.username,
        'email'           : sender.email,
        'initials'        : initials,
        'date'            : message.created.strftime('%d %b %Y à %H:%M'),
        'attachment'      : message.attachment.url if message.attachment else None,
        'attachment_name' : message.attachment.name.split('/')[-1] if message.attachment else None,
    }
    return JsonResponse(data)


def envoyer_message(request):
    """AJAX POST — envoyer un nouveau message"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'}, status=405)

    recipient_id = request.POST.get('recipient_id')
    subject      = request.POST.get('subject', '').strip()
    body         = request.POST.get('body', '').strip()
    attachment   = request.FILES.get('attachment')

    if not recipient_id or not subject or not body:
        return JsonResponse({'success': False, 'error': 'Tous les champs sont obligatoires.'}, status=400)

    try:
        recipient = User.objects.get(id=recipient_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Destinataire introuvable.'}, status=404)

    msg = Message(
        sender    = request.user,
        recipient = recipient,
        subject   = subject,
        body      = body,
    )
    if attachment:
        msg.attachment = attachment
    msg.save()

    return JsonResponse({'success': True, 'message_id': msg.id})


def repondre_message(request, message_id):
    """AJAX POST — répondre à un message"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'}, status=405)

    try:
        message_original = Message.objects.get(id=message_id, recipient=request.user)
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message introuvable.'}, status=404)

    body       = request.POST.get('body', '').strip()
    attachment = request.FILES.get('attachment')

    if not body:
        return JsonResponse({'success': False, 'error': 'La réponse ne peut pas être vide.'}, status=400)

    reponse = Message(
        sender    = request.user,
        recipient = message_original.sender,
        subject   = f"Re: {message_original.subject}",
        body      = body,
    )
    if attachment:
        reponse.attachment = attachment
    reponse.save()

    return JsonResponse({'success': True, 'message_id': reponse.id})


def supprimer_message(request, message_id):
    """AJAX POST — suppression douce d'un message"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'}, status=405)

    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message introuvable.'}, status=404)

    if message.recipient == request.user:
        message.is_deleted_by_recipient = True
    elif message.sender == request.user:
        message.is_deleted_by_sender = True
    else:
        return JsonResponse({'success': False, 'error': 'Non autorisé.'}, status=403)

    # Suppression réelle si les deux côtés ont supprimé
    if message.is_deleted_by_sender and message.is_deleted_by_recipient:
        message.delete()
    else:
        message.save()

    return JsonResponse({'success': True})


def marquer_message(request, message_id):
    """AJAX POST — toggle lu / non lu"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'}, status=405)

    try:
        message = Message.objects.get(id=message_id, recipient=request.user)
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message introuvable.'}, status=404)

    message.is_read = not message.is_read
    message.save(update_fields=['is_read'])

    return JsonResponse({'success': True, 'is_read': message.is_read})


def archiver_message(request, message_id):
    """AJAX POST — archiver un message"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'}, status=405)

    try:
        message = Message.objects.get(id=message_id, recipient=request.user)
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message introuvable.'}, status=404)

    message.is_archived = True
    message.save(update_fields=['is_archived'])

    return JsonResponse({'success': True})



 
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
    
    
    


class Ajouter_matieres(View):
    templates=  'manager/ajouter_mats.html'
    
    def get(self, request):
         annees = AnneeAcademique.objects.all()
         context = {
            "annees": annees
        }
         return render(request, self.templates, context)
    
    
class Ajouter_matieres(View):
    template_name = 'manager/ajouter_mats.html'

    def get(self, request):
       annee_active = AnneeAcademique.get_active()
       context = {"annee_active": annee_active}
       
       return render(request, self.template_name, context)
    
    def post(self, request):
        nom = request.POST.get("nom")
        code = request.POST.get("code")
        coefficient = request.POST.get("coefficient")

        annee_active = AnneeAcademique.get_active()

        if not annee_active:
            messages.error(request, "Aucune année académique active.")
            return redirect("matiere")

        try:
            Matiere.objects.create(
                nom=nom,
                code=code,
                coefficient=coefficient,
                annee=annee_active  # ✅ Champ correct
            )
            messages.success(request, "Matière ajoutée avec succès.")
            return redirect("user")

        except Exception:
            messages.error(request, "Ce code existe déjà pour l'année active.")
            return redirect("matiere")




@csrf_exempt
def api_ajouter_note(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'}, status=405)

    try:
        etudiant_id  = request.POST.get('etudiant')
        matiere_id   = request.POST.get('matiere')
        periode_id   = request.POST.get('periode')
        valeur       = request.POST.get('note')
        appreciation = request.POST.get('appreciation', '')

        if not all([etudiant_id, matiere_id, periode_id, valeur]):
            return JsonResponse({'success': False, 'error': 'Tous les champs obligatoires ne sont pas remplis.'}, status=400)

        etudiant = User.objects.get(id=etudiant_id, role=Role.ETUDIANT)

        Note.objects.create(
            etudiant     = etudiant,
            matiere_id   = matiere_id,
            periode_id   = periode_id,
            note         = float(valeur),
            appreciation = appreciation,
            saisi_par    = request.user,
        )

        return JsonResponse({'success': True})

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Étudiant introuvable.'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)