import { useState } from "react";
import { Button, Card, CardContent, CardFooter, CardHeader, CardTitle, Select, useToast } from "../../components/ui";
import { ipc, WizardAnswers, WizardProfileResponse } from "../../lib/ipc";

interface ProfileStepProps {
  onNext: (payload: ProfileResult) => void;
  onBack: () => void;
  initialAnswers?: WizardAnswers;
}

export interface ProfileResult {
  answers: WizardAnswers;
  analysis: WizardProfileResponse;
}

const KB_TYPE_OPTIONS = [
  { value: "technical_documentation", label: "Technical documentation" },
  { value: "faq_support", label: "FAQ / Support" },
  { value: "legal_regulatory", label: "Legal / Regulatory" },
  { value: "reports_analysis", label: "Reports / Analysis" },
  { value: "general_knowledge", label: "General knowledge" },
];

export function ProfileStep({ onNext, onBack, initialAnswers }: ProfileStepProps) {
  const toast = useToast();
  const [answers, setAnswers] = useState<WizardAnswers>(
    initialAnswers || {
      kb_type: "technical_documentation",
      has_tables_diagrams: false,
      needs_multi_document: false,
      large_documents: false,
      needs_precision: false,
      frequent_updates: false,
      cite_page_numbers: false,
    }
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleToggle = (key: keyof WizardAnswers) => {
    setAnswers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleNext = async () => {
    setIsAnalyzing(true);
    try {
      const analysis = await ipc.analyzeWizardProfile(answers);
      onNext({ answers, analysis });
    } catch (error) {
      console.error("Failed to analyze profile:", error);
      toast.error("Profile analysis failed", "Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile your knowledge base</CardTitle>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Answer a few questions so we can recommend the best default configuration.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <Select
              label="Knowledge base type"
              options={KB_TYPE_OPTIONS}
              value={answers.kb_type}
              onChange={(e) =>
                setAnswers((prev) => ({ ...prev, kb_type: e.target.value }))
              }
            />

            <div className="space-y-3">
              <ToggleQuestion
                checked={answers.has_tables_diagrams}
                onChange={() => handleToggle("has_tables_diagrams")}
                label="Documents include tables or diagrams"
                description="Enable advanced parsing for structured content"
              />
              <ToggleQuestion
                checked={answers.needs_multi_document}
                onChange={() => handleToggle("needs_multi_document")}
                label="Answers must combine multiple documents"
                description="Increase retrieval depth and reranking"
              />
              <ToggleQuestion
                checked={answers.large_documents}
                onChange={() => handleToggle("large_documents")}
                label="Documents are often longer than 50 pages"
                description="Use larger chunks for long-form content"
              />
              <ToggleQuestion
                checked={answers.needs_precision}
                onChange={() => handleToggle("needs_precision")}
                label="You need highly precise answers"
                description="Favor accuracy, citations, and reranking"
              />
              <ToggleQuestion
                checked={answers.frequent_updates}
                onChange={() => handleToggle("frequent_updates")}
                label="Your knowledge base updates frequently"
                description="Enable incremental indexing and refresh"
              />
              <ToggleQuestion
                checked={answers.cite_page_numbers}
                onChange={() => handleToggle("cite_page_numbers")}
                label="Cite sources with page numbers"
                description="Enable page-level metadata in responses"
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="justify-between">
          <Button variant="ghost" onClick={onBack}>
            Back
          </Button>
          <Button onClick={handleNext} isLoading={isAnalyzing}>
            Analyze profile
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

function ToggleQuestion({
  checked,
  onChange,
  label,
  description,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
  description: string;
}) {
  return (
    <label className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/60">
      <input
        type="checkbox"
        className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
        checked={checked}
        onChange={onChange}
      />
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{label}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>
    </label>
  );
}
