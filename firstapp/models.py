from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Serre(models.Model):
    id_serre = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=50)
    localisation = models.CharField(max_length=100)
    surface = models.DecimalField(max_digits=8, decimal_places=2)
    type_culture = models.CharField(max_length=50)
    statut = models.CharField(max_length=20)

    def __str__(self):
        return self.nom


class Capteur(models.Model):
    id_capteur = models.AutoField(primary_key=True)
    serre = models.ForeignKey(
        Serre, on_delete=models.CASCADE, related_name="capteurs")
    type = models.CharField(max_length=30)
    date_installation = models.DateField()
    etat = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.type} (Serre {self.serre.nom})"


class Mesure(models.Model):
    id_mesure = models.AutoField(primary_key=True)
    capteur = models.ForeignKey(
        Capteur, on_delete=models.CASCADE, related_name="mesures")
    valeur_mesuree = models.DecimalField(max_digits=8, decimal_places=4)
    unite_mesure = models.CharField(max_length=10)
    horodatage = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.valeur_mesuree} {self.unite_mesure}"


class Utilisateur(models.Model):
    id_utilisateur = models.AutoField(primary_key=True)
    id_user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=100, unique=True)
    role = models.CharField(max_length=30)


class Plante(models.Model):
    id_plante = models.AutoField(primary_key=True)
    serre = models.ForeignKey(
        Serre, on_delete=models.CASCADE, related_name="plantes")
    espece = models.CharField(max_length=50)
    variete = models.CharField(max_length=50)
    stade_croissance = models.CharField(max_length=30)
    date_plantation = models.DateField()
    densite_plantation = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.espece} - {self.variete}"


class Actionneur(models.Model):
    id_actionneur = models.AutoField(primary_key=True)
    serre = models.ForeignKey(
        Serre, on_delete=models.CASCADE, related_name="actionneurs")
    type = models.CharField(max_length=30)
    etat_actuel = models.CharField(max_length=20)
    puissance = models.DecimalField(max_digits=6, decimal_places=2)
    date_installation = models.DateField()

    updated_at = models

    def __str__(self):
        return f"{self.type} (Serre {self.serre.nom})"


class RegleAutomatisation(models.Model):
    id_regle = models.AutoField(primary_key=True)
    serre = models.ForeignKey(
        Serre, on_delete=models.CASCADE, null=True, blank=True)
    nom = models.CharField(max_length=50)
    condition_declenchement = models.CharField(max_length=200)
    actionneur = models.ForeignKey(
        Actionneur, on_delete=models.SET_NULL, null=True, blank=True)
    # "on", "off", "alerte", etc.
    action = models.CharField(max_length=30, default="on")
    duree_minutes = models.PositiveIntegerField(null=True, blank=True)
    statut_activation = models.CharField(max_length=20)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} (Serre {self.serre.nom if self.serre else 'toutes'})"


class Commande(models.Model):
    id_commande = models.AutoField(primary_key=True)
    actionneur = models.ForeignKey(
        Actionneur, on_delete=models.CASCADE, related_name="commandes")
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    regle = models.ForeignKey(RegleAutomatisation, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name="commandes")
    date_declenchement = models.DateField()
    heure_declenchement = models.TimeField()
    statut = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande #{self.id_commande} - {self.statut}"
