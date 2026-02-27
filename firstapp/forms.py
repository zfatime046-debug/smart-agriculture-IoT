from firstapp.models import Commande, Actionneur
from django import forms
from .models import Utilisateur


class UtilisateurForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["nom", "prenom", "email", "role"]


class CommandeManuelleForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ["actionneur"]
