const API_KEY_STORAGE_KEY = 'giteq_gemini_api_key';
const THEME_STORAGE_KEY = 'giteq_theme';

export function saveApiKey(apiKey: string): void {
  localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
}

export function getApiKey(): string | null {
  return localStorage.getItem(API_KEY_STORAGE_KEY);
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE_KEY);
}

export function saveTheme(theme: 'dark' | 'light'): void {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  document.documentElement.classList.toggle('dark', theme === 'dark');
}

export function getTheme(): 'dark' | 'light' {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  return (stored as 'dark' | 'light') || 'dark';
}
