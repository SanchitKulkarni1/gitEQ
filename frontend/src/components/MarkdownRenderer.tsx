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

    // Handle code blocks FIRST (before other transformations)
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) => {
      const langLabel = lang ? `<span class="absolute top-2 right-3 text-xs text-slate-500 uppercase">${lang}</span>` : '';
      return `<div class="relative my-6"><pre class="bg-slate-900 border border-slate-700 rounded-xl p-4 pt-8 overflow-x-auto">${langLabel}<code class="text-sm font-mono text-emerald-400">${escapeHtml(code.trim())}</code></pre></div>`;
    });

    // Inline code (after code blocks to avoid conflicts)
    html = html.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 bg-slate-800/80 text-purple-300 rounded text-sm font-mono border border-slate-700">$1</code>');

    // Horizontal rules
    html = html.replace(/^[-*_]{3,}$/gm, '<hr class="my-8 border-t border-slate-700/50" />');

    // Headers with proper hierarchy and styling
    html = html.replace(/^#### (.*?)$/gm, '<h4 class="text-lg font-semibold text-slate-200 mt-6 mb-3 flex items-center gap-2"><span class="w-1 h-4 bg-purple-500 rounded"></span>$1</h4>');
    html = html.replace(/^### (.*?)$/gm, '<h3 class="text-xl font-bold text-white mt-8 mb-4 border-b border-slate-700/50 pb-2">$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2 class="text-2xl font-bold text-white mt-10 mb-5">$1</h2>');
    html = html.replace(/^# (.*?)$/gm, ''); // Skip h1 since section titles handle this

    // Bold and italic
    html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong class="font-bold text-white"><em>$1</em></strong>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>');
    html = html.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em class="italic text-slate-300">$1</em>');

    // Detect and style component/file blocks (patterns like "ComponentName ( file.py ):" or "**ComponentName**:")
    // These create visual card-like separation between different modules
    html = html.replace(
      /(<strong[^>]*>([^<]+(?:\s*\([^)]+\))?)<\/strong>)\s*:\s*(<br\s*\/?>|\n)?/g,
      '</p><div class="bg-slate-800/40 border border-slate-700/50 rounded-lg p-4 my-4"><h4 class="text-lg font-semibold text-purple-300 mb-2 flex items-center gap-2"><span class="w-2 h-2 bg-purple-500 rounded-full"></span>$1</h4><p class="text-slate-300">'
    );

    // Close component blocks before next component or section
    html = html.replace(/(<\/p>)(\s*<div class="bg-slate-800\/40)/g, '</p></div>$2');

    // Handle bullet lists with proper nesting
    html = html.replace(/^(\s*)\* (.*?)$/gm, (_, indent, text) => {
      const level = indent.length / 2;
      const marginClass = level > 0 ? `ml-${4 + level * 4}` : 'ml-4';
      return `<li class="${marginClass} mb-2 text-slate-300 flex items-start gap-2"><span class="text-purple-400 mt-1.5">•</span><span>${text}</span></li>`;
    });

    // Handle dash lists
    html = html.replace(/^- (.*?)$/gm, '<li class="ml-4 mb-2 text-slate-300 flex items-start gap-2"><span class="text-purple-400 mt-1.5">•</span><span>$1</span></li>');

    // Wrap consecutive list items in ul
    html = html.replace(/(<li class="ml-4.*?<\/li>\n?)+/g, '<ul class="space-y-1 my-4">$&</ul>');

    // Numbered lists
    let listCounter = 0;
    html = html.replace(/^\d+\. (.*?)$/gm, (_, text) => {
      listCounter++;
      return `<li class="ml-4 mb-3 text-slate-300 flex items-start gap-3"><span class="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center justify-center font-medium">${listCounter}</span><span>${text}</span></li>`;
    });
    html = html.replace(/(<li class="ml-4 mb-3.*?<\/li>\n?)+/g, (match) => {
      listCounter = 0; // Reset for next list
      return `<ol class="space-y-2 my-5">${match}</ol>`;
    });

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-purple-400 hover:text-purple-300 underline underline-offset-2 transition-colors" target="_blank" rel="noopener noreferrer">$1</a>');

    // Blockquotes with better styling
    html = html.replace(/^> (.*?)$/gm, '<blockquote class="border-l-4 border-purple-500/50 bg-slate-800/30 pl-4 pr-4 py-3 italic text-slate-400 my-4 rounded-r-lg">$1</blockquote>');

    // Tables (basic support)
    html = html.replace(/^\|(.+)\|$/gm, (match, content) => {
      const cells = content.split('|').map((cell: string) => cell.trim());
      const isHeader = cells.every((cell: string) => cell.match(/^[-:]+$/));
      if (isHeader) return ''; // Skip separator rows

      const cellTag = 'td';
      const cellHtml = cells.map((cell: string) =>
        `<${cellTag} class="px-4 py-2 border-b border-slate-700">${cell}</${cellTag}>`
      ).join('');
      return `<tr class="hover:bg-slate-800/50">${cellHtml}</tr>`;
    });
    html = html.replace(/(<tr.*?<\/tr>\n?)+/g, '<div class="overflow-x-auto my-6"><table class="w-full text-sm text-slate-300 border border-slate-700 rounded-lg overflow-hidden"><tbody>$&</tbody></table></div>');

    // Paragraphs - split by double newlines
    const blocks = html.split(/\n\n+/);
    html = blocks.map(block => {
      // Skip if already wrapped in a block element
      if (block.match(/^<(h[1-6]|ul|ol|pre|div|blockquote|table|hr)/)) {
        return block;
      }
      // Skip empty blocks
      if (!block.trim()) return '';
      // Wrap in paragraph
      return `<p class="text-slate-300 leading-relaxed mb-4">${block.replace(/\n/g, '<br/>')}</p>`;
    }).join('\n');

    return html;
  }, [content]);

  return (
    <div
      className="markdown-content prose-invert max-w-none"
      dangerouslySetInnerHTML={{ __html: renderMarkdown }}
    />
  );
}
