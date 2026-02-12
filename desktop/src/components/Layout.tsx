import { ReactNode, useState } from "react";
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  MessageSquare,
  Database,
  List,
  Settings,
  Sun,
  Moon,
  Menu,
} from "lucide-react";
import { clsx } from "clsx";

interface LayoutProps {
  children: ReactNode;
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export function Layout({ children, darkMode, onToggleDarkMode }: LayoutProps) {
  const { t } = useTranslation();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navItems = [
    { to: "/chat", icon: MessageSquare, label: t("navigation.chat") },
    { to: "/knowledge-bases", icon: Database, label: t("navigation.knowledgeBases") },
    { to: "/ingestion", icon: List, label: "Ingestion" },
    { to: "/settings", icon: Settings, label: t("navigation.settings") },
    { to: "/logs", icon: List, label: t("navigation.logs") },
  ];

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside
        className={clsx(
          "flex flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300",
          sidebarOpen ? "w-64" : "w-16"
        )}
      >
        {/* Logo */}
        <div className="flex items-center h-16 px-4 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <Menu className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          {sidebarOpen && (
            <span className="ml-3 text-xl font-bold text-primary-600 dark:text-primary-400">
              RAGKIT
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center px-4 py-3 mx-2 rounded-lg transition-colors",
                  isActive
                    ? "bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                )
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="ml-3">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Theme toggle */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onToggleDarkMode}
            className={clsx(
              "flex items-center w-full px-3 py-2 rounded-lg transition-colors",
              "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
            )}
          >
            {darkMode ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
            {sidebarOpen && (
              <span className="ml-3">
                {darkMode ? t("layout.lightMode") : t("layout.darkMode")}
              </span>
            )}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
