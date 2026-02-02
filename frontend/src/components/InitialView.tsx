import { useState } from 'react';
import { Github, Sparkles } from 'lucide-react';
import { validateGitHubUrl } from '../utils/markdown';

interface InitialViewProps {
  hasApiKey: boolean;
  onAnalyze: (repoUrl: string) => void;
}

export default function InitialView({ hasApiKey, onAnalyze }: InitialViewProps) {
  const [repoUrl, setRepoUrl] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!repoUrl.trim()) {
      setError('Please enter a repository URL');
      return;
    }

    if (!validateGitHubUrl(repoUrl)) {
      setError('Please enter a valid GitHub repository URL');
      return;
    }

    onAnalyze(repoUrl);
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-4rem)] p-6">
      <div className="max-w-2xl w-full text-center space-y-8">
        <div className="space-y-4">
          <div className="flex items-center justify-center gap-3 mb-6">
            <Github className="w-16 h-16 text-purple-400" />
            <Sparkles className="w-12 h-12 text-purple-300 animate-pulse" />
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">
            Analyze Any GitHub Repository
          </h1>
          <p className="text-xl text-slate-400">
            Paste a public repo URL to generate AI-powered documentation
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => {
                setRepoUrl(e.target.value);
                setError('');
              }}
              placeholder="https://github.com/owner/repository"
              className={`w-full px-6 py-4 bg-slate-800 border ${
                error ? 'border-red-500' : 'border-slate-600'
              } rounded-xl text-white text-lg placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all`}
            />
            {error && (
              <p className="mt-2 text-sm text-red-400 text-left">{error}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={!hasApiKey}
            className="w-full px-8 py-4 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 disabled:from-slate-700 disabled:to-slate-800 disabled:cursor-not-allowed text-white text-lg font-semibold rounded-xl transition-all hover:scale-[1.02] hover:shadow-lg hover:shadow-purple-500/50 disabled:hover:scale-100 disabled:hover:shadow-none"
            title={!hasApiKey ? 'Enter your Gemini API key first' : ''}
          >
            {hasApiKey ? (
              <>
                <Sparkles className="w-5 h-5 inline mr-2" />
                Generate Documentation
              </>
            ) : (
              'Enter your Gemini API key first'
            )}
          </button>
        </form>

        <div className="pt-8 text-sm text-slate-500">
          <p>No login required. Your API key is stored locally in your browser.</p>
        </div>
      </div>
    </div>
  );
}
