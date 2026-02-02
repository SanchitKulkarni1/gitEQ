import { useState, useEffect } from 'react';
import { Code2, Eye, EyeOff, Check, HelpCircle } from 'lucide-react';
import { saveApiKey, getApiKey } from '../utils/storage';

interface HeaderProps {
  onApiKeyChange: (key: string) => void;
}

export default function Header({ onApiKeyChange }: HeaderProps) {
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    const storedKey = getApiKey();
    if (storedKey) {
      setApiKey(storedKey);
      setIsSaved(true);
      onApiKeyChange(storedKey);
    }
  }, [onApiKeyChange]);

  const handleApiKeyChange = (value: string) => {
    setApiKey(value);
    setIsSaved(false);
    if (value.trim()) {
      saveApiKey(value);
      setIsSaved(true);
      onApiKeyChange(value);
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-slate-900/95 backdrop-blur-sm border-b border-slate-700/50 z-50">
      <div className="h-full max-w-screen-2xl mx-auto px-4 md:px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-white">
            <Code2 className="w-6 h-6 md:w-7 md:h-7 text-purple-400" />
            <span className="text-xl md:text-2xl font-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
              gitEQ
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 md:gap-4">
          <div className="flex items-center gap-2 md:gap-3">
            <label className="hidden md:block text-sm text-slate-400 whitespace-nowrap">
              Your Gemini API Key
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => handleApiKeyChange(e.target.value)}
                placeholder="API key"
                className="w-32 md:w-64 px-3 md:px-4 py-2 pr-16 md:pr-20 bg-slate-800 border border-slate-600 rounded-lg text-white text-xs md:text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button
                  onClick={() => setShowKey(!showKey)}
                  className="p-1 text-slate-400 hover:text-white transition-colors"
                  title={showKey ? 'Hide key' : 'Show key'}
                >
                  {showKey ? <EyeOff className="w-3 h-3 md:w-4 md:h-4" /> : <Eye className="w-3 h-3 md:w-4 md:h-4" />}
                </button>
                {isSaved && apiKey && (
                  <Check className="w-3 h-3 md:w-4 md:h-4 text-green-500" />
                )}
              </div>
            </div>
            <div className="relative">
              <button
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                onClick={() => setShowTooltip(!showTooltip)}
                className="p-1 text-slate-400 hover:text-white transition-colors"
              >
                <HelpCircle className="w-4 h-4 md:w-5 md:h-5" />
              </button>
              {showTooltip && (
                <div className="absolute top-full right-0 mt-2 w-56 md:w-64 p-3 bg-slate-800 border border-slate-600 rounded-lg shadow-xl text-xs text-slate-300 z-50">
                  Get your free API key from{' '}
                  <a
                    href="https://ai.google.dev"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-400 hover:text-purple-300 underline"
                  >
                    ai.google.dev
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
