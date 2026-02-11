import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '@/stores/appStore';
import { Menu } from 'lucide-react';

export function Header() {
  const navigate = useNavigate();
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);
  const { t, i18n } = useTranslation();

  return (
    <header className="flex items-center justify-between border-b border-white/40 bg-white/70 px-8 py-6 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="rounded-xl p-2 text-muted hover:bg-white/80 lg:hidden"
          aria-label={t('header.toggleSidebar')}
        >
          <Menu size={20} />
        </button>
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-muted">{t('header.overview')}</p>
          <h2 className="text-2xl font-display">{t('header.subtitle')}</h2>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <select
          className="rounded-full border border-slate-200 bg-white/80 px-3 py-1 text-xs font-semibold text-ink outline-none transition focus:border-accent/60 focus:ring-2 focus:ring-accent/20"
          value={i18n.language}
          onChange={(event) => i18n.changeLanguage(event.target.value)}
          aria-label={t('common.labels.language')}
        >
          <option value="fr">{t('common.languages.fr')}</option>
          <option value="en">{t('common.languages.en')}</option>
        </select>
        <span className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
          {t('header.live')}
        </span>
        <button
          onClick={() => navigate('/ingestion')}
          className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white shadow-soft"
        >
          {t('header.newRun')}
        </button>
      </div>
    </header>
  );
}
