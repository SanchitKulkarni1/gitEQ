# gitEQ - AI-Powered GitHub Repository Analyzer

A clean, minimal single-page web app that generates intelligent documentation for any public GitHub repository and provides an AI chatbot for codebase Q&A.

## Features

- **No Authentication Required** - Just provide your own Gemini API key
- **Repository Analysis** - Analyzes repository structure, dependencies, and architecture
- **AI-Generated Documentation** - Creates comprehensive documentation with multiple sections
- **Interactive Chatbot** - Ask questions about the codebase and get AI-powered answers
- **Dark/Light Mode** - Toggle between themes
- **Mobile Responsive** - Works on all device sizes
- **Export Options** - Copy markdown or download documentation

## Getting Started

### Prerequisites

- Node.js 18+ installed
- A Gemini API key (get one free at [ai.google.dev](https://ai.google.dev))

### Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file (optional):
   ```bash
   cp .env.example .env
   ```

   Edit `.env` if you want to change the API URL (default is `http://localhost:8000`)

4. Start the development server:
   ```bash
   npm run dev
   ```

### Backend Setup

This frontend requires a FastAPI backend running at `http://localhost:8000` (or the URL specified in your `.env` file).

The backend should provide these endpoints:

- `POST /api/analyze` - Start repository analysis
- `GET /api/analysis/{analysis_id}` - Get analysis status
- `POST /api/chat` - Send chat messages

## Usage

1. **Enter Your API Key**: Paste your Gemini API key in the header (it's stored locally in your browser)
2. **Analyze a Repository**: Enter a GitHub repository URL and click "Generate Documentation"
3. **View Documentation**: Browse through the generated documentation sections using the sidebar
4. **Chat with AI**: Click the "Ask AI" button to ask questions about the codebase

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Supabase** (available for data persistence if needed)

## Project Structure

```
src/
├── components/        # React components
│   ├── Header.tsx    # Top navigation with API key input
│   ├── Sidebar.tsx   # Documentation navigation
│   ├── InitialView.tsx    # Landing page
│   ├── LoadingView.tsx    # Analysis progress
│   ├── DocumentationView.tsx  # Documentation display
│   ├── ChatBot.tsx   # AI chat interface
│   ├── ErrorView.tsx # Error state
│   └── MarkdownRenderer.tsx  # Markdown rendering
├── utils/            # Utility functions
│   ├── api.ts       # API integration
│   ├── storage.ts   # LocalStorage management
│   └── markdown.ts  # Markdown utilities
├── types.ts         # TypeScript interfaces
├── App.tsx          # Main application
└── main.tsx         # Entry point
```

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## License

MIT
