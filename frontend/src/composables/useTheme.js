import { ref } from 'vue';

const STORAGE_KEY = 'raglab.theme';
const theme = ref('parchment'); // 'parchment' | 'dark'

// Initialize from localStorage on first load.
if (typeof window !== 'undefined') {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === 'dark' || saved === 'parchment') {
    theme.value = saved;
  }
  applyTheme(theme.value);
}

function applyTheme(t) {
  if (typeof document === 'undefined') return;
  if (t === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
}

export function useTheme() {
  function toggleTheme() {
    theme.value = theme.value === 'parchment' ? 'dark' : 'parchment';
    applyTheme(theme.value);
    localStorage.setItem(STORAGE_KEY, theme.value);
  }

  return { theme, toggleTheme };
}
