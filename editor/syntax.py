import tkinter as tk
import re
import os
from editor.tab import EditorTab
from utils import debug_console

# Configuration des couleurs basée sur la psychologie des couleurs et l'ergonomie visuelle
COLOR_SCHEME = {
    # Couleurs principales - basées sur la théorie des couleurs complémentaires
    'command_primary': '#2E86AB',      # Bleu professionnel pour les commandes importantes
    'command_secondary': '#A23B72',     # Magenta pour les commandes de formatage
    'command_environment': '#F18F01',   # Orange pour les environnements
    'command_math': '#C73E1D',         # Rouge-orange pour les commandes mathématiques
    
    # Couleurs de contenu - tons plus doux pour réduire la fatigue oculaire
    'text_bold': '#2D5016',            # Vert foncé pour le texte gras
    'text_italic': '#6A4C93',          # Violet pour l'italique
    'text_underline': '#9B59B6',       # Violet clair pour le souligné
    'text_emphasis': '#8E44AD',        # Violet profond pour l'emphase
    
    # Couleurs structurelles - hiérarchie visuelle claire
    'brace_level1': '#34495E',         # Gris-bleu pour les accolades principales
    'brace_level2': '#7F8C8D',         # Gris moyen pour le niveau 2
    'brace_level3': '#95A5A6',         # Gris clair pour le niveau 3
    'bracket': '#E67E22',              # Orange pour les crochets
    'parenthesis': '#16A085',          # Turquoise pour les parenthèses
    
    # Couleurs spécialisées
    'comment': '#7D8491',              # Gris neutre pour les commentaires
    'string': '#27AE60',               # Vert pour les chaînes
    'number': '#E74C3C',               # Rouge vif pour les nombres
    'float': '#C0392B',                # Rouge foncé pour les décimales
    'special_char': '#8E44AD',         # Violet pour les caractères spéciaux
    'label_ref': '#3498DB',            # Bleu ciel pour les labels et références
    'citation': '#9B59B6',             # Violet pour les citations
    'url': '#1ABC9C',                  # Turquoise pour les URLs
    'file_path': '#F39C12',            # Jaune-orange pour les chemins de fichier
    
    # Couleurs d'environnements spécifiques
    'env_math': '#8E44AD',             # Violet pour les environnements mathématiques
    'env_table': '#2980B9',            # Bleu pour les tableaux
    'env_figure': '#27AE60',           # Vert pour les figures
    'env_list': '#E67E22',             # Orange pour les listes
    'env_theorem': '#C0392B',          # Rouge pour les théorèmes
    
    # Couleurs d'arrière-plan (optionnelles)
    'bg_math': '#FDF2E9',              # Fond crème très léger pour les maths
    'bg_code': '#F8F9FA',              # Fond gris très léger pour le code
}

# Classification des commandes LaTeX par catégorie
LATEX_COMMANDS = {
    'primary': [
        'documentclass', 'usepackage', 'begin', 'end', 'chapter', 'section', 
        'subsection', 'subsubsection', 'paragraph', 'subparagraph', 'part',
        'maketitle', 'tableofcontents', 'listoffigures', 'listoftables'
    ],
    'formatting': [
        'textbf', 'textit', 'texttt', 'textrm', 'textsf', 'textsl', 'textsc',
        'underline', 'emph', 'textcolor', 'colorbox', 'fcolorbox', 'huge',
        'Large', 'large', 'normalsize', 'small', 'footnotesize', 'scriptsize', 'tiny'
    ],
    'math': [
        'frac', 'sqrt', 'sum', 'int', 'prod', 'lim', 'sin', 'cos', 'tan', 'log',
        'exp', 'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta', 'lambda',
        'mu', 'pi', 'sigma', 'phi', 'psi', 'omega', 'infty', 'partial', 'nabla'
    ],
    'environments': [
        'document', 'figure', 'table', 'equation', 'align', 'gather', 'split',
        'itemize', 'enumerate', 'description', 'center', 'flushleft', 'flushright',
        'quote', 'quotation', 'verse', 'verbatim', 'tabular', 'array', 'matrix'
    ]
}

MATH_ENVIRONMENTS = [
    'equation', 'align', 'gather', 'split', 'multline', 'flalign', 'alignat',
    'matrix', 'pmatrix', 'bmatrix', 'vmatrix', 'Vmatrix', 'cases'
]

