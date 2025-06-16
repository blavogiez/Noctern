\LoadClass[a4paper,12pt]{article} % Classe du document

%--------------------- Packages ------------------------

\RequirePackage[french]{babel} %Langue du document
\RequirePackage[utf8]{inputenc} %Caractères spéciaux
\RequirePackage[section]{placeins}%Pour placement de section
\RequirePackage[T1]{fontenc} %Quelques lettres qui sont pas inclus dans UTF-8
\RequirePackage{mathtools} %Paquet pour des équations et symboles mathématiques
\RequirePackage{siunitx} %Pour écrire avec la notation scientifique (Ex.: \num{2e+9})
\RequirePackage{float} %Pour placement d'images
\RequirePackage{graphicx} %Paquet pour insérer des images
\RequirePackage[justification=centering]{caption} %Pour les légendes centralisées
\RequirePackage{subcaption}
\RequirePackage{wallpaper}
\RequirePackage{nomencl}
\RequirePackage{minted}
\RequirePackage{xcolor}
\RequirePackage{listings}
\RequirePackage[most]{tcolorbox}
\RequirePackage{enumitem}
\RequirePackage{tcolorbox}
\RequirePackage{listings}
\RequirePackage{xcolor}
\RequirePackage{tcolorbox}
\RequirePackage{inconsolata}
\RequirePackage{helvet}

\tcbuselibrary{listings, skins}


%\makenomenclature
\RequirePackage{fancyhdr}
%\pagestyle{fancy}
%\fancyheadoffset{1cm}
%\setlength{\headheight}{2cm}
\RequirePackage{url}
\RequirePackage[hidelinks]{hyperref}%Paquet pour insérer légendes dans des sous-figures comme Figure 1a, 1b
\RequirePackage[left=2.5cm,right=2.5cm,top=2cm,bottom=3.5cm]{geometry} %Configuration de la page

%-------------------- Informations sur le rapport ----------------------

