import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { AlertTriangle, Trash2, Info } from "lucide-react";
import { Button } from "./Button";
import { Modal, ModalFooter } from "./Modal";
import { cn } from "@/lib/utils";

// Types
export type ConfirmVariant = "danger" | "warning" | "info";

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmVariant;
}

interface ConfirmContextValue {
  confirm: (options: ConfirmOptions) => Promise<boolean>;
}

// Context
const ConfirmContext = createContext<ConfirmContextValue | null>(null);

// Hook
export function useConfirm() {
  const context = useContext(ConfirmContext);
  if (!context) {
    throw new Error("useConfirm must be used within a ConfirmProvider");
  }
  return context.confirm;
}

// Provider
interface ConfirmProviderProps {
  children: ReactNode;
}

export function ConfirmProvider({ children }: ConfirmProviderProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [options, setOptions] = useState<ConfirmOptions | null>(null);
  const [resolveRef, setResolveRef] = useState<((value: boolean) => void) | null>(null);

  const confirm = useCallback((opts: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setOptions(opts);
      setResolveRef(() => resolve);
      setIsOpen(true);
    });
  }, []);

  const handleConfirm = () => {
    setIsOpen(false);
    resolveRef?.(true);
  };

  const handleCancel = () => {
    setIsOpen(false);
    resolveRef?.(false);
  };

  const variant = options?.variant || "danger";

  const icons = {
    danger: Trash2,
    warning: AlertTriangle,
    info: Info,
  };

  const colors = {
    danger: {
      bg: "bg-red-100 dark:bg-red-900/30",
      icon: "text-red-600 dark:text-red-400",
      button: "danger" as const,
    },
    warning: {
      bg: "bg-yellow-100 dark:bg-yellow-900/30",
      icon: "text-yellow-600 dark:text-yellow-400",
      button: "primary" as const,
    },
    info: {
      bg: "bg-blue-100 dark:bg-blue-900/30",
      icon: "text-blue-600 dark:text-blue-400",
      button: "primary" as const,
    },
  };

  const Icon = icons[variant];
  const colorClasses = colors[variant];

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}

      <Modal
        isOpen={isOpen}
        onClose={handleCancel}
        showCloseButton={false}
        closeOnOverlayClick={false}
        size="sm"
      >
        {options && (
          <div className="text-center">
            <div
              className={cn(
                "w-12 h-12 mx-auto rounded-xl flex items-center justify-center mb-4",
                colorClasses.bg
              )}
            >
              <Icon className={cn("w-6 h-6", colorClasses.icon)} />
            </div>

            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {options.title}
            </h3>

            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {options.message}
            </p>

            <div className="flex gap-3 justify-center">
              <Button variant="secondary" onClick={handleCancel}>
                {options.cancelLabel || "Cancel"}
              </Button>
              <Button variant={colorClasses.button} onClick={handleConfirm}>
                {options.confirmLabel || "Confirm"}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </ConfirmContext.Provider>
  );
}
