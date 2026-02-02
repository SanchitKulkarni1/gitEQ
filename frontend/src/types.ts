export interface Repository {
  owner: string;
  name: string;
  branch: string;
  architecture: string;
  filesAnalyzed: number;
  symbolsExtracted: number;
}

export interface DocumentationSection {
  id: string;
  title: string;
  icon: string;
  content: string;
}

export interface Documentation {
  repository: Repository;
  sections: DocumentationSection[];
  fullMarkdown: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface AnalysisStatus {
  step: number;
  message: string;
  completed: boolean;
}

export type AppState =
  | { type: 'initial' }
  | { type: 'loading'; progress: AnalysisStatus[] }
  | { type: 'documentation'; data: Documentation; analysisId: string }
  | { type: 'error'; message: string };
