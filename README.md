<div align="center">
  <img src="resources/icons/app_icon.png" alt="AutomaTeX Logo" width="128" height="128">
  
  # AutomaTeX
  
  **Une expérience LaTeX moderne et assistée par l'IA**
  
  [![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
  [![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)](#)
  
  [Fonctionnalités](#-fonctionnalités) •
  [Installation](#-installation) •
  [Démarrage rapide](#-démarrage-rapide) •
  [Raccourcis](#-raccourcis-clavier)
</div>

---

## 🌟 Présentation

AutomaTeX est un éditeur LaTeX moderne conçu pour simplifier votre workflow d'écriture tout en préservant la puissance de LaTeX. Il combine l'ergonomie d'un éditeur contemporain avec des outils d'IA locaux pour vous permettre de vous concentrer sur ce qui compte vraiment : **votre contenu**.

> 🎓 *Né de la frustration d'un étudiant face à la verbosité de LaTeX, AutomaTeX est un projet personnel qui vise à lisser les aspérités de l'expérience LaTeX.*

---

## ✨ Fonctionnalités

<div align="center">
  <table>
    <tr>
      <td width="50%" valign="top">
        <h3>🤖 IA Locale</h3>
        <ul>
          <li>Complétion et génération de texte</li>
          <li>Reformulation intelligente</li>
          <li>Traduction de documents</li>
          <li>Tout s'exécute localement avec Ollama</li>
        </ul>
      </td>
      <td width="50%" valign="top">
        <h3>🖼️ Gestion Intelligente</h3>
        <ul>
          <li>Collage d'images avec code LaTeX automatique</li>
          <li>Organisation automatique des fichiers</li>
          <li>Nettoyage des fichiers inutilisés</li>
          <li>Aperçu intégré du PDF</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td width="50%" valign="top">
        <h3>⌨️ Expérience Optimisée</h3>
        <ul>
          <li>Interface claire avec thèmes clair/sombre</li>
          <li>Surlignage syntaxique</li>
          <li>Navigation par plan du document</li>
          <li>Raccourcis clavier intuitifs</li>
        </ul>
      </td>
      <td width="50%" valign="top">
        <h3>🔒 Respect de la vie privée</h3>
        <ul>
          <li>Aucune donnée ne quitte votre machine</li>
          <li>Modèles d'IA exécutés localement</li>
          <li>Gratuit et open-source</li>
          <li>Pas de compte requis</li>
        </ul>
      </td>
    </tr>
  </table>
</div>

---

## 🚀 Installation

### 📋 Prérequis

<div align="center">
  <table>
    <tr>
      <th>Outil</th>
      <th>Description</th>
      <th>Lien</th>
    </tr>
    <tr>
      <td><b>Python 3.8+</b></td>
      <td>Langage principal de l'application</td>
      <td>
        <a href="https://www.python.org/downloads/">
          <img src="https://img.shields.io/badge/Télécharger-Python-blue?style=for-the-badge&logo=python" alt="Télécharger Python">
        </a>
      </td>
    </tr>
    <tr>
      <td><b>Distribution LaTeX</b></td>
      <td>Pour compiler les documents</td>
      <td>
        <a href="https://miktex.org/download">
          <img src="https://img.shields.io/badge/Windows-MiKTeX-orange?style=for-the-badge&logo=windows" alt="MiKTeX">
        </a>
        <a href="https://www.tug.org/mactex/">
          <img src="https://img.shields.io/badge/macOS-MacTeX-black?style=for-the-badge&logo=apple" alt="MacTeX">
        </a>
        <a href="https://www.tug.org/texlive/">
          <img src="https://img.shields.io/badge/Linux-TeXLive-yellow?style=for-the-badge&logo=linux" alt="TeX Live">
        </a>
      </td>
    </tr>
    <tr>
      <td><b>Ollama</b></td>
      <td>Moteur d'IA local</td>
      <td>
        <a href="https://ollama.com/">
          <img src="https://img.shields.io/badge/Télécharger-Ollama-FF6B35?style=for-the-badge&logo=ollama" alt="Télécharger Ollama">
        </a>
      </td>
    </tr>
  </table>
</div>

### 📦 Dépendances Python

L'application utilise plusieurs bibliothèques Python :

- `ttkbootstrap` - Interface utilisateur moderne
- `pdf2image` - Conversion PDF vers images
- `Pillow` - Traitement d'images
- `PyPDF2` - Manipulation de PDFs
- `pdfplumber` - Extraction de texte depuis les PDFs

### 🛠️ Installation pas à pas

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/your-username/AutomaTeX.git
   cd AutomaTeX
   ```

2. **Installer les dépendances Python**
   ```bash
   pip install -r requirements.txt
   ```

3. **Télécharger les modèles d'IA**
   ```bash
   # Modèles recommandés
   ollama pull mistral
   ollama pull codellama:7b-instruct
   ```

4. **Lancer l'application**
   ```bash
   python main.py
   ```

---

## 🏁 Démarrage rapide

<div align="center">
  <table>
    <tr>
      <th>Étape</th>
      <th>Action</th>
      <th>Résultat</th>
    </tr>
    <tr>
      <td>1</td>
      <td>Créer un nouveau document</td>
      <td>Fichier → Nouveau</td>
    </tr>
    <tr>
      <td>2</td>
      <td>Écrire du contenu</td>
      <td>Utiliser l'éditeur</td>
    </tr>
    <tr>
      <td>3</td>
      <td>Utiliser l'IA</td>
      <td>Ctrl+Shift+G pour générer du texte</td>
    </tr>
    <tr>
      <td>4</td>
      <td>Compiler</td>
      <td>Cliquer sur "Compiler"</td>
    </tr>
    <tr>
      <td>5</td>
      <td>Voir le PDF</td>
      <td>Le PDF s'ouvre automatiquement</td>
    </tr>
  </table>
</div>

---

## ⌨️ Raccourcis clavier

<div align="center">
  <table>
    <tr>
      <th>Fonction</th>
      <th>Raccourci</th>
      <th>Description</th>
    </tr>
    <tr>
      <td><b>Complétion IA</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>C</kbd></td>
      <td>Complète la phrase en cours</td>
    </tr>
    <tr>
      <td><b>Génération IA</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>G</kbd></td>
      <td>Génère du texte à partir d'une instruction</td>
    </tr>
    <tr>
      <td><b>Reformulation</b></td>
      <td>Sélection + <kbd>Ctrl</kbd> + <kbd>R</kbd></td>
      <td>Reformule le texte sélectionné</td>
    </tr>
    <tr>
      <td><b>Coller image</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd></td>
      <td>Colle une image du presse-papier</td>
    </tr>
    <tr>
      <td><b>Zoom +</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>+</kbd></td>
      <td>Agrandit la taille du texte</td>
    </tr>
    <tr>
      <td><b>Zoom -</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>-</kbd></td>
      <td>Réduit la taille du texte</td>
    </tr>
    <tr>
      <td><b>Compiler</b></td>
      <td>Bouton "Compiler"</td>
      <td>Compile le document LaTeX</td>
    </tr>
  </table>
</div>

---

## 📚 Guide utilisateur

### 🤖 Configuration des modèles d'IA

1. Allez dans **Paramètres** → **Gérer les modèles**
2. Sélectionnez les modèles pour chaque tâche :
   - **Complétion** : Modèle pour compléter les phrases
   - **Génération** : Modèle pour générer du texte
   - **Reformulation** : Modèle pour reformuler
   - **Débogage** : Modèle pour corriger les erreurs
   - **Style** : Modèle pour améliorer le style

### 🖼️ Utilisation du collage d'images

1. Copiez une image dans votre presse-papier
2. Appuyez sur <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd>
3. L'image est automatiquement :
   - Sauvegardée dans `figures/section/sous-section/`
   - Renommée de façon séquentielle (`fig_1.png`, `fig_2.png`, etc.)
   - Insérée avec le code LaTeX approprié

### 🌍 Traduction de documents

1. Cliquez sur le bouton **Traduire**
2. Sélectionnez la langue cible
3. Le document traduit est sauvegardé avec un préfixe (`fr_document.tex`)

---

## 🧠 Philosophie du projet

<div align="center">
  <blockquote>
    <p>
      "AutomaTeX n'est pas destiné à remplacer votre connaissance de LaTeX, mais à l'augmenter."
    </p>
  </blockquote>
</div>

Ce projet est né d'une frustration personnelle : LaTeX est puissant mais verbeux. AutomaTeX vise à préserver cette puissance tout en éliminant les tâches fastidieuses.

### 🔬 Principes directeurs

- **Local-first** : Vos données restent chez vous
- **Intuitif** : Interface pensée pour la productivité
- **Extensible** : Architecture modulaire
- **Gratuit** : Pas de frais cachés ou d'abonnement

---

## 🛠️ Leçons apprises

### ⚡ Performance vs. Complexité

Au début, j'ai tenté d'implémenter un système de vérification en temps réel qui analyserait le texte à chaque frappe. Résultat : un éditeur inutilisable avec plus de 300ms de latence par frappe.

Solution : un système de mise à jour différée qui préserve la fluidité tout en offrant un feedback quasi instantané.

### 🎯 L'IA au service de l'utilisateur

L'IA n'est pas magique en soi. Ce qui fait la différence, c'est comment ses résultats sont présentés. L'interface interactive qui permet d'accepter, rejeter ou reformuler une suggestion en un seul clic transforme l'IA d'une boîte noire en un véritable assistant.

---

## 🗺️ Feuille de route

<div align="center">
  <table>
    <tr>
      <th>Fonctionnalité</th>
      <th>Status</th>
      <th>Priorité</th>
    </tr>
    <tr>
      <td>Arborescence de fichiers</td>
      <td>À venir</td>
      <td>Haute</td>
    </tr>
    <tr>
      <td>Support LSP</td>
      <td>À venir</td>
      <td>Moyenne</td>
    </tr>
    <tr>
      <td>Raccourcis Vim/Emacs</td>
      <td>À venir</td>
      <td>Basse</td>
    </tr>
    <tr>
      <td>Intégration Git</td>
      <td>À venir</td>
      <td>Moyenne</td>
    </tr>
  </table>
</div>

---

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

<div align="center">
  <h3>🚀 Prêt à transformer votre expérience LaTeX ?</h3>
  <p>
    <a href="#-installation">
      <img src="https://img.shields.io/badge/Commencer-maintenant-4CAF50?style=for-the-badge&logo=rocket" alt="Commencer">
    </a>
    <a href="https://github.com/your-username/AutomaTeX/issues">
      <img src="https://img.shields.io/badge/Signaler%20un%20bug-rouge?style=for-the-badge&logo=github" alt="Signaler un bug">
    </a>
  </p>
  
  *Développé avec ❤️ par un étudiant passionné*
</div>