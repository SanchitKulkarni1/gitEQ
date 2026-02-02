import { useMemo } from 'react';

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const escapeHtml = (text: string) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  };

  const cleanContent = (text: string): string => {
    // Remove common LLM preambles/prefixes
    const preamblePatterns = [
      /^Okay,?\s*(here's|here is)\s*/i,
      /^Sure,?\s*(here's|here is)\s*/i,
      /^Certainly,?\s*(here's|here is)\s*/i,
      /^Here's\s*/i,
      /^Here is\s*/i,
      /^Below is\s*/i,
    ];

    let cleaned = text.trim();
    for (const pattern of preamblePatterns) {
      cleaned = cleaned.replace(pattern, '');
    }

    // Remove trailing notes like "Let me know if..."
    cleaned = cleaned.replace(/\n+(?:Let me know|Feel free|If you have|Please let me know|Hope this helps).*$/is, '');

    return cleaned.trim();
  };

  const renderMarkdown = useMemo(() => {
    let html = cleanContent(content);

    // === STEP 1: Handle code blocks FIRST (before other transformations) ===
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) => {
      const langLabel = lang ? `<span class="absolute top-2 right-3 text-xs text-slate-500 uppercase">${lang}</span>` : '';
      return `<div class="relative my-6"><pre class="bg-slate-900 border border-slate-700 rounded-xl p-4 pt-8 overflow-x-auto">${langLabel}<code class="text-sm font-mono text-emerald-400 whitespace-pre">${escapeHtml(code.trim())}</code></pre></div>`;
    });

    // === STEP 2: Detect and wrap file tree structures ===
    // Match patterns like: ├── file.py or |-- file.py or └── file.py
    const hasTreeStructure = /[├└│|][\-─]+/.test(html);
    if (hasTreeStructure) {
      // Wrap consecutive tree lines in a code block
      html = html.replace(/((?:^.*[├└│|][\-─].*$\n?)+)/gm, (match) => {
        return `<pre class="bg-slate-900/50 border border-slate-700 rounded-lg p-4 my-4 overflow-x-auto font-mono text-sm text-slate-300 whitespace-pre">${match}</pre>`;
      });
    }

    // === STEP 3: Inline code ===
    html = html.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 bg-slate-800/80 text-purple-300 rounded text-sm font-mono border border-slate-700">$1</code>');

    // === STEP 4: Horizontal rules ===
    html = html.replace(/^[-*_]{3,}$/gm, '<hr class="my-8 border-t border-slate-700/50" />');

    // === STEP 5: Headers ===
    html = html.replace(/^#### (.*?)$/gm, '<h4 class="text-lg font-semibold text-slate-200 mt-8 mb-4">$1</h4>');
    html = html.replace(/^### (.*?)$/gm, '<h3 class="text-xl font-bold text-white mt-10 mb-5 border-b border-slate-700/50 pb-2">$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2 class="text-2xl font-bold text-white mt-12 mb-6">$1</h2>');
    html = html.replace(/^# (.*?)$/gm, '');

    // === STEP 6: Bold and italic ===
    html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong class="font-bold text-white"><em>$1</em></strong>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>');
    html = html.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em class="italic text-slate-300">$1</em>');

    // === STEP 7: Handle dash lists ===
    html = html.replace(/^- (.*?)$/gm, '<li class="mb-2 text-slate-300 flex items-start gap-2"><span class="text-purple-400 mt-1">•</span><span>$1</span></li>');

    // Wrap consecutive list items
    html = html.replace(/(<li class="mb-2.*?<\/li>\n?)+/g, '<ul class="space-y-1 my-4 ml-4">$&</ul>');

    // === STEP 8: Numbered lists ===
    let listCounter = 0;
    html = html.replace(/^\d+\. (.*?)$/gm, () => {
      listCounter++;
      return `<li class="mb-3 text-slate-300 flex items-start gap-3"><span class="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center justify-center font-medium">${listCounter}</span><span>`;
    });

    // Close numbered list items (find where they end by looking for double newline or another list item)
    html = html.replace(/(<li class="mb-3.*?<span>)([^]*?)(?=\n\n|\n<li|$)/g, '$1$2</span></li>');

    // Wrap numbered lists
    html = html.replace(/(<li class="mb-3.*?<\/li>\n?)+/g, (match) => {
      listCounter = 0;
      return `<ol class="space-y-2 my-5 ml-4">${match}</ol>`;
    });

    // === STEP 9: Links ===
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-purple-400 hover:text-purple-300 underline underline-offset-2 transition-colors" target="_blank" rel="noopener noreferrer">$1</a>');

    // === STEP 10: Blockquotes ===
    html = html.replace(/^> (.*?)$/gm, '<blockquote class="border-l-4 border-purple-500/50 bg-slate-800/30 pl-4 pr-4 py-3 italic text-slate-400 my-4 rounded-r-lg">$1</blockquote>');

    // === STEP 11: Module/Component blocks ===
    // Pattern: **Module Name (file.py):** or **Module Name:**
    html = html.replace(
      /(<strong[^>]*>([^<]+)<\/strong>)\s*:\s*\n/g,
      '<div class="bg-slate-800/40 border-l-4 border-purple-500 rounded-r-lg p-4 my-6"><h4 class="text-lg font-semibold text-purple-300 mb-3">$1</h4><div class="text-slate-300 space-y-2">'
    );

    // === STEP 12: Paragraphs ===
    // Split by double newlines for paragraphs
    const blocks = html.split(/\n\n+/);
    html = blocks.map(block => {
      const trimmed = block.trim();
      // Skip if empty
      if (!trimmed) return '';
      // Skip if already a block element
      if (trimmed.match(/^<(h[1-6]|ul|ol|pre|div|blockquote|table|hr|li)/)) {
        return trimmed;
      }
      // Wrap in paragraph
      return `<p class="text-slate-300 leading-relaxed mb-4">${trimmed.replace(/\n/g, '<br/>')}</p>`;
    }).join('\n\n');

    // === STEP 13: Clean up orphaned closing tags ===
    html = html.replace(/<\/div>\s*<\/div>/g, '</div>');

    return html;
  }, [content]);

  return (
    <div
      className="markdown-content prose-invert max-w-none space-y-4"
      dangerouslySetInnerHTML={{ __html: renderMarkdown }}
    />
  );
}
