import { FileText, GitBranch, Package } from 'lucide-react';
import { Repository, DocumentationSection } from '../types';

interface SidebarProps {
  repository: Repository;
  sections: DocumentationSection[];
  activeSection: string;
  onSectionClick: (sectionId: string) => void;
  onNewAnalysis: () => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({
  repository,
  sections,
  activeSection,
  onSectionClick,
  onNewAnalysis,
  isOpen,
  onClose,
}: SidebarProps) {
  const handleSectionClick = (sectionId: string) => {
    onSectionClick(sectionId);
    onClose();
  };

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}
      <aside className={`fixed left-0 top-16 bottom-0 w-80 bg-slate-900/95 md:bg-slate-900/50 backdrop-blur-sm border-r border-slate-700/50 flex flex-col z-50 transition-transform duration-300 ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-6 p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-3">
            {repository.owner}/{repository.name}
          </h3>

          <div className="flex flex-wrap gap-2 mb-3">
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
              <GitBranch className="w-3 h-3" />
              {repository.branch}
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs">
              <Package className="w-3 h-3" />
              {repository.architecture}
            </span>
          </div>

          <div className="space-y-1 text-sm text-slate-400">
            <div className="flex justify-between">
              <span>Files analyzed:</span>
              <span className="text-white font-medium">{repository.filesAnalyzed}</span>
            </div>
            <div className="flex justify-between">
              <span>Symbols extracted:</span>
              <span className="text-white font-medium">{repository.symbolsExtracted}</span>
            </div>
          </div>
        </div>

        <nav className="space-y-1">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => handleSectionClick(section.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-all ${
                activeSection === section.id
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                  : 'text-slate-300 hover:bg-slate-800/50 hover:text-white'
              }`}
            >
              <span className="text-lg">{section.icon}</span>
              <span className="font-medium">{section.title}</span>
            </button>
          ))}
        </nav>
      </div>

      <div className="p-6 border-t border-slate-700/50">
        <button
          onClick={onNewAnalysis}
          className="w-full px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-all hover:scale-[1.02]"
        >
          <FileText className="w-4 h-4 inline mr-2" />
          New Analysis
        </button>
      </div>
    </aside>
    </>
  );
}