\newcommand{\UE}[1]{\renewcommand{\UE}{#1}}
\newcommand{\sujet}[1]{\renewcommand{\sujet}{#1}}
\newcommand{\titre}[1]{\renewcommand{\titre}{#1}}
\newcommand{\enseignant}[1]{\renewcommand{\enseignant}{#1}}
\newcommand{\eleves}[1]{\renewcommand{\eleves}{#1}}

\newcommand{\fairemarges}{
\makenomenclature
\pagestyle{fancy}
\fancyheadoffset{1cm}
\setlength{\headheight}{2cm}
\lhead{\includegraphics[scale=0.1]{logos/logo_ECL.jpg}} %Affichage de l'image au top de la page
\rhead{\textit{\nouppercase{\leftmark}}}
\rfoot{\thepage}
\cfoot{\textcolor{blue}{\textbf{\titre}}}
\lfoot{\UE}
}
\newcommand{\fairepagedegarde}{
\begin{titlepage}
 % date complète avec jour

\ThisLRCornerWallPaper{0.3}{logos/folded.png} % Réduire l'opacité de l'image de fond
	\centering %Centraliser le contenu
	\includegraphics[width=0.8\textwidth]{logos/logo.png}\par\vspace{1cm} %Insertion du logo
	{\scshape\LARGE \textcolor{black}{Université de Lille} \par} %Nom de l'université en noir
	\vspace{1.5cm}%Espace de 1,5cm
	{\scshape\Large \textcolor{black}{\UE \\ \sujet \\ \vspace{0.3cm}  Rapport}\par} %sous-titre en noir
	\vspace{1cm}%Espace de 1cm
    \rule{\linewidth}{0.2 mm} \\[0.4 cm]
	{\huge\bfseries \textcolor{blue}{\titre} \par} \
    \rule{\linewidth}{0.2 mm} \\[1.5 cm]
	\vspace{1cm}%Espace de 3cm

	\begin{minipage}{0.5\textwidth} %Minipage pour faire deux colonnes
		\begin{flushleft} \large %Envoyer à gauche
		\emph{\textbf{Élèves :}}\\ %Pour le titre au dessus des noms à gauche
        \textcolor{black}{\eleves}\\ %Remplacer pour chacun en noir
		\end{flushleft}
	\end{minipage}
	~
	\begin{minipage}{0.4\textwidth}
		\begin{flushright} \large
		\emph{\textbf{Enseignant :}} \\
		 \textcolor{black}{\enseignant} \\ %Enseignant en noir
		\end{flushright}
	\end{minipage}\\[4cm]

	\vfill
	{\LARGE \today\par}
	\end{titlepage}
}


\newcommand{\tabledematieres}{
\tableofcontents
\newpage
}

\newcommand{\insererfigure}[4]{
\begin{figure}[H]
\centering
\includegraphics[height=#2]{#1}
\caption{#3}
\label{fig: #4}
\end{figure}
}

\newcommand{\stylishcircle}{%
  \tikz[baseline=-.6ex] {
    \shade[ball color=gray!30, draw=gray!70]
      (0,0) circle (0.8ex);
  }%
}

\newcommand{\merci}{
  \vspace*{\fill}
  \begin{center}
    {\bfseries\LARGE Merci d'avoir consulté cette présentation}
  \end{center}
  \vspace*{\fill}
}


\setlist[itemize]{
  label=\stylishcircle,
  labelsep=1.5em,
  left=4em,              % indentation
  itemsep=0.5\baselineskip,   % espace entre les items
  parsep=0pt,            % pas d'espace supplémentaire entre paragraphes internes
  topsep=0.5\baselineskip % espace avant et après la liste
}

\newcounter{tseccounter}[subsection] % remet à zéro à chaque nouvelle subsection
\renewcommand{\thetseccounter}{\arabic{tseccounter}}

\makeatletter
\newcommand{\tsec}[1]{%
  \refstepcounter{tseccounter}%
  \par\vspace{1\baselineskip}%
  \noindent
  {\normalsize\bfseries \thetseccounter. #1\par}%
  \vspace{1\baselineskip}%
}
\makeatother


\makeatletter
\newcommand{\tsecnonum}[1]{%
  \par\vspace{1\baselineskip}%
  \noindent
  {\normalsize\bfseries #1\par}%
  \vspace{1\baselineskip}%
}
\makeatother

% saut de page à chaque section

\let\oldsection\section
\renewcommand\section{%
  \clearpage% ou \newpage
  \oldsection}

% Box de réponse

% Définition de la boîte de réponse
\newtcolorbox{resultbox}{
  colback=gray!10,       % fond clair
  colframe=gray!60,      % bordure grise
  boxrule=0.5pt,         % épaisseur de la bordure
  arc=4pt,               % arrondi des coins
  left=6pt,              % marge intérieure gauche
  right=6pt,             % marge intérieure droite
  top=4pt,               % marge intérieure haute
  bottom=4pt,            % marge intérieure basse
  before skip=10pt,      % espace avant la boîte
  after skip=10pt        % espace après la boîte
}

% Définition de la boîte de comparaison
\newtcolorbox{comparisonbox}{
  colback=blue!10,       % Fond bleu clair
  colframe=blue!60,      % Bordure bleue
  boxrule=0.5pt,         % Épaisseur de la bordure
  arc=8pt,               % Arrondi des coins
  left=6pt,              % Marge intérieure gauche
  right=6pt,             % Marge intérieure droite
  top=4pt,               % Marge intérieure haute
  bottom=4pt,            % Marge intérieure basse
  before skip=10pt,      % Espace avant la boîte
  after skip=10pt,        % Espace après la boîte
  drop shadow            % Ombre subtile
}

% Définition de la boîte d'observation
\newtcolorbox{observationbox}{
  colback=red!10,      % Fond vert clair
  colframe=red!60,     % Bordure verte
  boxrule=0.5pt,         % Épaisseur de la bordure
  arc=8pt,               % Arrondi des coins
  left=6pt,              % Marge intérieure gauche
  right=6pt,             % Marge intérieure droite
  top=4pt,               % Marge intérieure haute
  bottom=4pt,            % Marge intérieure basse
  before skip=10pt,      % Espace avant la boîte
  after skip=10pt,       % Espace après la boîte
  drop shadow            % Ombre subtile
}

% Commande personnalisée pour l'observation
\newcommand{\obs}[1]{%
  \begin{observationbox}
  \textbf{Observation:} #1
  \end{observationbox}
}

% Commande personnalisée pour la comparaison
\newcommand{\comp}[1]{%
  \begin{comparisonbox}
  \textbf{Comparaison:} #1
  \end{comparisonbox}
}

% Commande personnalisée
\newcommand{\res}[1]{%
  \begin{resultbox}
  \textbf{Résultat:} #1
  \end{resultbox}
}

% Codebox tous langages
% Style générique de listing

\lstdefinestyle{mycustomstyle}{
  breaklines=true,
  basicstyle=\ttfamily\small\color{black}, % <- couleur forcée en noir
  keywordstyle=\color{green!60!black}\bfseries,
  commentstyle=\color{gray!60!black}\itshape,
  stringstyle=\color{blue},
  showstringspaces=false,
  numbers=left,
  numberstyle=\tiny\color{gray},
  stepnumber=1,
  numbersep=10pt,
}


\newtcblisting{codeboxlang}[2][]{%
  enhanced,
  arc=12pt,
  colback=green!5!white,
  colframe=green!60!black,
  coltext=black,         % Couleur du code
  coltitle=red,        % <<< Couleur du texte du titre
  boxrule=1pt,
  top=10pt,bottom=10pt,left=12pt,right=12pt,
  attach boxed title to top left={yshift=-10pt,xshift=12pt},
  boxed title style={colback=pink!20!white, boxrule=0pt, arc=6pt},
  title={\faIcon{code} \textcolor{blue}{\textbf{\large \textsc{#2} Code}}}, 
  listing only,
  listing options={%
    style=mycustomstyle,
    language=#2,
    literate={\\}{\textbackslash}1
             {_}{\_}1
             {^}{\^}1
             {/}{\/}1
             {{}{\{}1
             {}}{\{}1
             {|}{\textbar}1
             {~}{\textasciitilde}1
  },
  drop shadow,
  fonttitle=\bfseries,
  #1%
}



% Raccourci d'appel des codebox de langue

% Incomplet (ne compile pas)

% Créer un nouvel environnement 'sql' basé sur 'codeboxlang'
%\newenvironment{sql}{\begin{codeboxlang}[title=SQL Query]{sql}}{\end{codeboxlang}}

% Créer un nouvel environnement 'java' basé sur 'codeboxlang'
%\newenvironment{java}{\begin{codeboxlang}[title=Code Java]{java}}{\end{codeboxlang}}

% Créer un nouvel environnement 'python' basé sur 'codeboxlang'
%\newenvironment{python}{\begin{codeboxlang}[title=Code Python]{python}}{\end{codeboxlang}}



% Utilisation :
% \begin{codeboxlang}{Python}
% print("Hello")
% \end{codeboxlang}