def apply_syntax_highlighting(editor):
    """
    Applique une coloration syntaxique avancée optimisée pour LaTeX.
    Utilise des principes de psychologie des couleurs et d'ergonomie visuelle.
    """
    if not editor:
        debug_console.log("Editor not available for syntax highlighting.", level='WARNING')
        return

    current_tab = editor.master
    if not isinstance(current_tab, EditorTab):
        return

    # Configuration des polices
    base_font = current_tab.editor_font
    try:
        font_family = base_font.cget("family")
        font_size = base_font.cget("size")
        bold_font = (font_family, font_size, "bold")
        italic_font = (font_family, font_size, "italic")
        normal_font = (font_family, font_size, "normal")
        small_font = (font_family, max(8, font_size - 2), "normal")
    except tk.TclError:
        bold_font = ("Arial", 12, "bold")
        italic_font = ("Arial", 12, "italic")
        normal_font = ("Arial", 12, "normal")
        small_font = ("Arial", 10, "normal")

    # Configuration des tags avec couleurs psychologiquement optimisées
    _configure_tags(editor, bold_font, italic_font, normal_font, small_font)
    
    # Suppression des anciens tags
    _clear_all_tags(editor)

    try:
        content = editor.get("1.0", tk.END)
    except tk.TclError:
        debug_console.log("Could not get editor content", level='ERROR')
        return

    # Application de la coloration syntaxique
    _apply_advanced_highlighting(editor, content)

def _configure_tags(editor, bold_font, italic_font, normal_font, small_font):
    """Configure tous les tags de coloration avec les couleurs optimisées."""
    
    # Commandes par catégorie
    editor.tag_configure("cmd_primary", foreground=COLOR_SCHEME['command_primary'], font=bold_font)
    editor.tag_configure("cmd_formatting", foreground=COLOR_SCHEME['command_secondary'], font=normal_font)
    editor.tag_configure("cmd_math", foreground=COLOR_SCHEME['command_math'], font=normal_font)
    editor.tag_configure("cmd_environment", foreground=COLOR_SCHEME['command_environment'], font=bold_font)
    editor.tag_configure("cmd_generic", foreground=COLOR_SCHEME['command_primary'], font=normal_font)
    
    # Contenu formaté
    editor.tag_configure("content_bold", foreground=COLOR_SCHEME['text_bold'], font=bold_font)
    editor.tag_configure("content_italic", foreground=COLOR_SCHEME['text_italic'], font=italic_font)
    editor.tag_configure("content_underline", foreground=COLOR_SCHEME['text_underline'], underline=True)
    editor.tag_configure("content_emphasis", foreground=COLOR_SCHEME['text_emphasis'], font=italic_font)
    
    # Délimiteurs hiérarchiques
    editor.tag_configure("brace_l1", foreground=COLOR_SCHEME['brace_level1'], font=bold_font)
    editor.tag_configure("brace_l2", foreground=COLOR_SCHEME['brace_level2'], font=normal_font)
    editor.tag_configure("brace_l3", foreground=COLOR_SCHEME['brace_level3'], font=normal_font)
    editor.tag_configure("bracket", foreground=COLOR_SCHEME['bracket'], font=normal_font)
    editor.tag_configure("parenthesis", foreground=COLOR_SCHEME['parenthesis'], font=normal_font)
    
    # Éléments spécialisés
    editor.tag_configure("comment", foreground=COLOR_SCHEME['comment'], font=italic_font)
    editor.tag_configure("string", foreground=COLOR_SCHEME['string'], font=normal_font)
    editor.tag_configure("number", foreground=COLOR_SCHEME['number'], font=normal_font)
    editor.tag_configure("float_number", foreground=COLOR_SCHEME['float'], font=normal_font)
    editor.tag_configure("special_char", foreground=COLOR_SCHEME['special_char'], font=normal_font)
    editor.tag_configure("label_ref", foreground=COLOR_SCHEME['label_ref'], font=normal_font)
    editor.tag_configure("citation", foreground=COLOR_SCHEME['citation'], font=normal_font)
    editor.tag_configure("url", foreground=COLOR_SCHEME['url'], font=normal_font, underline=True)
    editor.tag_configure("file_path", foreground=COLOR_SCHEME['file_path'], font=small_font)
    
    # Environnements spécialisés
    editor.tag_configure("env_math", foreground=COLOR_SCHEME['env_math'], font=normal_font,
                        background=COLOR_SCHEME['bg_math'])
    editor.tag_configure("env_code", foreground=COLOR_SCHEME['command_primary'], font=("Courier New", 10),
                        background=COLOR_SCHEME['bg_code'])

