from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from model_utils.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime


# ------------------------------
# Enums et choix partagés
# ------------------------------
class Role(models.TextChoices):
    ADMINISTRATEUR = "ADMIN", "Administrateur"
    ENSEIGNANT = "PROF", "Enseignant"
    ETUDIANT = "ETUD", "Étudiant"

class StatutTache(models.TextChoices):
    EN_ATTENTE = "ATTENTE", "En attente"
    EN_TRAITEMENT = "TRAITEMENT", "En cours de traitement"
    TERMINE = "TERMINE", "Terminé"
    ECHEC = "ECHEC", "Échec"

class StatutEnvoi(models.TextChoices):
    NON_ENVOYE = "NON_ENVOYE", "Non envoyé"
    ENVOYE = "ENVOYE", "Envoyé"
    ECHEC_ENVOI = "ECHEC_ENVOI", "Échec de l'envoi"


# ------------------------------
# Modèle Utilisateur de base

class User(AbstractUser):
    role = models.CharField(max_length=5, choices=Role.choices, default=Role.ETUDIANT)
    telephone = PhoneNumberField(blank=True, null=True)
    email_parent = models.EmailField("Email du parent", blank=True, null=True)
    date=models.DateTimeField(default=datetime.now)
    
    # Social Links
    
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn URL")
    github_username = models.CharField(max_length=50, blank=True, verbose_name="GitHub Username")


    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    @property
    def is_admin(self):
        return self.role == Role.ADMINISTRATEUR
    
    @property
    def is_teacher(self):
        return self.role == Role.ENSEIGNANT
    
    @property
    def is_student(self):
        return self.role == Role.ETUDIANT
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"


# ------------------------------
# Modèles du référentiel scolaire
# ------------------------------
class AnneeAcademique(TimeStampedModel):
    libelle = models.CharField("Année", max_length=20, unique=True) # Ex: "2024-2025"
    actif = models.BooleanField(default=True)
    date_debut = models.DateField()
    date_fin = models.DateField()

    class Meta:
        verbose_name = "Année académique"
        verbose_name_plural = "Années académiques"
        ordering = ["-date_debut"]

    def clean(self):
        # Empêche d'avoir deux années actives en même temps
        if self.actif:
            if AnneeAcademique.objects.filter(actif=True).exclude(pk=self.pk).exists():
                raise ValidationError("Il ne peut y avoir qu'une seule année active à la fois")

    @classmethod
    def get_active(cls):
        return cls.objects.filter(actif=True).first()
    
    def __str__(self):
        return self.libelle


class Classe(TimeStampedModel):
    nom = models.CharField(max_length=10) # Ex: "3ème A", "Tle S2"
    niveau = models.CharField(max_length=50) # Ex: "Troisième", "Terminale S"
    annee = models.ForeignKey(AnneeAcademique, on_delete=models.CASCADE, related_name="classes")

    class Meta:
        verbose_name = "Classe"
        unique_together = ['nom', 'annee'] # Pas deux classes mêmes nom même année
        ordering = ["niveau", "nom"]

    def __str__(self):
        return f"{self.nom} ({self.annee})"


class Matiere(TimeStampedModel):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    coefficient = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    annee = models.ForeignKey(AnneeAcademique, on_delete=models.CASCADE, related_name="matieres")

    class Meta:
        verbose_name = "Matière"
        unique_together = ['code', 'annee']
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} (coef {self.coefficient})"


class Periode(TimeStampedModel):
    """ Trimestre, semestre, séquence, entièrement configurable """
    libelle = models.CharField(max_length=50) # Ex: "1er Trimestre"
    annee = models.ForeignKey(AnneeAcademique, on_delete=models.CASCADE, related_name="periodes")
    date_debut = models.DateField()
    date_fin = models.DateField()
    cloturee = models.BooleanField("Période clôturée", default=False, help_text="Plus aucune note ne peut être modifiée une fois clôturée")

    class Meta:
        verbose_name = "Période"
        unique_together = ['libelle', 'annee']
        ordering = ["date_debut"]

    def __str__(self):
        return f"{self.libelle} {self.annee}"


# ------------------------------
# Relations d'affectation
# ------------------------------
class Inscription(TimeStampedModel):
    """ Lien entre un étudiant et sa classe pour une année donnée.
    IMPORTANT : On ne met JAMAIS de champ classe sur l'étudiant : un étudiant change de classe chaque année """
    etudiant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': Role.ETUDIANT}, related_name="inscriptions")
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name="inscriptions")
    annee = models.ForeignKey(AnneeAcademique, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Inscription"
        unique_together = ['etudiant', 'annee'] # Un étudiant ne peut être inscrit qu'une fois par année
        ordering = ["etudiant__last_name"]

    def clean(self):
        self.annee = self.classe.annee

    def __str__(self):
        return f"{self.etudiant} - {self.classe}"


class AffectationEnseignant(TimeStampedModel):
    """ Définit quel enseignant enseigne quelle matière dans quelle classe.
    C'est la base de TOUT votre système de permissions """
    enseignant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': Role.ENSEIGNANT}, related_name="affectations")
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Affectation enseignant"
        unique_together = ['enseignant', 'matiere', 'classe']

    def __str__(self):
        return f"{self.enseignant} - {self.matiere} {self.classe}"


# ------------------------------
# Coeur métier : Notes
# ------------------------------
class Note(TimeStampedModel):
    etudiant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': Role.ETUDIANT}, related_name="notes")
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    periode = models.ForeignKey(Periode, on_delete=models.CASCADE)
    note = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(20)])
    appreciation = models.TextField(blank=True)
    saisi_par = models.ForeignKey( User, on_delete=models.PROTECT, related_name="notes_saisies", limit_choices_to={'role': Role.ENSEIGNANT} )

    class Meta:
        verbose_name = "Note"
        # CONTRAINTE LA PLUS IMPORTANTE DU PROJET : Empêche TOUS les bugs de doublons
        unique_together = ['etudiant', 'matiere', 'periode']
        indexes = [
            models.Index(fields=['etudiant', 'periode'])
          
        ]

    def clean(self):
        # Empêche la modification de notes sur une période clôturée
        if self.periode.cloturee:
            raise ValidationError("Impossible de modifier une note sur une période clôturée")

    def __str__(self):
        return f"{self.etudiant} - {self.matiere} : {self.note}/20"


# ------------------------------
# MODÈLE SPÉCIFIQUE CELERY - LE PLUS IMPORTANT
# ------------------------------
class Bulletin(TimeStampedModel):
    """ Suivi de tous les bulletins générés et envoyés.
    Ce modèle est la clé qui va vous éviter de lancer des tâches Celery dans le vide.
    Vous savez à tout moment quel est le statut de chaque bulletin.
    """
    etudiant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bulletins")
    periode = models.ForeignKey(Periode, on_delete=models.CASCADE)
    statut_generation = models.CharField(max_length=15, choices=StatutTache.choices, default=StatutTache.EN_ATTENTE)
    statut_envoi = models.CharField(max_length=15, choices=StatutEnvoi.choices, default=StatutEnvoi.NON_ENVOYE)
    
    # Référence Celery
    task_id = models.UUIDField(blank=True, null=True, editable=False)
    
    # Fichier généré
    fichier = models.FileField(upload_to="bulletins/%Y/", blank=True, null=True)
    
    # Logs pour le debug
    erreur = models.TextField(blank=True)

    class Meta:
        unique_together = ['etudiant', 'periode']
        ordering = ["-created"]

    def __str__(self):
        return f"Bulletin {self.etudiant} {self.periode} : {self.get_statut_generation_display()}"