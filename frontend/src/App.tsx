import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import InitialView from './components/InitialView';
import LoadingView from './components/LoadingView';
import DocumentationView from './components/DocumentationView';
import ErrorView from './components/ErrorView';
import ChatBot from './components/ChatBot';
import { AppState, Documentation, AnalysisStatus } from './types';
import { startAnalysis, getAnalysisStatus } from './utils/api';

const ANALYSIS_STEPS: AnalysisStatus[] = [
  { step: 1, message: 'Fetching repository structure...', completed: false },
  { step: 2, message: 'Extracting code symbols...', completed: false },
  { step: 3, message: 'Building dependency graph...', completed: false },
  { step: 4, message: 'Detecting architecture...', completed: false },
  { step: 5, message: 'Running stress analysis...', completed: false },
  { step: 6, message: 'Generating documentation...', completed: false },
];

function App() {
  const [apiKey, setApiKey] = useState('');
  const [appState, setAppState] = useState<AppState>({ type: 'initial' });
  const [activeSection, setActiveSection] = useState('');
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  const startPolling = useCallback((analysisId: string) => {
    let currentStep = 0;

    const interval = setInterval(async () => {
      try {
        const result = await getAnalysisStatus(analysisId);

        if (currentStep < ANALYSIS_STEPS.length) {
          setAppState({
            type: 'loading',
            progress: ANALYSIS_STEPS.map((step, index) => ({
              ...step,
              completed: index <= currentStep,
            })),
          });
          currentStep++;
        }

        if (result.status === 'completed' && result.result) {
          clearInterval(interval);
          setPollingInterval(null);

          const documentation: Documentation = {
            repository: {
              owner: result.result.repository.owner,
              name: result.result.repository.name,
              branch: result.result.repository.branch,
              architecture: result.result.repository.architecture,
              filesAnalyzed: result.result.repository.files_analyzed,
              symbolsExtracted: result.result.repository.symbols_extracted,
            },
            sections: result.result.sections,
            fullMarkdown: result.result.full_markdown,
          };

          setAppState({
            type: 'documentation',
            data: documentation,
            analysisId,
          });

          if (documentation.sections.length > 0) {
            setActiveSection(documentation.sections[0].id);
          }
        } else if (result.status === 'failed') {
          clearInterval(interval);
          setPollingInterval(null);
          setAppState({
            type: 'error',
            message: result.error || 'Analysis failed. Please try again.',
          });
        }
      } catch (error) {
        clearInterval(interval);
        setPollingInterval(null);
        setAppState({
          type: 'error',
          message: error instanceof Error ? error.message : 'Failed to fetch analysis status',
        });
      }
    }, 2000);

    setPollingInterval(interval);
  }, []);

  const handleAnalyze = async (repoUrl: string) => {
    try {
      setAppState({
        type: 'loading',
        progress: ANALYSIS_STEPS.map((step) => ({ ...step, completed: false })),
      });

      const response = await startAnalysis({
        repo_url: repoUrl,
        api_key: apiKey,
      });

      startPolling(response.analysis_id);
    } catch (error) {
      setAppState({
        type: 'error',
        message: error instanceof Error ? error.message : 'Failed to start analysis',
      });
    }
  };

  const handleNewAnalysis = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
    setAppState({ type: 'initial' });
    setActiveSection('');
  };

  const handleCancel = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
    setAppState({ type: 'initial' });
  };

  const handleSectionClick = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.querySelector(`[data-section-id="${sectionId}"]`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header onApiKeyChange={setApiKey} />

      <div className="pt-16 flex">
        {appState.type === 'documentation' && (
          <Sidebar
            repository={appState.data.repository}
            sections={appState.data.sections}
            activeSection={activeSection}
            onSectionClick={handleSectionClick}
            onNewAnalysis={handleNewAnalysis}
            isOpen={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
          />
        )}

        {appState.type === 'documentation' && (
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="md:hidden fixed bottom-20 left-4 z-30 p-3 bg-purple-600 hover:bg-purple-500 text-white rounded-full shadow-lg"
          >
            {sidebarOpen ? '✕' : '☰'}
          </button>
        )}

        <main
          className={`flex-1 ${
            appState.type === 'documentation' ? 'md:ml-80' : ''
          } transition-all duration-300`}
        >
          {appState.type === 'initial' && (
            <InitialView hasApiKey={!!apiKey} onAnalyze={handleAnalyze} />
          )}

          {appState.type === 'loading' && (
            <LoadingView progress={appState.progress} onCancel={handleCancel} />
          )}

          {appState.type === 'documentation' && (
            <DocumentationView
              sections={appState.data.sections}
              fullMarkdown={appState.data.fullMarkdown}
              repoName={`${appState.data.repository.owner}/${appState.data.repository.name}`}
              activeSection={activeSection}
              onSectionChange={setActiveSection}
              onReAnalyze={handleNewAnalysis}
            />
          )}

          {appState.type === 'error' && (
            <ErrorView message={appState.message} onRetry={handleNewAnalysis} />
          )}
        </main>
      </div>

      <ChatBot
        analysisId={appState.type === 'documentation' ? appState.analysisId : null}
        apiKey={apiKey}
        repoName={
          appState.type === 'documentation'
            ? `${appState.data.repository.owner}/${appState.data.repository.name}`
            : ''
        }
      />
    </div>
  );
}

export default App;
