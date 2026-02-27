from firstapp.models import RegleAutomatisation, Actionneur
from .models import Commande
from .forms import CommandeManuelleForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils import timezone
from .models import RegleAutomatisation
from django.db.models import Prefetch


from .models import (
    Serre, Capteur, Mesure, Plante, Actionneur, Commande, RegleAutomatisation, Utilisateur
)
from .forms import UtilisateurForm


# =========================
# HOME
# =========================
@login_required
def home_list(request):
    # Option: petit dashboard
    context = {
        "nb_serres": Serre.objects.count(),
        "nb_capteurs": Capteur.objects.count(),
        "nb_mesures": Mesure.objects.count(),
        "nb_actionneurs": Actionneur.objects.count(),
        "nb_commandes": Commande.objects.count(),
        "nb_regles": RegleAutomatisation.objects.count(),
    }
    return render(request, "home/list.html", context)


# =========================
# SERRE
# =========================
def serre_list(request):
    serres = Serre.objects.all().order_by("id_serre")
    return render(request, "serre/list.html", {"serres": serres})


# =========================
# CAPTEUR
# =========================
def capteur_list(request):
    capteurs = Capteur.objects.select_related("serre").order_by("id_capteur")
    return render(request, "capteurs/list.html", {"capteurs": capteurs})


# =========================
# MESURE
# =========================
def mesure_list(request):
    mesures = Mesure.objects.select_related(
        "capteur__serre").order_by("-horodatage")
    return render(request, "mesures/list.html", {"mesures": mesures})


# =========================
# PLANTE
# =========================
def plante_list(request):
    plantes = Plante.objects.select_related("serre").order_by("id_plante")
    return render(request, "plantes/list.html", {"plantes": plantes})


# =========================
# ACTIONNEUR
# =========================
def actionneur_list(request):
    actionneurs = Actionneur.objects.select_related(
        "serre").order_by("id_actionneur")
    return render(request, "actionneurs/list.html", {"actionneurs": actionneurs})


# =========================
# COMMANDE
# =========================
def commande_list(request):
    commandes = Commande.objects.select_related(
        "actionneur__serre", "utilisateur"
    ).order_by("-date_declenchement", "-heure_declenchement", "-id_commande")
    return render(request, "commandes/list.html", {"commandes": commandes})


# =========================
# UTILISATEUR (CRUD)
# =========================
def utilisateur_list(request):
    utilisateurs = Utilisateur.objects.all().order_by("id_utilisateur")
    return render(request, "utilisateur/list.html", {"utilisateurs": utilisateurs})


def utilisateur_create(request):
    if request.method == "POST":
        form = UtilisateurForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("utilisateur_list")
    else:
        form = UtilisateurForm()
    return render(request, "utilisateurs/form.html", {"form": form, "title": "Ajouter un utilisateur"})


def utilisateur_update(request, id):
    utilisateur = get_object_or_404(Utilisateur, id_utilisateur=id)

    if request.method == "POST":
        form = UtilisateurForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            return redirect("utilisateur_list")
    else:
        form = UtilisateurForm(instance=utilisateur)

    return render(request, "utilisateurs/form.html", {"form": form, "title": "Modifier un utilisateur"})


def utilisateur_delete(request, id):
    utilisateur = get_object_or_404(Utilisateur, id_utilisateur=id)

    if request.method == "POST":
        utilisateur.delete()
        return redirect("utilisateur_list")

    return render(request, "utilisateurs/confirm_delete.html", {"utilisateur": utilisateur})


# =========================
# REGISTER (auth)
# =========================
def register(request):
    """
    Crée un compte Django (auth.User) pour login/logout.
    Ton modèle Utilisateur (custom) est séparé : tu peux le remplir ensuite.
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # connecte directement après inscription
            return redirect("home_list")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


@login_required
def creer_commande_manuelle(request):
    if request.method == "POST":
        form = CommandeManuelleForm(request.POST)
        if form.is_valid():
            cmd = form.save(commit=False)
            now = timezone.localtime()
            cmd.utilisateur = request.user
            cmd.date_declenchement = now.date()
            cmd.heure_declenchement = now.time().replace(microsecond=0)
            cmd.statut = "EN_ATTENTE"
            cmd.save()
            return redirect("commande_list")
    else:
        form = CommandeManuelleForm()

    return render(request, "commandes/creer.html", {"form": form})

# =========================
# REGLE
# =========================


def regle_list(request):
    commandes_qs = (
        Commande.objects
        .select_related("actionneur__serre", "utilisateur")
        .order_by("-date_declenchement", "-heure_declenchement", "-id_commande")
    )

    regles = (
        RegleAutomatisation.objects
        .prefetch_related(Prefetch("commandes", queryset=commandes_qs))
        .order_by("id_regle")
    )

    return render(request, "regles/list.html", {"regles": regles})


def pick_actionneur_for_rule(regle):
    txt = (regle.nom + " " + regle.condition_declenchement).lower()

    # ordre important: on teste d'abord les cas spécifiques
    if "brum" in txt:
        return Actionneur.objects.filter(type__icontains="Brum").first()

    if "pompe" in txt or "irrig" in txt or "goutte" in txt:
        return Actionneur.objects.filter(type__icontains="Pompe").first()

    if "inject" in txt or "fertig" in txt:
        return Actionneur.objects.filter(type__icontains="Inject").first()

    if "alarme" in txt or "alerte" in txt or "fuite" in txt:
        return Actionneur.objects.filter(type__icontains="Alarme").first()

    if "ventil" in txt:
        return Actionneur.objects.filter(type__icontains="Ventilation").first()

    # sinon rien
    return None
