export function FrekJsonPreview({ document }) {
  if (!document) return null;

  const jsonString = JSON.stringify(document, null, 2);

  // Simple syntax highlighting
  const highlightJson = (json) => {
    return json
      .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
      .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>')
      .replace(/: (\d+\.?\d*)/g, ': <span class="json-number">$1</span>')
      .replace(/: (null|true|false)/g, ': <span class="json-number">$1</span>')
      .replace(/([{}[\],])/g, '<span class="json-bracket">$1</span>');
  };

  return (
    <div className="bg-dark border border-terra/20 overflow-hidden">
      <div className="px-4 py-2 bg-navy border-b border-terra/20 flex items-center justify-between">
        <span className="font-mono text-xs text-terra">
          {document.mix_id}.frek.json
        </span>
        <span className="font-mono text-[10px] text-dim">
          {(jsonString.length / 1024).toFixed(1)} KB
        </span>
      </div>
      <pre className="p-4 overflow-x-auto text-xs font-mono leading-relaxed max-h-[400px] overflow-y-auto">
        <code dangerouslySetInnerHTML={{ __html: highlightJson(jsonString) }} />
      </pre>
    </div>
  );
}

export default FrekJsonPreview;
