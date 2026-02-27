from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from .views import creer_commande_manuelle

urlpatterns = [
    path("home/", views.home_list, name="home_list"),
    path("serre/", views.serre_list, name="serre_list"),
    path("capteur/", views.capteur_list, name="capteur_list"),
    path("mesure/", views.mesure_list, name="mesure_list"),
    path("plante/", views.plante_list, name="plante_list"),
    path("actionneur/", views.actionneur_list, name="actionneur_list"),
    path("commande/", views.commande_list, name="commande_list"),
    path("regle/", views.regle_list, name="regle_list"),

    path("utilisateur/", views.utilisateur_list, name="utilisateur_list"),
    path("utilisateur/create/", views.utilisateur_create,
         name="utilisateur_create"),
    path("utilisateur/<int:id>/update/",
         views.utilisateur_update, name="utilisateur_update"),
    path("utilisateur/<int:id>/delete/",
         views.utilisateur_delete, name="utilisateur_delete"),
    path("register/", views.register, name="register"),
    path("", LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("commandes/creer/", creer_commande_manuelle, name="commande_creer"),

]
