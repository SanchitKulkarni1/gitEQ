import { Check, Loader2 } from 'lucide-react';
import { AnalysisStatus } from '../types';

interface LoadingViewProps {
  progress: AnalysisStatus[];
  onCancel: () => void;
}

export default function LoadingView({ progress, onCancel }: LoadingViewProps) {
  const currentStep = progress.findIndex(step => !step.completed);
  const allComplete = currentStep === -1;

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-4rem)] p-6">
      <div className="max-w-lg w-full text-center space-y-8">
        <div className="flex justify-center">
          <div className="relative">
            <div className="w-24 h-24 border-4 border-purple-500/30 rounded-full"></div>
            <div className="absolute inset-0 w-24 h-24 border-4 border-t-purple-500 rounded-full animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="w-10 h-10 text-purple-400" />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-white">
            Analyzing Repository
          </h2>
          <p className="text-slate-400">Usually takes 30-60 seconds</p>
        </div>

        <div className="space-y-3 text-left bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          {progress.map((status, index) => (
            <div
              key={index}
              className={`flex items-start gap-3 transition-all ${
                index === currentStep
                  ? 'text-purple-300'
                  : status.completed
                  ? 'text-slate-400'
                  : 'text-slate-600'
              }`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {status.completed ? (
                  <Check className="w-5 h-5 text-green-500" />
                ) : index === currentStep ? (
                  <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
                ) : (
                  <div className="w-5 h-5 border-2 border-slate-600 rounded-full"></div>
                )}
              </div>
              <span className="font-medium">{status.message}</span>
            </div>
          ))}
        </div>

        <button
          onClick={onCancel}
          className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-all"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
