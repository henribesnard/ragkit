import { useState } from "react";
import { FolderOpen } from "lucide-react";
import { Button, Card, CardContent, CardFooter, CardHeader, CardTitle, Input } from "../../components/ui";
import { ipc } from "../../lib/ipc";

export interface FolderSelection {
  path: string;
  recursive: boolean;
}

interface FolderStepProps {
  onNext: (folder: FolderSelection) => void;
  onBack: () => void;
  initialFolder?: FolderSelection | null;
}

export function FolderStep({ onNext, onBack, initialFolder }: FolderStepProps) {
  const [path, setPath] = useState(initialFolder?.path || "");
  const [recursive, setRecursive] = useState(initialFolder?.recursive ?? true);

  const handleBrowse = async () => {
    const selected = await ipc.selectFolder();
    if (selected) {
      setPath(selected);
    }
  };

  const handleNext = () => {
    onNext({ path: path.trim(), recursive });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>Select your documents folder</CardTitle>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Choose the folder that contains the documents you want to index.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1">
              <Input
                label="Folder path"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                placeholder="Select a folder..."
              />
            </div>
            <Button variant="secondary" onClick={handleBrowse}>
              <FolderOpen className="w-4 h-4 mr-2" />
              Browse
            </Button>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              checked={recursive}
              onChange={(e) => setRecursive(e.target.checked)}
            />
            Include subfolders
          </label>

          <p className="text-sm text-gray-500 dark:text-gray-400">
            You can add or change folders later from the knowledge base screen.
          </p>
        </CardContent>
        <CardFooter className="justify-between">
          <Button variant="ghost" onClick={onBack}>
            Back
          </Button>
          <Button onClick={handleNext}>Continue</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
