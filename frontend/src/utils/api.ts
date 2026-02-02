// Auto-detect environment: use production backend on Vercel, localhost for development
const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://giteq.onrender.com';

export interface AnalyzeRequest {
  repo_url: string;
  api_key: string;
}

export interface AnalyzeResponse {
  analysis_id: string;
  status: string;
}

export interface AnalysisResult {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: {
    repository: {
      owner: string;
      name: string;
      branch: string;
      architecture: string;
      files_analyzed: number;
      symbols_extracted: number;
    };
    sections: Array<{
      id: string;
      title: string;
      icon: string;
      content: string;
    }>;
    full_markdown: string;
  };
  error?: string;
}

export interface ChatRequest {
  analysis_id: string;
  question: string;
  api_key: string;
}

export interface ChatResponse {
  answer: string;
  intent?: string;
}

export async function startAnalysis(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(error.detail || 'Failed to start analysis');
  }

  return response.json();
}

export async function getAnalysisStatus(analysisId: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/analysis/${analysisId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch analysis status');
  }

  return response.json();
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Chat request failed' }));
    throw new Error(error.detail || 'Failed to send message');
  }

  return response.json();
}
