import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ThemeStore {
  darkMode: boolean;
  toggleDarkMode: () => void;
  setDarkMode: (dark: boolean) => void;
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      darkMode: false,
      
      toggleDarkMode: () => {
        const newMode = !get().darkMode;
        set({ darkMode: newMode });
        // Apply to document
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('dark', newMode);
        }
      },
      
      setDarkMode: (dark: boolean) => {
        set({ darkMode: dark });
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('dark', dark);
        }
      },
    }),
    {
      name: 'theme-storage',
      // Apply theme on hydration
      onRehydrateStorage: () => (state) => {
        if (state?.darkMode && typeof document !== 'undefined') {
          document.documentElement.classList.add('dark');
        }
      },
    }
  )
);
