require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });

require(['vs/editor/editor.main'], function () {
  const editor = monaco.editor.create(document.getElementById('editor'), {
    value: "\\documentclass{article}\n\\begin{document}\n",
    language: 'latex',
    theme: 'vs-dark',
    fontSize: 14,
  });

  let timeout = null;

  editor.onDidChangeModelContent(() => {
    clearTimeout(timeout);

    timeout = setTimeout(() => {
      const code = editor.getValue();

      fetch('http://localhost:8000/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      .then(res => res.json())
      .then(data => {
        if (data.completion && !data.completion.startsWith("❌")) {
          const position = editor.getPosition();
          const range = new monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column);

          editor.executeEdits("suggestion", [{
            range,
            text: data.completion,
            forceMoveMarkers: true,
          }]);
        }
      });
    }, 1000);  // délai après arrêt de frappe
  });
});
