import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorViewProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorView({ message, onRetry }: ErrorViewProps) {
  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-4rem)] p-6">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="p-4 bg-red-500/20 rounded-full">
            <AlertCircle className="w-16 h-16 text-red-400" />
          </div>
        </div>

        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-white">Analysis Failed</h2>
          <p className="text-slate-400">{message}</p>
        </div>

        <button
          onClick={onRetry}
          className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition-all hover:scale-[1.02]"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      </div>
    </div>
  );
}
