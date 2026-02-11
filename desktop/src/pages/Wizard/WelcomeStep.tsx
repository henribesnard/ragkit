import { useTranslation } from "react-i18next";
import { Database, Shield, Sparkles, Zap } from "lucide-react";
import { Button, Card, CardContent, CardFooter, CardHeader, CardTitle } from "../../components/ui";

interface WelcomeStepProps {
  onNext: () => void;
}

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  const { t } = useTranslation();

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <CardTitle>{t("wizard.welcome.title")}</CardTitle>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("wizard.welcome.subtitle")}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            <FeatureCard
              icon={Shield}
              title={t("wizard.welcome.features.localFirst.title")}
              description={t("wizard.welcome.features.localFirst.description")}
            />
            <FeatureCard
              icon={Zap}
              title={t("wizard.welcome.features.fast.title")}
              description={t("wizard.welcome.features.fast.description")}
            />
            <FeatureCard
              icon={Database}
              title={t("wizard.welcome.features.flexible.title")}
              description={t("wizard.welcome.features.flexible.description")}
            />
          </div>
          <p className="mt-6 text-gray-600 dark:text-gray-400">
            {t("wizard.welcome.body")}
          </p>
        </CardContent>
        <CardFooter className="justify-end">
          <Button onClick={onNext}>{t("wizard.welcome.cta")}</Button>
        </CardFooter>
      </Card>
    </div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof Shield;
  title: string;
  description: string;
}) {
  return (
    <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800 text-center border border-gray-200 dark:border-gray-700">
      <div className="w-10 h-10 mx-auto rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-3">
        <Icon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
      </div>
      <h3 className="font-medium text-gray-900 dark:text-white">{title}</h3>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>
    </div>
  );
}
