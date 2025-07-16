SendMode Input
SetKeyDelay, 0, 0

F1::
    SendRaw, \begin{codeboxlang}[title=]{sql}
    Send, {Enter 2}
    Send, {Backspace}
    SendRaw, \end{codeboxlang}
    Send, {Up 2}
    Send, {Right 9}
    return

F2::
    SendRaw, \res{}
    Send, {Left 1}
    return

F3:: 
    SendRaw, \comp{}
    Send, {Left 1}
    return

F4:: 
    SendRaw, \obs{}
    Send, {Left 1}
    return

F5:: 
    SendRaw, \tsec{}
    Send, {Left 1}
    return

F6::
    SendRaw, \begin{itemize}
    Send, {Enter}
    return

F7:: 
    SendRaw, \item 
    Send, {Space}
    return

F8::
    SendRaw, \section{}
    Send, {Left 1}
    return

F9::
    SendRaw, \subsection{}
    Send, {Left 1}
    return

F10::
    SendRaw, \insererfigure{img/}{5cm}{}{fig::}
    Send, {Left 1}
    return

F12:: Reload