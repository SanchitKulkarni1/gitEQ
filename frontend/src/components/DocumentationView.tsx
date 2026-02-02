import { useEffect, useRef, useState } from 'react';
import { Copy, Download, RefreshCw, Check } from 'lucide-react';
import { DocumentationSection } from '../types';
import { copyToClipboard, downloadAsMarkdown } from '../utils/markdown';
import MarkdownRenderer from './MarkdownRenderer';

interface DocumentationViewProps {
  sections: DocumentationSection[];
  fullMarkdown: string;
  repoName: string;
  activeSection: string;
  onSectionChange: (sectionId: string) => void;
  onReAnalyze: () => void;
}

export default function DocumentationView({
  sections,
  fullMarkdown,
  repoName,
  activeSection,
  onSectionChange,
  onReAnalyze,
}: DocumentationViewProps) {
  const [copied, setCopied] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const sectionRefs = useRef<{ [key: string]: HTMLElement | null }>({});

  useEffect(() => {
    const observerOptions = {
      root: contentRef.current,
      rootMargin: '-100px 0px -66%',
      threshold: 0,
    };

    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const sectionId = entry.target.getAttribute('data-section-id');
          if (sectionId) {
            onSectionChange(sectionId);
          }
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);

    Object.values(sectionRefs.current).forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => observer.disconnect();
  }, [sections, onSectionChange]);

  const handleCopy = async () => {
    try {
      await copyToClipboard(fullMarkdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleDownload = () => {
    downloadAsMarkdown(fullMarkdown, `${repoName}-documentation.md`);
  };

  return (
    <div className="flex-1 flex flex-col">
      <div className="sticky top-16 z-10 bg-slate-900/95 backdrop-blur-sm border-b border-slate-700/50 px-8 py-4">
        <div className="flex items-center justify-between max-w-5xl mx-auto">
          <h1 className="text-2xl font-bold text-white">Documentation</h1>
          <div className="flex items-center gap-3">
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-all hover:scale-[1.02]"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-green-500" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy Markdown
                </>
              )}
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-all hover:scale-[1.02]"
            >
              <Download className="w-4 h-4" />
              Download MD
            </button>
            <button
              onClick={onReAnalyze}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition-all hover:scale-[1.02]"
            >
              <RefreshCw className="w-4 h-4" />
              Re-analyze
            </button>
          </div>
        </div>
      </div>

      <div
        ref={contentRef}
        className="flex-1 overflow-y-auto px-8 py-8"
      >
        <div className="max-w-5xl mx-auto space-y-12">
          {sections.map((section) => (
            <section
              key={section.id}
              ref={(el) => (sectionRefs.current[section.id] = el)}
              data-section-id={section.id}
              className="scroll-mt-32"
            >
              <div className="flex items-center gap-3 mb-6">
                <span className="text-3xl">{section.icon}</span>
                <h2 className="text-3xl font-bold text-white">{section.title}</h2>
              </div>
              <div className="prose prose-invert prose-purple max-w-none">
                <MarkdownRenderer content={section.content} />
              </div>
              {section !== sections[sections.length - 1] && (
                <div className="mt-12 border-t border-slate-700/50"></div>
              )}
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
