\LoadClass[a4paper,12pt]{article}

% --------------------- Packages ------------------------
\RequirePackage[french]{babel}
\RequirePackage[utf8]{inputenc}
\RequirePackage[section]{placeins}
\RequirePackage[T1]{fontenc}
\RequirePackage{mathtools}
\RequirePackage{siunitx}
\RequirePackage{float}
\RequirePackage{graphicx}
\RequirePackage[justification=centering]{caption}
\RequirePackage{subcaption}
\RequirePackage{wallpaper}
\RequirePackage{nomencl}
\RequirePackage{minted}
\RequirePackage{xcolor}
\RequirePackage{listings}
\RequirePackage[most]{tcolorbox}
\RequirePackage{ifthen}
\RequirePackage{enumitem}
\RequirePackage{inconsolata}
\RequirePackage{fancyhdr}
\RequirePackage{url}
\RequirePackage[hidelinks]{hyperref}
\RequirePackage[left=2.5cm,right=2.5cm,top=2cm,bottom=3.5cm]{geometry}
\tcbuselibrary{listings, skins}

% --------------------- Infos ------------------------
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
	\lhead{\includegraphics[scale=0.1]{logos/logo_ECL.jpg}}
	\rhead{\textit{\nouppercase{\leftmark}}}
	\rfoot{\thepage}
	\cfoot{\textcolor{blue}{\textbf{\titre}}}
	\lfoot{\UE}
}

\newcommand{\fairepagedegarde}{
	\begin{titlepage}
		\centering
		\includegraphics[width=0.8\textwidth]{logos/logo.png}\par\vspace{1cm}
		{\scshape\LARGE \textcolor{black}{Université de Lille} \par}
		\vspace{1.5cm}
		{\scshape\Large \textcolor{black}{\UE \\ \sujet \\ \vspace{0.3cm}  Rapport}\par}
		\vspace{1cm}
		\rule{\linewidth}{0.2 mm} \\[0.4 cm]
		{\huge\bfseries \textcolor{blue}{\titre} \par}
		\rule{\linewidth}{0.2 mm} \\[1.5 cm]
		
		\begin{minipage}{0.5\textwidth}
			\begin{flushleft} \large
				\emph{\textbf{Élèves :}}\\
				\textcolor{black}{\eleves}\\
			\end{flushleft}
		\end{minipage}
		~
		\begin{minipage}{0.4\textwidth}
			\begin{flushright} \large
				\emph{\textbf{Enseignant :}} \\
				\textcolor{black}{\enseignant} \\
			\end{flushright}
		\end{minipage}\\[4cm]
		
		\vfill
		{\large \today\par}
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
	left=4em,
	itemsep=0.5\baselineskip,
	parsep=0pt,
	topsep=0.5\baselineskip
}

\newcounter{tseccounter}[subsection]
\renewcommand{\thetseccounter}{\arabic{tseccounter}}

\makeatletter
\newcommand{\tsec}[1]{%
	\refstepcounter{tseccounter}%
	\par\vspace{1\baselineskip}%
	\noindent
	{\normalsize\bfseries \thetseccounter. #1\par}%
	\vspace{1\baselineskip}%
}
\newcommand{\tsecnonum}[1]{%
	\par\vspace{1\baselineskip}%
	\noindent
	{\normalsize\bfseries #1\par}%
	\vspace{1\baselineskip}%
}
\makeatother

\let\oldsection\section
\renewcommand\section{%
	\clearpage
	\oldsection}

% -------------------- Boxe de contenu --------------------

\newtcolorbox{resultbox}{
	colback=gray!10,
	colframe=gray!60,
	boxrule=0.5pt,
	arc=4pt,
	left=6pt, right=6pt, top=4pt, bottom=4pt,
	before skip=10pt, after skip=10pt
}

\newtcolorbox{comparisonbox}{
	colback=blue!10,
	colframe=blue!60,
	boxrule=0.5pt,
	arc=8pt,
	left=6pt, right=6pt, top=4pt, bottom=4pt,
	before skip=10pt, after skip=10pt,
	drop shadow
}

\newtcolorbox{observationbox}{
	colback=red!10,
	colframe=red!60,
	boxrule=0.5pt,
	arc=8pt,
	left=6pt, right=6pt, top=4pt, bottom=4pt,
	before skip=10pt, after skip=10pt,
	drop shadow
}

\newcommand{\obs}[1]{%
	\begin{observationbox}
		\textbf{Observation:} #1
	\end{observationbox}
}

\newcommand{\comp}[1]{%
	\begin{comparisonbox}
		\textbf{Comparaison:} #1
	\end{comparisonbox}
}

\newcommand{\res}[1]{%
	\begin{resultbox}
		\textbf{Résultat:} #1
	\end{resultbox}
}

% -------------------- CodeBox par langage --------------------

\lstdefinestyle{sqlstyle}{
	language=SQL,
	basicstyle=\ttfamily\small\color{brown!80!black},
	keywordstyle=\color{red!80!black}\bfseries,
	commentstyle=\color{gray}\itshape,
	stringstyle=\color{orange!90!black},
	numbers=left,
	numberstyle=\tiny\color{gray},
	stepnumber=1,
	numbersep=10pt,
	breaklines=true,
	showstringspaces=false,
}

\lstdefinestyle{pythonstyle}{
	language=Python,
	basicstyle=\ttfamily\small\color{blue!80!black},
	keywordstyle=\color{teal!80!black}\bfseries,
	commentstyle=\color{gray}\itshape,
	stringstyle=\color{orange},
	numbers=left,
	numberstyle=\tiny\color{gray},
	stepnumber=1,
	numbersep=10pt,
	breaklines=true,
	showstringspaces=false,
}

\lstdefinestyle{javastyle}{
	language=Java,
	basicstyle=\ttfamily\small\color{violet!80!black},
	keywordstyle=\color{purple!90!black}\bfseries,
	commentstyle=\color{gray}\itshape,
	stringstyle=\color{orange!80!black},
	numbers=left,
	numberstyle=\tiny\color{gray},
	stepnumber=1,
	numbersep=10pt,
	breaklines=true,
	showstringspaces=false,
}

\newcommand{\codeboxcolback}[1]{%
	\ifthenelse{\equal{#1}{Python}}{blue!5!white}{%
		\ifthenelse{\equal{#1}{Java}}{purple!5!white}{green!5!white}}%
}

\newcommand{\codeboxcolframe}[1]{%
	\ifthenelse{\equal{#1}{Python}}{blue!50!black}{%
		\ifthenelse{\equal{#1}{Java}}{purple!60!black}{green!60!black}}%
}

\newtcblisting{codeboxlang}[2][]{
	enhanced,
	arc=12pt,
	coltext=black,
	coltitle=red,
	boxrule=1pt,
	top=10pt,bottom=10pt,left=12pt,right=12pt,
	attach boxed title to top left={yshift=-10pt,xshift=12pt},
	boxed title style={colback=pink!20!white, boxrule=0pt, arc=6pt},
	title={\textcolor{blue}{\textbf{\large \textsc{#2} Code}}},
	listing only,
	listing options={
		language=#2,
		style=#2 style,
		literate={\\}{\textbackslash}1 {_}{\_}1 {^}{\^}1 {|}{\textbar}1 {~}{\textasciitilde}1,
	},
	drop shadow,
	fonttitle=\bfseries,
	colback=\codeboxcolback{#2},
	colframe=\codeboxcolframe{#2},
	#1
}
