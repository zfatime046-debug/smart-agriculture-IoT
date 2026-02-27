from django.contrib import admin
from .models import *
from .models import RegleAutomatisation

admin.site.register(Serre)
admin.site.register(Capteur)
admin.site.register(Mesure)
admin.site.register(Plante)
admin.site.register(Actionneur)
admin.site.register(Commande)
admin.site.register(RegleAutomatisation)
admin.site.register(Utilisateur)
