require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });

require(['vs/editor/editor.main'], function () {
  const editor = monaco.editor.create(document.getElementById('editor'), {
    value: "Début du document.\n",
    language: 'latex',
    theme: 'vs-white',
    fontSize: 18,
  });

  // Commande de complétion
  editor.addCommand(
    monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyC,
    () => {
      const code = editor.getValue();

      fetch("http://localhost:8000/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      })
        .then((res) => res.json())
        .then((data) => {
          const completion = data.completion;

          if (completion && !completion.startsWith("❌")) {
            const position = editor.getPosition();

            editor.executeEdits("completion", [
              {
                range: new monaco.Range(
                  position.lineNumber,
                  position.column,
                  position.lineNumber,
                  position.column
                ),
                text: completion,
                forceMoveMarkers: true,
              },
            ]);
          }
        })
        .catch((err) => console.error("Erreur complétion :", err));
    }
  );

  // Bouton de compilation
  document.getElementById("compile-btn").onclick = function () {
    const latex = editor.getValue();
    document.getElementById("latex-content").value = latex;
  };
});
