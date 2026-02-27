import re
import threading
import unicodedata

from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from firstapp.services.rules_engine import appliquer_regles
from .models import Mesure, RegleAutomatisation, Commande, Utilisateur


# Extrait: "Humidité sol < 25" même si texte complet
COND_RE = re.compile(
    r"(.+?)\s*(>=|<=|==|>|<|=)\s*([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE
)


def normalize(text: str) -> str:
    s = (text or "").strip().lower()
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    s = re.sub(r"\s+", " ", s)
    return s


def compare(val: float, op: str, seuil: float) -> bool:
    if op == ">":
        return val > seuil
    if op == "<":
        return val < seuil
    if op == ">=":
        return val >= seuil
    if op == "<=":
        return val <= seuil
    if op in ("=", "=="):
        return val == seuil
    return False


def auto_off(actionneur):
    actionneur.etat_actuel = "off"
    actionneur.save(update_fields=["etat_actuel"])


@receiver(post_save, sender=Mesure)
def on_new_mesure(sender, instance, created, **kwargs):
    if not created:
        return

    serre = instance.capteur.serre
    capteur_type = normalize(instance.capteur.type)
    valeur = float(instance.valeur_mesuree)

    user_system = Utilisateur.objects.first()

    regles = (
        RegleAutomatisation.objects
        .filter(statut_activation__iexact="active")
        .filter(Q(serre=serre) | Q(serre__isnull=True))
        .select_related("actionneur")
    )

    for r in regles:
        cond_raw = normalize(r.condition_declenchement)

        # garder seulement la partie avant "alors"
        if "alors" in cond_raw:
            cond_raw = cond_raw.split("alors")[0]

        # enlever "si"
        cond_raw = cond_raw.replace("si ", "")

        # enlever %
        cond_raw = cond_raw.replace("%", "")

        m = COND_RE.search(cond_raw)
        if not m:
            continue

        left, op, seuil = normalize(m.group(1)), m.group(2), float(m.group(3))

        if left not in capteur_type:
            continue

        if not compare(valeur, op, seuil):
            continue

        actionneur = r.actionneur
        if not actionneur:
            continue

        now = timezone.localtime()

        with transaction.atomic():
            Commande.objects.create(
                actionneur=actionneur,
                utilisateur=user_system,
                date_declenchement=now.date(),
                heure_declenchement=now.time().replace(microsecond=0),
                statut="executee",
                regle=r
            )

            actionneur.etat_actuel = "on"
            actionneur.save(update_fields=["etat_actuel"])

        # gestion durée
        if hasattr(r, "duree_minutes") and r.duree_minutes:
            t = threading.Timer(
                int(r.duree_minutes) * 60,
                auto_off,
                args=(actionneur,)
            )
            t.daemon = True
            t.start()
