from django.db import models
from django.utils.translation import gettext_lazy as _


# ------------------------------
# Enums et choix partagés
# ------------------------------
class Role(models.TextChoices):
    ADMINISTRATEUR = "ADMIN", "Administrateur"
    ENSEIGNANT = "PROF", "Enseignant"
    ETUDIANT = "ETUD", "Étudiant"
    INVITE = "INV", "Invite" 

class StatutTache(models.TextChoices):
    EN_ATTENTE = "ATTENTE", "En attente"
    EN_TRAITEMENT = "TRAITEMENT", "En cours de traitement"
    TERMINE = "TERMINE", "Terminé"
    ECHEC = "ECHEC", "Échec"

class StatutEnvoi(models.TextChoices):
    NON_ENVOYE = "NON_ENVOYE", "Non envoyé"
    ENVOYE = "ENVOYE", "Envoyé"
    ECHEC_ENVOI = "ECHEC_ENVOI", "Échec de l'envoi"
