interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const renderMarkdown = (text: string) => {
    let html = text;

    html = html.replace(/### (.*?)$/gm, '<h3 class="text-xl font-bold text-white mt-6 mb-3">$1</h3>');
    html = html.replace(/## (.*?)$/gm, '<h2 class="text-2xl font-bold text-white mt-8 mb-4">$1</h2>');
    html = html.replace(/# (.*?)$/gm, '<h1 class="text-3xl font-bold text-white mt-10 mb-5">$1</h1>');

    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');

    html = html.replace(/`([^`]+)`/g, '<code class="px-2 py-0.5 bg-slate-800 text-purple-300 rounded text-sm font-mono">$1</code>');

    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) => {
      return `<pre class="bg-slate-800 border border-slate-700 rounded-lg p-4 overflow-x-auto my-4"><code class="text-sm font-mono text-slate-300">${escapeHtml(code.trim())}</code></pre>`;
    });

    html = html.replace(/^\- (.*?)$/gm, '<li class="ml-4 mb-2">$1</li>');
    html = html.replace(/(<li.*<\/li>\n?)+/g, '<ul class="list-disc list-inside space-y-2 my-4 text-slate-300">$&</ul>');

    html = html.replace(/^\d+\. (.*?)$/gm, '<li class="ml-4 mb-2">$1</li>');
    html = html.replace(/(<li.*<\/li>\n?)+/g, (match) => {
      if (!match.includes('list-disc')) {
        return `<ol class="list-decimal list-inside space-y-2 my-4 text-slate-300">${match}</ol>`;
      }
      return match;
    });

    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-purple-400 hover:text-purple-300 underline" target="_blank" rel="noopener noreferrer">$1</a>');

    html = html.replace(/^\> (.*?)$/gm, '<blockquote class="border-l-4 border-purple-500 pl-4 italic text-slate-400 my-4">$1</blockquote>');

    html = html.replace(/\n\n/g, '</p><p class="text-slate-300 leading-relaxed mb-4">');
    html = `<p class="text-slate-300 leading-relaxed mb-4">${html}</p>`;

    return html;
  };

  const escapeHtml = (text: string) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  };

  return (
    <div
      className="markdown-content"
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
    />
  );
}
