from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Classe, Matiere, AnneeAcademique, Periode, Inscription, AffectationEnseignant, Note, Bulletin

# -----------------------------
# Custom User
# -----------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Champs affichés dans l'admin
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'telephone', 'email_parent')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')

# -----------------------------
# Autres modèles
# -----------------------------
@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau', 'annee')
    list_filter = ('niveau', 'annee')
    search_fields = ('nom',)

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'coefficient', 'annee')
    list_filter = ('annee',)
    search_fields = ('nom', 'code')

@admin.register(AnneeAcademique)
class AnneeAcademiqueAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'actif', 'date_debut', 'date_fin')
    list_filter = ('actif',)

@admin.register(Periode)
class PeriodeAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'annee', 'date_debut', 'date_fin', 'cloturee')
    list_filter = ('annee', 'cloturee')

@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'classe', 'annee')
    list_filter = ('annee', 'classe')

@admin.register(AffectationEnseignant)
class AffectationEnseignantAdmin(admin.ModelAdmin):
    list_display = ('enseignant', 'matiere', 'classe')
    list_filter = ('classe', 'matiere')

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'matiere', 'periode', 'note', 'saisi_par')
    list_filter = ('periode', 'matiere')

@admin.register(Bulletin)
class BulletinAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'periode', 'statut_generation', 'statut_envoi')
    list_filter = ('periode', 'statut_generation', 'statut_envoi')

# Register your models here.