def _clear_all_tags(editor):
    """Supprime tous les tags de coloration existants."""
    tags_to_remove = [
        "cmd_primary", "cmd_formatting", "cmd_math", "cmd_environment", "cmd_generic",
        "content_bold", "content_italic", "content_underline", "content_emphasis",
        "brace_l1", "brace_l2", "brace_l3", "bracket", "parenthesis",
        "comment", "string", "number", "float_number", "special_char",
        "label_ref", "citation", "url", "file_path", "env_math", "env_code"
    ]
    
    for tag in tags_to_remove:
        try:
            editor.tag_remove(tag, "1.0", tk.END)
        except tk.TclError:
            pass

def _apply_advanced_highlighting(editor, content):
    """Applique la coloration syntaxique avancée avec analyse contextuelle."""
    
    # 1. Commentaires (priorité haute pour éviter la coloration à l'intérieur)
    for match in re.finditer(r"%[^\n]*", content):
        editor.tag_add("comment", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
    
    # 2. Environnements mathématiques avec fond coloré
    _highlight_math_environments(editor, content)
    
    # 3. Commandes LaTeX par catégorie
    _highlight_commands_by_category(editor, content)
    
    # 4. Contenu formaté à l'intérieur des accolades
    _highlight_formatted_content(editor, content)
    
    # 5. Délimiteurs avec hiérarchie visuelle
    _highlight_hierarchical_delimiters(editor, content)
    
    # 6. Nombres et caractères spéciaux
    _highlight_numbers_and_specials(editor, content)
    
    # 7. Références, citations et URLs
    _highlight_references_and_links(editor, content)

def _highlight_math_environments(editor, content):
    """Colore les environnements mathématiques avec arrière-plan."""
    math_env_pattern = r'\\begin\{(' + '|'.join(MATH_ENVIRONMENTS) + r')\}.*?\\end\{\1\}'
    for match in re.finditer(math_env_pattern, content, re.DOTALL):
        editor.tag_add("env_math", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

def _highlight_commands_by_category(editor, content):
    """Colore les commandes LaTeX selon leur catégorie."""
    # Commandes principales
    for cmd in LATEX_COMMANDS['primary']:
        pattern = r'\\' + re.escape(cmd) + r'\b'
        for match in re.finditer(pattern, content):
            editor.tag_add("cmd_primary", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
    
    # Commandes de formatage
    for cmd in LATEX_COMMANDS['formatting']:
        pattern = r'\\' + re.escape(cmd) + r'\b'
        for match in re.finditer(pattern, content):
            editor.tag_add("cmd_formatting", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
    
    # Commandes mathématiques
    for cmd in LATEX_COMMANDS['math']:
        pattern = r'\\' + re.escape(cmd) + r'\b'
        for match in re.finditer(pattern, content):
            editor.tag_add("cmd_math", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
    
    # Environnements
    for env in LATEX_COMMANDS['environments']:
        pattern = r'\\(begin|end)\{' + re.escape(env) + r'\}'
        for match in re.finditer(pattern, content):
            editor.tag_add("cmd_environment", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
    
    # Commandes génériques non classifiées
    generic_pattern = r'\\[a-zA-Z@]+(?!\w)'
    for match in re.finditer(generic_pattern, content):
        # Vérifier si cette commande n'est pas déjà classifiée
        cmd_name = match.group(0)[1:]  # Enlever le backslash
        if not any(cmd_name in category for category in LATEX_COMMANDS.values()):
            editor.tag_add("cmd_generic", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

def _highlight_formatted_content(editor, content):
    """Colore le contenu formaté à l'intérieur des commandes."""
    # Texte gras
    for match in re.finditer(r'\\textbf\{([^}]+)\}', content):
        editor.tag_add("content_bold", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
    
    # Texte italique
    for match in re.finditer(r'\\textit\{([^}]+)\}', content):
        editor.tag_add("content_italic", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
    
    # Texte souligné
    for match in re.finditer(r'\\underline\{([^}]+)\}', content):
        editor.tag_add("content_underline", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
    
    # Emphase
    for match in re.finditer(r'\\emph\{([^}]+)\}', content):
        editor.tag_add("content_emphasis", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")

def _highlight_hierarchical_delimiters(editor, content):
    """Colore les délimiteurs avec hiérarchie visuelle basée sur l'imbrication."""
    brace_stack = []
    bracket_stack = []
    paren_stack = []
    
    for i, char in enumerate(content):
        pos = f"1.0 + {i} chars"
        
        if char == '{':
            level = len(brace_stack) % 3 + 1
            tag = f"brace_l{level}"
            editor.tag_add(tag, pos, f"1.0 + {i + 1} chars")
            brace_stack.append(i)
        elif char == '}' and brace_stack:
            open_pos = brace_stack.pop()
            level = len(brace_stack) % 3 + 1
            tag = f"brace_l{level}"
            editor.tag_add(tag, pos, f"1.0 + {i + 1} chars")
        elif char == '[':
            editor.tag_add("bracket", pos, f"1.0 + {i + 1} chars")
            bracket_stack.append(i)
        elif char == ']' and bracket_stack:
            bracket_stack.pop()
            editor.tag_add("bracket", pos, f"1.0 + {i + 1} chars")
        elif char == '(':
            editor.tag_add("parenthesis", pos, f"1.0 + {i + 1} chars")
            paren_stack.append(i)
        elif char == ')' and paren_stack:
            paren_stack.pop()
            editor.tag_add("parenthesis", pos, f"1.0 + {i + 1} chars")

def _highlight_numbers_and_specials(editor, content):
    """Colore les nombres et caractères spéciaux."""
    # Nombres décimaux
    for match in re.finditer(r'\b\d+\.\d+\b', content):
        editor.tag_add("float_number", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
    
    # Nombres entiers (après les décimaux pour éviter les conflits)
    for match in re.finditer(r'\b\d+\b', content):
        # Vérifier que ce n'est pas déjà coloré comme décimal
        start_pos = match.start()
        if start_pos > 0 and content[start_pos - 1] == '.':
            continue
        if match.end() < len(content) and content[match.end()] == '.':
            continue
        editor.tag_add("number", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
    
    # Caractères spéciaux LaTeX
    special_chars = [r'\\', r'\&', r'\$', r'\#', r'\%', r'\_', r'\{', r'\}', r'\~', r'\^']
    for char_pattern in special_chars:
        for match in re.finditer(char_pattern, content):
            editor.tag_add("special_char", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

def _highlight_references_and_links(editor, content):
    """Colore les références, citations et liens."""
    # Labels et références
    ref_patterns = [r'\\label\{([^}]+)\}', r'\\ref\{([^}]+)\}', r'\\eqref\{([^}]+)\}']
    for pattern in ref_patterns:
        for match in re.finditer(pattern, content):
            editor.tag_add("label_ref", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
    
    # Citations
    cite_patterns = [r'\\cite\{([^}]+)\}', r'\\citep\{([^}]+)\}', r'\\citet\{([^}]+)\}']
    for pattern in cite_patterns:
        for match in re.finditer(pattern, content):
            editor.tag_add("citation", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
    
    # URLs
    for match in re.finditer(r'\\url\{([^}]+)\}', content):
        editor.tag_add("url", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
    
    # Chemins de fichiers
    file_patterns = [r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', r'\\input\{([^}]+)\}', r'\\include\{([^}]+)\}']
    for pattern in file_patterns:
        for match in re.finditer(pattern, content):
            editor.tag_add("file_path", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")

def _resolve_image_path(tex_file_path, image_path_in_tex):
    """Résout le chemin d'une image relativement au fichier TeX."""
    if not tex_file_path:
        base_directory = os.getcwd()
    else:
        base_directory = os.path.dirname(tex_file_path)
    
    clean_image_path = image_path_in_tex.strip().replace('\n', '').replace('\r', '')
    normalized_path = os.path.normpath(clean_image_path.replace("/", os.sep))
    return os.path.join(base_directory, normalized_path)

def clear_syntax_highlighting(editor):
    """Supprime toute la coloration syntaxique."""
    if not editor:
        return
    
    _clear_all_tags(editor)

def refresh_syntax_highlighting(editor):
    """Rafraîchit la coloration syntaxique."""
    clear_syntax_highlighting(editor)
    apply_syntax_highlighting(editor)

def get_color_scheme():
    """Retourne le schéma de couleurs actuel pour une éventuelle personnalisation."""
    return COLOR_SCHEME.copy()

def update_color_scheme(new_colors):
    """Met à jour le schéma de couleurs."""
    COLOR_SCHEME.update(new_colors)