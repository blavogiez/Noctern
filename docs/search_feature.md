# Fonctionnalité de Recherche

Cette fonctionnalité implémente une barre de recherche inspirée de VSCode pour l'éditeur AutomaTeX.

## Utilisation

1. Appuyez sur `Ctrl+F` pour ouvrir la barre de recherche
2. Saisissez le terme à rechercher dans le champ de texte
3. Les correspondances seront automatiquement mises en surbrillance dans le document
4. Utilisez les boutons « Précédent » et « Suivant » pour naviguer entre les correspondances
5. Le compteur affiche la position actuelle parmi le nombre total de correspondances (ex: "2 / 5")
6. Appuyez sur `Échap` ou cliquez sur le bouton de fermeture pour fermer la barre de recherche

## Fonctionnalités

- **Recherche en temps réel** : Les résultats sont mis à jour automatiquement lors de la saisie
- **Mise en surbrillance** : Toutes les correspondances sont mises en surbrillance dans le document
- **Navigation** : Navigation intuitive entre les correspondances avec les boutons de navigation
- **Compteur** : Affichage clair de la position actuelle parmi le nombre total de correspondances
- **Sensibilité à la casse** : Option pour activer/désactiver la sensibilité à la casse
- **Fermeture rapide** : Fermeture avec la touche Échap ou le bouton de fermeture

## Raccourcis clavier

- `Ctrl+F` : Ouvrir la barre de recherche
- `Entrée` : Aller à la correspondance suivante
- `Maj+Entrée` : Aller à la correspondance précédente
- `Échap` : Fermer la barre de recherche

## Design

La barre de recherche utilise un design moderne et épuré avec :
- Icônes SVG élégantes
- Espacements équilibrés
- Typographie claire
- Transitions douces à l'affichage/disparition