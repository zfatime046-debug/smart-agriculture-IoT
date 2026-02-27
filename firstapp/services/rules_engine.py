from django.db import transaction
from django.utils import timezone
from firstapp.models import Mesure, Actionneur


def key_from_type(sensor_type: str) -> str:
    s = (sensor_type or "").strip().lower()
    mapping = {
        "température air": "TEMPÉRATURE_AIR",
        "humidité air": "HUMIDITÉ_AIR",
        "humidité sol": "HUMIDITÉ_SOL",
        "luminosité (lux)": "LUX",
        "co2": "CO2",
        "ph solution": "PH_SOLUTION",
        "ec solution": "EC_SOLUTION",
        "détection fuite d’eau": "FUIT_EAU",
        "detection fuite d'eau": "FUIT_EAU",
    }
    return mapping.get(s, s.upper().replace(" ", "_"))


def _set_etat(actionneur_type: str, etat: bool, serre):
    # IMPORTANT: filtre par serre + utilise etat_actuel (chez toi)
    Actionneur.objects.filter(
        serre=serre,
        type__iexact=actionneur_type
    ).update(etat_actuel=("on" if etat else "off"))


def last_val(serre, capteur_type_contient: str):
    m = Mesure.objects.filter(
        capteur__serre=serre,
        capteur__type__icontains=capteur_type_contient
    ).order_by("-horodatage").first()
    return float(m.valeur_mesuree) if m else None


@transaction.atomic
def appliquer_regles(mesure: Mesure):
    serre = mesure.capteur.serre
    cap_type = (mesure.capteur.type or "").lower()
    val = float(mesure.valeur_mesuree)

    # Valeurs courantes (si la mesure envoyée correspond) sinon dernière valeur en DB
    t = val if "température air" in cap_type else last_val(
        serre, "Température air")
    h = val if "humidité air" in cap_type else last_val(serre, "Humidité air")
    hs = val if "humidité sol" in cap_type else last_val(serre, "Humidité sol")
    ph = val if "ph solution" in cap_type else last_val(serre, "pH solution")
    lux = val if "luminosité" in cap_type else last_val(serre, "Luminosité")
    co2 = val if cap_type.strip() == "co2" else last_val(serre, "CO2")
    fuite = val if "fuite" in cap_type else last_val(serre, "fuite")

    resultats = {}

    # 1) Ventilation si chaud : T > 30
    if t is not None:
        etat = t > 30
        _set_etat("Ventilation (extracteur)", etat, serre)
        _set_etat("Ventilation zénithale", etat, serre)
        resultats["ventilation"] = etat

    # 2) Brumisation si air sec : H < 55 ET T > 28
    if (h is not None) and (t is not None):
        etat = (h < 55) and (t > 28)
        _set_etat("Brumisation", etat, serre)
        _set_etat("Brumisation haute pression", etat, serre)
        resultats["brumisation"] = etat

    # 3) Irrigation si sol sec : HS < 25
    if hs is not None:
        etat = hs < 25
        _set_etat("Electrovanne irrigation", etat, serre)
        _set_etat("Électrovanne principale", etat, serre)
        resultats["irrigation"] = etat

    # 4) Alerte pH : pH < 5.5 OU > 6.5
    if ph is not None:
        alerte = (ph < 5.5) or (ph > 6.5)
        _set_etat("Alarme sonore", alerte, serre)
        resultats["alerte_ph"] = alerte

    # 6) Ombrage : LUX > 500
    if lux is not None:
        etat = lux > 500
        _set_etat("Ombrage automatique", etat, serre)
        resultats["ombrage"] = etat

    # 5) Sécurité fuite d’eau : FUIT_EAU = 1
    if fuite is not None:
        alerte = int(fuite) == 1
        _set_etat("Alarme sonore", alerte, serre)
        resultats["fuite_eau"] = alerte

# 7) CO2 : CO2 > 800
    if co2 is not None:
        etat = co2 > 800
        # adapte le nom exact de ton actionneur si différent
        _set_etat("Injecteur CO2", etat, serre)
        resultats["co2"] = etat

    return resultats
