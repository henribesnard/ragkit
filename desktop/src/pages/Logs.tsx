import { useEffect, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import {
    RefreshCw,
    Trash2,
    Search,
    AlertCircle,
    Info,
    AlertTriangle,
    PlayCircle
} from "lucide-react";
import { ipc } from "@/lib/ipc";
import { cn } from "@/lib/utils";
import {
    Button,
    Input,
    Select,
    Card,
    CardContent,
    CardHeader,
    useToast
} from "@/components/ui";

interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
    module: string;
    line?: number;
    exception?: string;
}

export default function Logs() {
    const { t } = useTranslation();
    const { success, error: toastError } = useToast();
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [search, setSearch] = useState("");
    const [levelFilter, setLevelFilter] = useState("ALL");
    const [autoRefresh, setAutoRefresh] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    const fetchLogs = async () => {
        try {
            setIsLoading(true);
            const data = await ipc.getLogs(1000);
            setLogs(data);
        } catch (error) {
            console.error("Failed to fetch logs", error);
        } finally {
            setIsLoading(false);
        }
    };

    const clearLogs = async () => {
        try {
            await ipc.clearLogs();
            setLogs([]);
            setLogs([]);
            success(t("logs.cleared"), t("logs.clearedDescription"));
        } catch (err) {
            toastError(t("common.error"), String(err));
        }
    };

    useEffect(() => {
        fetchLogs();

        // Auto-refresh interval
        let interval: ReturnType<typeof setInterval>;
        if (autoRefresh) {
            interval = setInterval(fetchLogs, 2000);
        }
        return () => clearInterval(interval);
    }, [autoRefresh]);

    useEffect(() => {
        let result = logs;

        if (levelFilter !== "ALL") {
            result = result.filter((log) => log.level === levelFilter);
        }

        if (search) {
            const lowerSearch = search.toLowerCase();
            result = result.filter(
                (log) =>
                    log.message.toLowerCase().includes(lowerSearch) ||
                    log.module.toLowerCase().includes(lowerSearch) ||
                    log.exception?.toLowerCase().includes(lowerSearch)
            );
        }

        setFilteredLogs(result);
    }, [logs, search, levelFilter]);

    // Auto-scroll to bottom when new logs arrive
    useEffect(() => {
        if (scrollRef.current && autoRefresh) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [filteredLogs, autoRefresh]);

    const getLevelColor = (level: string) => {
        switch (level) {
            case "ERROR":
            case "CRITICAL":
                return "text-red-600 dark:text-red-400";
            case "WARNING":
                return "text-yellow-600 dark:text-yellow-400";
            case "INFO":
                return "text-blue-600 dark:text-blue-400";
            case "DEBUG":
                return "text-gray-600 dark:text-gray-400";
            default:
                return "text-gray-800 dark:text-gray-200";
        }
    };

    const getLevelIcon = (level: string) => {
        switch (level) {
            case "ERROR":
            case "CRITICAL":
                return <AlertCircle className="w-4 h-4" />;
            case "WARNING":
                return <AlertTriangle className="w-4 h-4" />;
            case "INFO":
                return <Info className="w-4 h-4" />;
            default:
                return <div className="w-4 h-4" />;
        }
    };

    return (
        <div className="container py-6 space-y-6 h-[calc(100vh-4rem)] flex flex-col">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">{t("logs.title")}</h1>
                    <p className="text-muted-foreground">{t("logs.subtitle")}</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant={autoRefresh ? "primary" : "outline"}
                        size="sm"
                        onClick={() => setAutoRefresh(!autoRefresh)}
                    >
                        <PlayCircle className={cn("w-4 h-4 mr-2", autoRefresh && "animate-pulse")} />
                        {autoRefresh ? t("logs.autoRefreshOn") : t("logs.autoRefreshOff")}
                    </Button>
                    <Button variant="outline" size="sm" onClick={fetchLogs} disabled={isLoading}>
                        <RefreshCw className={cn("w-4 h-4 mr-2", isLoading && "animate-spin")} />
                        {t("common.actions.refresh")}
                    </Button>
                    <Button variant="danger" size="sm" onClick={clearLogs}>
                        <Trash2 className="w-4 h-4 mr-2" />
                        {t("logs.clear")}
                    </Button>
                </div>
            </div>

            <Card className="flex-1 flex flex-col overflow-hidden">
                <CardHeader className="py-3 px-4 border-b bg-muted/50">
                    <div className="flex items-center gap-4">
                        <div className="relative flex-1 max-w-sm">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder={t("logs.searchPlaceholder")}
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="pl-9 h-9"
                            />
                        </div>
                        <div className="w-[150px]">
                            <Select
                                value={levelFilter}
                                onChange={(e) => setLevelFilter(e.target.value)}
                                options={[
                                    { value: "ALL", label: t("logs.levels.all") },
                                    { value: "INFO", label: "INFO" },
                                    { value: "WARNING", label: "WARNING" },
                                    { value: "ERROR", label: "ERROR" },
                                    { value: "DEBUG", label: "DEBUG" },
                                ]}
                            />
                        </div>
                        <div className="ml-auto text-xs text-muted-foreground">
                            {filteredLogs.length} {t("logs.entries")}
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="p-0 flex-1 overflow-auto bg-black/90 text-primary-foreground font-mono text-xs" ref={scrollRef}>
                    {filteredLogs.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                            <Info className="w-8 h-8 mb-2 opacity-50" />
                            <p>{t("logs.noLogs")}</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-800">
                            {filteredLogs.map((log, index) => (
                                <div key={index} className="flex gap-4 p-2 hover:bg-white/5 transition-colors">
                                    <div className="shrink-0 text-gray-500 w-32 tabular-nums">
                                        {new Date(log.timestamp).toLocaleTimeString()}
                                    </div>
                                    <div className={cn("shrink-0 w-16 font-bold flex items-center gap-1", getLevelColor(log.level))}>
                                        {getLevelIcon(log.level)}
                                        {log.level}
                                    </div>
                                    <div className="flex-1 break-all">
                                        <span className="text-gray-400 mr-2">[{log.module}]</span>
                                        {log.message}
                                        {log.exception && (
                                            <pre className="mt-1 p-2 bg-red-900/20 text-red-300 rounded overflow-x-auto">
                                                {log.exception}
                                            </pre>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
