import { Globe } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";

interface LanguageSelectorProps {
  variant?: "compact" | "full";
  className?: string;
}

export function LanguageSelector({
  variant = "compact",
  className,
}: LanguageSelectorProps) {
  const { t, i18n } = useTranslation();

  const options = [
    { value: "fr", label: t("language.fr") },
    { value: "en", label: t("language.en") },
  ];

  const handleChange = (lang: string) => {
    if (lang && lang !== i18n.language) {
      i18n.changeLanguage(lang);
    }
  };

  if (variant === "full") {
    return (
      <div className={cn("space-y-2", className)}>
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {t("settings.language.label")}
        </p>
        <div className="flex flex-wrap gap-2">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleChange(option.value)}
              className={cn(
                "px-4 py-2 rounded-lg border text-sm font-medium transition-colors",
                i18n.language === option.value
                  ? "bg-primary-600 text-white border-primary-600"
                  : "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200"
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Globe className="w-4 h-4 text-gray-500" />
      <select
        value={i18n.language}
        onChange={(event) => handleChange(event.target.value)}
        className="text-sm border rounded px-2 py-1 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
