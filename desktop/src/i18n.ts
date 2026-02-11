import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import fr from "./locales/fr.json";

const STORAGE_KEY = "ragkit.language";

const getInitialLanguage = (): string => {
  if (typeof window !== "undefined") {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored && ["fr", "en"].includes(stored)) {
        return stored;
      }
    } catch {
      // Ignore storage access issues and fall back to default.
    }
  }
  return "fr";
};

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    fr: { translation: fr },
  },
  lng: getInitialLanguage(),
  fallbackLng: "en",
  supportedLngs: ["fr", "en"],
  interpolation: {
    escapeValue: false,
  },
});

i18n.on("languageChanged", (lng) => {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, lng);
  } catch {
    // Ignore storage errors.
  }
});

export default i18n;
