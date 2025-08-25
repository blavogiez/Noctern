# Règles de Layout SOLID pour AutomaTeX Panels

## 🎯 Objectif
Créer une structure cohérente et logique pour TOUS les panels de l'application, basée sur des principes SOLID.

## 📏 Règles de Layout par Type de Panel

### 1. **PanelStyle.SPLIT** - Pour panels avec 2+ sections majeures
**Usage** : Panels complexes avec beaucoup de contenu à organiser
**Répartition** : Top pane (weight=2) + Bottom pane (weight=1)

**Panels concernés** :
- ✅ `generation` (référence parfaite)
- ✅ `table_insertion` (nouvellement optimisé)
- 🔄 `settings` (à optimiser)
- 🔄 `snippets` (à optimiser) 
- 🔄 `metrics` (à vérifier)
- 🔄 `proofreading` (SCROLLABLE → SPLIT)

**Structure type** :
```python
def create_content(self):
    paned_window = self.main_container
    self._create_main_section(paned_window)      # weight=2
    self._create_secondary_section(paned_window) # weight=1

def _create_main_section(self, parent):
    main_frame = ttk.Frame(parent)
    parent.add(main_frame, weight=2)
    content_frame = ttk.Frame(main_frame, padding=StandardComponents.PADDING)
    content_frame.pack(fill="both", expand=True)
```

### 2. **PanelStyle.SIMPLE** - Pour panels avec contenu linéaire
**Usage** : Panels avec formulaires simples ou actions uniques
**Structure** : Sections verticales empilées

**Panels concernés** :
- ✅ `rephrase` (parfait)
- ✅ `image_details` (parfait)
- ✅ `style_intensity` (parfait)
- 🔄 `translate` (à optimiser)
- 🔄 `keywords` (à optimiser)
- 🔄 `debug` (à vérifier)

**Structure type** :
```python
def create_content(self):
    main_frame = self.main_container  # Simple frame
    self._create_input_section(main_frame)
    self._create_options_section(main_frame)
    self._create_actions_section(main_frame)
```

### 3. **PanelStyle.TABBED** - Pour panels avec catégories distinctes
**Usage** : Contenu organisé par onglets thématiques
**Garde actuel** : Déjà bien structurés

**Panels concernés** :
- ✅ `prompts` (parfait)
- ✅ `global_prompts` (parfait)

### 4. **PanelStyle.SCROLLABLE** - ÉVITER (remplacer par SPLIT)
**Problème** : Ne utilise pas l'espace vertical efficacement
**Action** : Convertir vers SPLIT quand possible

## 🏗️ Architecture StandardComponents Obligatoire

### Tous les panels DOIVENT utiliser :

1. **Sections standardisées** :
   ```python
   section = StandardComponents.create_section(parent, "Title")
   ```

2. **Labels uniformes** :
   ```python
   label = StandardComponents.create_info_label(parent, "Text", "body")
   ```

3. **Boutons cohérents** :
   ```python
   buttons = [("Text", callback, "primary")]
   StandardComponents.create_button_row(parent, buttons)
   ```

4. **Inputs standardisés** :
   ```python
   entry = StandardComponents.create_entry_input(parent, "placeholder")
   text = StandardComponents.create_text_input(parent, "placeholder", height=8)
   ```

5. **Padding uniforme** :
   ```python
   ttk.Frame(parent, padding=StandardComponents.PADDING)
   ```

## 🎨 Répartition d'Espace SPLIT

### Pattern Optimal (inspiré de `generation`) :
```python
# Top pane : Contenu principal (2/3 de l'espace)
main_frame = ttk.Frame(parent)
parent.add(main_frame, weight=2)

# Bottom pane : Options/Actions (1/3 de l'espace)  
bottom_frame = ttk.Frame(parent)
parent.add(bottom_frame, weight=1)
```

## 📋 Plan de Migration

### Phase 1 : Panels SCROLLABLE → SPLIT
- `proofreading.py` : Interface riche → SPLIT
- `style_intensity_refactored.py` : Formulaire → SIMPLE

### Phase 2 : Optimisation SPLIT existants
- `settings.py` : Améliorer répartition espace
- `snippets.py` : Optimiser layout listbox/editor
- `metrics.py` : Vérifier cohérence

### Phase 3 : Finalisation SIMPLE
- `translate.py` : Vérifier StandardComponents
- `keywords.py` : Optimiser layout
- Tous les autres SIMPLE

## ✅ Critères de Validation

Un panel est **SOLID** s'il respecte :

1. ✅ Layout approprié au contenu
2. ✅ StandardComponents partout  
3. ✅ Utilise TOUT l'espace vertical
4. ✅ Répartition logique (2:1 pour SPLIT)
5. ✅ Padding/spacing cohérents
6. ✅ Pas de hardcoded fonts/colors
7. ✅ Navigation/focus logique

## 🎯 Objectif Final

**TOUS** les panels auront la même qualité professionnelle que `generation`, avec une structure prévisible et maintenable.