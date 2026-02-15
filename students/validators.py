import re
from django.core.exceptions import ValidationError

class CustomPasswordValidator:

    def validate(self, password, user=None):

        if not re.search(r'[A-Z]', password):
            raise ValidationError("Le mot de passe doit contenir au moins une majuscule.")

        if not re.search(r'[a-z]', password):
            raise ValidationError("Le mot de passe doit contenir au moins une minuscule.")

        if not re.search(r'[0-9]', password):
            raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")

        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            raise ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")

    def get_help_text(self):
        return "Votre mot de passe doit contenir majuscule, minuscule, chiffre et caractère spécial."
