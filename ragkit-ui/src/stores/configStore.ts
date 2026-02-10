import { create } from 'zustand';

export type ExpertiseLevel = 'simple' | 'intermediate' | 'expert';

interface ConfigStoreState {
  config: Record<string, any>;
  expertiseLevel: ExpertiseLevel;
  jsonDraft: string;
  jsonError: string | null;
  setConfig: (config: Record<string, any>, options?: { syncJson?: boolean }) => void;
  setExpertiseLevel: (level: ExpertiseLevel) => void;
  setJsonDraft: (draft: string) => void;
}

export const useConfigStore = create<ConfigStoreState>((set, get) => ({
  config: {},
  expertiseLevel: 'simple',
  jsonDraft: '',
  jsonError: null,
  setConfig: (config, options) =>
    set((state) => ({
      config,
      jsonDraft:
        options?.syncJson === false
          ? state.jsonDraft
          : JSON.stringify(config ?? {}, null, 2),
      jsonError: null,
    })),
  setExpertiseLevel: (level) => set({ expertiseLevel: level }),
  setJsonDraft: (draft) => {
    set({ jsonDraft: draft });
    try {
      const parsed = JSON.parse(draft);
      set({ config: parsed, jsonError: null });
    } catch (error) {
      set({ jsonError: error instanceof Error ? error.message : 'Invalid JSON' });
    }
  },
}));
