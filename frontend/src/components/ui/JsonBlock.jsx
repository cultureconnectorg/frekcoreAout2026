export function JsonBlock({ code, filename = null, verified = false }) {
  // Simple syntax highlighting
  const highlightJson = (jsonString) => {
    return jsonString
      .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
      .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>')
      .replace(/: (\d+)/g, ': <span class="json-number">$1</span>')
      .replace(/([{}[\],])/g, '<span class="json-bracket">$1</span>')
      .replace(/\/\/(.+)/g, '<span class="json-comment">//$1</span>');
  };

  return (
    <div className="relative bg-dark border border-terra/20 rounded-sm overflow-hidden">
      {filename && (
        <div className="px-4 py-2 bg-navy border-b border-terra/20 font-mono text-xs text-terra">
          {filename}
        </div>
      )}
      <pre className="p-4 overflow-x-auto text-sm font-mono leading-relaxed">
        <code dangerouslySetInnerHTML={{ __html: highlightJson(code) }} />
      </pre>
      {verified && (
        <div className="absolute bottom-4 right-4 px-3 py-1 bg-fgreen/20 border border-fgreen/30 rounded-sm">
          <span className="font-mono text-xs text-[#5DC882]">✓ VÉRIFIÉ</span>
        </div>
      )}
    </div>
  );
}

export default JsonBlock;
