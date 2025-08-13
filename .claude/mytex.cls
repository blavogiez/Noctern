\LoadClass[a4paper,12pt]{article} % Classe du document

%--------------------- Packages ------------------------

\RequirePackage[french]{babel} %Langue du document
\RequirePackage[utf8]{inputenc} %Caractères spéciaux
\RequirePackage[section]{placeins}%Pour placement de section
\RequirePackage[T1]{fontenc} %Quelques lettres qui sont pas inclus dans UTF-8
\RequirePackage{ifthen} % Package pour les conditions (pour sélection de polices)
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
\RequirePackage{hyperref}

% Commandes pour sélectionner les polices depuis le fichier .tex
\newcommand{\policeprincipale}[1]{%
	\ifthenelse{\equal{#1}{times}}{%
		\RequirePackage{times}%
	}{%
		\ifthenelse{\equal{#1}{palatino}}{%
			\RequirePackage{palatino}%
		}{%
			\ifthenelse{\equal{#1}{mathptmx}}{%
				\RequirePackage{mathptmx}%
			}{%
				\ifthenelse{\equal{#1}{mathpazo}}{%
					\RequirePackage{mathpazo}%
				}{%
					\ifthenelse{\equal{#1}{kpfonts}}{%
						\RequirePackage{kpfonts}%
					}{%
						\ifthenelse{\equal{#1}{charter}}{%
							\RequirePackage{charter}%
						}{%
							\ifthenelse{\equal{#1}{utopia}}{%
								\RequirePackage{utopia}%
							}{%
								\ifthenelse{\equal{#1}{fourier}}{%
									\RequirePackage{fourier}%
								}{%
									\ifthenelse{\equal{#1}{newcent}}{%
										\RequirePackage{newcent}%
									}{%
										\ifthenelse{\equal{#1}{bookman}}{%
											\RequirePackage{bookman}%
										}{%
											\ifthenelse{\equal{#1}{lmodern}}{%
												\RequirePackage{lmodern}%
											}{%
												% Police par défaut si non reconnue
												\RequirePackage{palatino}%
												\PackageWarning{votreclasse}{Police principale '#1' non reconnue, utilisation de palatino par défaut}%
	}}}}}}}}}}}%
}

\newcommand{\policesecondaire}[1]{%
	\ifthenelse{\equal{#1}{times}}{%
		\RequirePackage{times}%
	}{%
		\ifthenelse{\equal{#1}{palatino}}{%
			\RequirePackage{palatino}%
		}{%
			\ifthenelse{\equal{#1}{mathptmx}}{%
				\RequirePackage{mathptmx}%
			}{%
				\ifthenelse{\equal{#1}{mathpazo}}{%
					\RequirePackage{mathpazo}%
				}{%
					\ifthenelse{\equal{#1}{kpfonts}}{%
						\RequirePackage{kpfonts}%
					}{%
						\ifthenelse{\equal{#1}{charter}}{%
							\RequirePackage{charter}%
						}{%
							\ifthenelse{\equal{#1}{utopia}}{%
								\RequirePackage{utopia}%
							}{%
								\ifthenelse{\equal{#1}{fourier}}{%
									\RequirePackage{fourier}%
								}{%
									\ifthenelse{\equal{#1}{newcent}}{%
										\RequirePackage{newcent}%
									}{%
										\ifthenelse{\equal{#1}{bookman}}{%
											\RequirePackage{bookman}%
										}{%
											\ifthenelse{\equal{#1}{lmodern}}{%
												\RequirePackage{lmodern}%
											}{%
												% Pas de police secondaire si non reconnue
												\PackageWarning{votreclasse}{Police secondaire '#1' non reconnue, ignorée}%
	}}}}}}}}}}}%
}

% Packages pour un style professionnel
\RequirePackage{microtype} % Amélioration fine de la typographie
\RequirePackage{setspace} % Contrôle précis de l'espacement
\RequirePackage{titlesec} % Personnalisation professionnelle des titres
\RequirePackage{tikz} % Éléments graphiques minimalistes
\RequirePackage{pgfplots} % Graphiques scientifiques
\RequirePackage{booktabs} % Tableaux de qualité professionnelle
\RequirePackage{array} % Tableaux améliorés
\RequirePackage{multirow} % Tableaux complexes
\RequirePackage{longtable} % Tableaux sur plusieurs pages
\RequirePackage{colortbl} % Couleurs subtiles dans les tableaux
\RequirePackage{ragged2e} % Justification optimisée
\RequirePackage{csquotes} % Guillemets typographiques
\RequirePackage{parskip} % Espacement des paragraphes
\RequirePackage{amsmath,amssymb} % Mathématiques avancées
\RequirePackage{theorem} % Théorèmes et définitions

\tcbuselibrary{listings, skins, breakable}

% Configuration de siunitx pour le français
\sisetup{
	locale = FR,
	group-separator = {\,},
	output-decimal-marker = {,}
}

% Configuration de microtype pour une typographie parfaite
\microtypesetup{
	protrusion = true,
	expansion = true,
	tracking = true,
	kerning = true,
	spacing = true
}

% Palette de couleurs professionnelles plus sérieuses
\definecolor{primary}{HTML}{1A237E}        % Bleu indigo profond
\definecolor{secondary}{HTML}{263238}      % Gris bleu foncé
\definecolor{accent}{HTML}{1565C0}         % Bleu professionnel
\definecolor{success}{HTML}{2E7D32}        % Vert foncé professionnel
\definecolor{warning}{HTML}{F57C00}        % Orange foncé professionnel
\definecolor{error}{HTML}{C62828}          % Rouge foncé professionnel
\definecolor{lightgray}{HTML}{F5F5F5}      % Gris très clair
\definecolor{mediumgray}{HTML}{9E9E9E}     % Gris moyen
\definecolor{darkgray}{HTML}{424242}       % Gris foncé
\definecolor{textcolor}{HTML}{212121}      % Couleur de texte principale
\definecolor{codebg}{HTML}{FAFAFA}         % Fond de code neutre
\definecolor{codeframe}{HTML}{BDBDBD}      % Bordure de code

% Couleurs spécifiques pour les boîtes d'information (tons sérieux)
\definecolor{resultcolor}{HTML}{1B5E20}    % Vert très foncé pour résultats
\definecolor{comparisoncolor}{HTML}{0D47A1} % Bleu très foncé pour comparaisons
\definecolor{observationcolor}{HTML}{E65100} % Orange très foncé pour observations
\definecolor{attentioncolor}{HTML}{B71C1C}  % Rouge très foncé pour attention

% Couleurs spécifiques par langage (tons professionnels)
\definecolor{pythonbg}{HTML}{F8F9FA}
\definecolor{pythonframe}{HTML}{3776AB}
\definecolor{javabg}{HTML}{F8F9FA}
\definecolor{javaframe}{HTML}{ED8B00}
\definecolor{sqlbg}{HTML}{F8F9FA}
\definecolor{sqlframe}{HTML}{336791}
\definecolor{cppbg}{HTML}{F8F9FA}
\definecolor{cppframe}{HTML}{00599C}
\definecolor{jsbg}{HTML}{F8F9FA}
\definecolor{jsframe}{HTML}{F0DB4F}
\definecolor{htmlbg}{HTML}{F8F9FA}
\definecolor{htmlframe}{HTML}{E34C26}
\definecolor{cssbg}{HTML}{F8F9FA}
\definecolor{cssframe}{HTML}{1572B6}
\definecolor{bashbg}{HTML}{F8F9FA}
\definecolor{bashframe}{HTML}{4EAA25}
\definecolor{rbg}{HTML}{F8F9FA}
\definecolor{rframe}{HTML}{198CE7}
\definecolor{matlabbg}{HTML}{F8F9FA}
\definecolor{matlabframe}{HTML}{0076A8}

% Configuration des liens (style professionnel)
\hypersetup{
	colorlinks=true,
	linkcolor=primary,
	urlcolor=accent,
	citecolor=secondary,
	filecolor=accent,
	pdfborder={0 0 0},
	pdftitle={},
	pdfauthor={},
	pdfsubject={},
	pdfkeywords={}
}

% Configuration des titres (style professionnel épuré)
\titleformat{\section}
{\Large\bfseries\color{primary}}
{\thesection}
{1em}
{}
[\vspace{-0.3em}\rule{\textwidth}{0.8pt}]

\titleformat{\subsection}
{\large\bfseries\color{secondary}}
{\thesubsection}
{1em}
{}

\titleformat{\subsubsection}
{\normalsize\bfseries\color{darkgray}}
{\thesubsubsection}
{1em}
{}

% Configuration des captions (style académique)
\captionsetup{
	font={small,rm},
	labelfont={bf,color=primary},
	textfont={color=textcolor},
	format=hang,
	justification=justified,
	singlelinecheck=false,
	margin=1cm
}

%\makenomenclature
\RequirePackage{fancyhdr}
\RequirePackage{url}
\RequirePackage[left=2.5cm,right=2.5cm,top=2.5cm,bottom=3.5cm]{geometry}

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
	\setlength{\headheight}{2.5cm}
	\fancyhf{}
	\lhead{\includegraphics[scale=0.1]{logos/logo_ECL.jpg}}
	\rhead{\small\textbf{\color{primary}\nouppercase{\leftmark}}}
	\rfoot{\small\color{darkgray}\textbf{\thepage}}
	\cfoot{\small\color{primary}\textbf{\titre}}
	\lfoot{\small\color{darkgray}\textbf{\UE}}
	\renewcommand{\headrulewidth}{0.8pt}
	\renewcommand{\footrulewidth}{0.8pt}
	\renewcommand{\headrule}{\hbox to\headwidth{\color{primary}\leaders\hrule height \headrulewidth\hfill}}
	\renewcommand{\footrule}{\hbox to\headwidth{\color{primary}\leaders\hrule height \footrulewidth\hfill}}
}

\newcommand{\fairepagedegarde}{
	\begin{titlepage}
		\centering
		\vspace*{1cm}  % Commence plus haut
		\includegraphics[width=0.6\textwidth]{logos/logo.png}\par
		\vspace{1.5cm}
		{\Large\textbf{\textcolor{primary}{Université de Lille}} \par}
		\vspace{1.2cm}
		{\large\textcolor{secondary}{\UE} \par}
		{\large\textcolor{secondary}{\sujet} \par}
		\vspace{0.4cm}
		{\large\textcolor{secondary}{Rapport} \par}
		\vspace{1.5cm}
		
		\begin{tcolorbox}[
			colback=white,
			colframe=primary,
			boxrule=1.5pt,
			arc=0pt,
			left=2cm,
			right=2cm,
			top=1cm,
			bottom=1cm,
			width=0.8\textwidth,
			halign=center,  % Centre le titre horizontalement
			valign=center   % Centre le titre verticalement
			]
			{\huge\bfseries\textcolor{primary}{\titre}}
		\end{tcolorbox}
		
		\vspace{2cm}
		
		\begin{minipage}{0.45\textwidth}
			\begin{flushleft}
				\textbf{Étudiants :}\\
				\textcolor{textcolor}{\eleves}
			\end{flushleft}
		\end{minipage}
		\hfill
		\begin{minipage}{0.45\textwidth}
			\begin{flushright}
				\textbf{Enseignant :}\\
				\textcolor{textcolor}{\enseignant}
			\end{flushright}
		\end{minipage}
		
		\vfill
		{\large\textcolor{darkgray}{\today}}
	\end{titlepage}
}

\newcommand{\tabledematieres}{
	\tableofcontents
	\newpage
}

\newcommand{\insererfigure}[4]{
	\begin{figure}[H]
		\centering
		\begin{tcolorbox}[
			colback=white,
			colframe=mediumgray,
			boxrule=1pt,
			arc=0pt,
			left=15pt,
			right=15pt,
			top=15pt,
			bottom=10pt,
			width=\textwidth
			]
			\includegraphics[width=\linewidth,height=#2,keepaspectratio]{#1}
		\end{tcolorbox}
		\caption{#3}
		\label{fig: #4}
	\end{figure}
}

\newcommand{\merci}{
	\vspace*{\fill}
	\begin{center}
		{\Huge\bfseries\color{primary}Merci d'avoir consulté cette présentation}
	\end{center}
	\vspace*{\fill}
}

% Configuration des listes (style professionnel)
\setlist[itemize]{
	label=\textbullet,
	labelsep=0.5em,
	left=1.5em,
	itemsep=0.3\baselineskip,
	parsep=0pt,
	topsep=0.5\baselineskip
}

\setlist[enumerate]{
	label=\textbf{\arabic*.},
	labelsep=0.5em,
	left=2em,
	itemsep=0.3\baselineskip,
	parsep=0pt,
	topsep=0.5\baselineskip
}

% Compteur pour les sous-sections techniques
\newcounter{tseccounter}[subsection]
\renewcommand{\thetseccounter}{\arabic{tseccounter}}

% Sous-section technique avec numérotation
\makeatletter
\newcommand{\tsec}[1]{%
	\refstepcounter{tseccounter}%
	\par\vspace{1\baselineskip}%
	\noindent
	\begin{tcolorbox}[
		colback=lightgray,
		colframe=secondary,
		boxrule=0pt,
		arc=0pt,
		left=20pt,
		right=20pt,
		top=12pt,
		bottom=12pt,
		leftrule=3pt
		]
		{\normalsize\bfseries\color{primary}\thetseccounter. #1}
	\end{tcolorbox}
	\vspace{0.5\baselineskip}%
}
\makeatother

% Sous-section technique sans numérotation
\makeatletter
\newcommand{\tsecnonum}[1]{%
	\par\vspace{1\baselineskip}%
	\noindent
	\begin{tcolorbox}[
		colback=lightgray,
		colframe=darkgray,
		boxrule=0pt,
		arc=0pt,
		left=20pt,
		right=20pt,
		top=12pt,
		bottom=12pt,
		leftrule=3pt
		]
		{\normalsize\bfseries\color{primary}#1}
	\end{tcolorbox}
	\vspace{0.5\baselineskip}%
}
\makeatother

% Nouvelle page à chaque section
\let\oldsection\section
\renewcommand\section{%
	\clearpage
	\oldsection}

% Boîtes d'information professionnelles avec couleurs sérieuses

% Boîte de résultat (vert très foncé)
\newtcolorbox{resultbox}{
	enhanced,
	colback=resultcolor!10,
	colframe=resultcolor,
	boxrule=1.2pt,
	arc=0pt,
	left=20pt,
	right=20pt,
	top=15pt,
	bottom=15pt,
	before skip=15pt,
	after skip=15pt,
	leftrule=4pt,
	attach boxed title to top left={yshift=-12pt,xshift=20pt},
	boxed title style={colback=resultcolor, arc=0pt, boxrule=0pt},
	title={\color{white}\textbf{Résultat}},
	fonttitle=\bfseries\small
}

% Boîte de comparaison (bleu très foncé)
\newtcolorbox{comparisonbox}{
	enhanced,
	colback=comparisoncolor!10,
	colframe=comparisoncolor,
	boxrule=1.2pt,
	arc=0pt,
	left=20pt,
	right=20pt,
	top=15pt,
	bottom=15pt,
	before skip=15pt,
	after skip=15pt,
	leftrule=4pt,
	attach boxed title to top left={yshift=-12pt,xshift=20pt},
	boxed title style={colback=comparisoncolor, arc=0pt, boxrule=0pt},
	title={\color{white}\textbf{Comparaison}},
	fonttitle=\bfseries\small
}

% Boîte d'observation (orange très foncé)
\newtcolorbox{observationbox}{
	enhanced,
	colback=observationcolor!10,
	colframe=observationcolor,
	boxrule=1.2pt,
	arc=0pt,
	left=20pt,
	right=20pt,
	top=15pt,
	bottom=15pt,
	before skip=15pt,
	after skip=15pt,
	leftrule=4pt,
	attach boxed title to top left={yshift=-12pt,xshift=20pt},
	boxed title style={colback=observationcolor, arc=0pt, boxrule=0pt},
	title={\color{white}\textbf{Observation}},
	fonttitle=\bfseries\small
}

% Boîte d'information (gris bleu foncé)
\newtcolorbox{infobox}{
	enhanced,
	colback=secondary!10,
	colframe=secondary,
	boxrule=1.2pt,
	arc=0pt,
	left=20pt,
	right=20pt,
	top=15pt,
	bottom=15pt,
	before skip=15pt,
	after skip=15pt,
	leftrule=4pt,
	attach boxed title to top left={yshift=-12pt,xshift=20pt},
	boxed title style={colback=secondary, arc=0pt, boxrule=0pt},
	title={\color{white}\textbf{Information}},
	fonttitle=\bfseries\small
}

% Boîte d'attention (rouge très foncé)
\newtcolorbox{warningbox}{
	enhanced,
	colback=attentioncolor!10,
	colframe=attentioncolor,
	boxrule=1.2pt,
	arc=0pt,
	left=20pt,
	right=20pt,
	top=15pt,
	bottom=15pt,
	before skip=15pt,
	after skip=15pt,
	leftrule=4pt,
	attach boxed title to top left={yshift=-12pt,xshift=20pt},
	boxed title style={colback=attentioncolor, arc=0pt, boxrule=0pt},
	title={\color{white}\textbf{Attention}},
	fonttitle=\bfseries\small
}

% Commandes pour les boîtes
\newcommand{\obs}[1]{%
	\begin{observationbox}
		#1
	\end{observationbox}
}

\newcommand{\comp}[1]{%
	\begin{comparisonbox}
		#1
	\end{comparisonbox}
}

\newcommand{\res}[1]{%
	\begin{resultbox}
		#1
	\end{resultbox}
}

\newcommand{\info}[1]{%
	\begin{infobox}
		#1
	\end{infobox}
}

\newcommand{\warning}[1]{%
	\begin{warningbox}
		#1
	\end{warningbox}
}

% Styles de code professionnels
\lstdefinestyle{basestyle}{
	basicstyle=\ttfamily\small,
	numbers=left,
	numberstyle=\tiny\color{darkgray},
	stepnumber=1,
	numbersep=15pt,
	breaklines=true,
	showstringspaces=false,
	tabsize=4,
	captionpos=b,
	frame=none,
	xleftmargin=25pt,
	xrightmargin=10pt,
	framexleftmargin=20pt,
	framexrightmargin=5pt,
	framexbottommargin=8pt,
	framextopmargin=8pt
}

% Styles spécifiques par langage
\lstdefinestyle{pythonstyle}{
	style=basestyle,
	language=Python,
	backgroundcolor=\color{pythonbg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{pythonframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

\lstdefinestyle{javastyle}{
	style=basestyle,
	language=Java,
	backgroundcolor=\color{javabg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{javaframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

\lstdefinestyle{sqlstyle}{
	style=basestyle,
	language=SQL,
	backgroundcolor=\color{sqlbg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{sqlframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

\lstdefinestyle{cppstyle}{
	style=basestyle,
	language=C++,
	backgroundcolor=\color{cppbg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{cppframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

\lstdefinestyle{c++style}{
	style=cppstyle
}

\lstdefinestyle{javascriptstyle}{
	style=basestyle,
	language=JavaScript,
	backgroundcolor=\color{jsbg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{jsframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

\lstdefinestyle{htmlstyle}{
	style=basestyle,
	language=HTML,
	backgroundcolor=\color{htmlbg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{htmlframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

\lstdefinestyle{cssstyle}{
	style=basestyle,
	language=CSS,
	backgroundcolor=\color{cssbg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{cssframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

\lstdefinestyle{bashstyle}{
	style=basestyle,
	language=bash,
	backgroundcolor=\color{bashbg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{bashframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

\lstdefinestyle{rstyle}{
	style=basestyle,
	language=R,
	backgroundcolor=\color{rbg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{rframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

\lstdefinestyle{matlabstyle}{
	style=basestyle,
	language=Matlab,
	backgroundcolor=\color{matlabbg},
	basicstyle=\ttfamily\small\color{textcolor},
	keywordstyle=\color{matlabframe}\bfseries,
	commentstyle=\color{darkgray}\itshape,
	stringstyle=\color{success},
	identifierstyle=\color{textcolor},
	numberstyle=\tiny\color{darkgray}
}

% Environnement de code avec style professionnel et couleur unique
\newtcblisting{codeboxlang}[2][]{
	enhanced,
	arc=0pt,
	boxrule=1pt,
	top=20pt,
	bottom=20pt,
	left=0pt,
	right=0pt,
	attach boxed title to top left={yshift=-15pt,xshift=20pt},
	boxed title style={
		boxrule=0pt,
		arc=0pt,
		left=15pt,
		right=15pt,
		top=8pt,
		bottom=8pt,
		colback=primary  % Couleur unique pour tous les langages
	},
	listing only,
	listing options={
		language=#2,
		style=#2style,
		literate={\\}{\textbackslash}1 {_}{\_}1 {^}{\^{}}1 {|}{\textbar}1 {~}{\textasciitilde}1
		{á}{{\'a}}1 {à}{{\`a}}1 {â}{{\^a}}1 {ä}{{\"a}}1 {ã}{{\~a}}1
		{é}{{\'e}}1 {è}{{\`e}}1 {ê}{{\^e}}1 {ë}{{\"e}}1
		{í}{{\'i}}1 {ì}{{\`i}}1 {î}{{\^i}}1 {ï}{{\"i}}1
		{ó}{{\'o}}1 {ò}{{\`o}}1 {ô}{{\^o}}1 {ö}{{\"o}}1 {õ}{{\~o}}1
		{ú}{{\'u}}1 {ù}{{\`u}}1 {û}{{\^u}}1 {ü}{{\"u}}1
		{ç}{{\c c}}1 {ñ}{{\~n}}1
		{À}{{\`A}}1 {Á}{{\'A}}1 {Â}{{\^A}}1 {Ã}{{\~A}}1 {Ä}{{\"A}}1
		{È}{{\`E}}1 {É}{{\'E}}1 {Ê}{{\^E}}1 {Ë}{{\"E}}1
		{Ì}{{\`I}}1 {Í}{{\'I}}1 {Î}{{\^I}}1 {Ï}{{\"I}}1
		{Ò}{{\`O}}1 {Ó}{{\'O}}1 {Ô}{{\^O}}1 {Õ}{{\~O}}1 {Ö}{{\"O}}1
		{Ù}{{\`U}}1 {Ú}{{\'U}}1 {Û}{{\^U}}1 {Ü}{{\"U}}1
		{Ç}{{\c C}}1 {Ñ}{{\~N}}1,
	},
	fonttitle=\bfseries\small,
	breakable,
	colback=codebg,
	colframe=primary,        % Couleur unique pour tous les cadres
	coltext=textcolor,
	coltitle=white,
	title={\textbf{\MakeUppercase{#2}}},
	#1
}

% Configuration de l'espacement pour un aspect professionnel
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.4\baselineskip}
\onehalfspacing

% Amélioration de la mise en page
\raggedbottom
\clubpenalty=10000
\widowpenalty=10000

% Configuration des équations
\numberwithin{equation}{section}

% Configuration des figures et tableaux
\numberwithin{figure}{section}
\numberwithin{table}{section}

% Configuration des tableaux professionnels
\renewcommand{\arraystretch}{1.2}

% Environnement pour les définitions
\newtheorem{definition}{Définition}[section]
\newtheorem{theorem}{Théorème}[section]
\newtheorem{remarque}{Remarque}[section]
\newtheorem{proposition}{Proposition}[section]
\newtheorem{lemme}{Lemme}[section]

% Configuration des théorèmes avec style professionnel
\theoremstyle{definition}
\newtheorem{exemple}{Exemple}