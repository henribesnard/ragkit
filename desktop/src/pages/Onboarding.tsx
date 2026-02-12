import { Wizard } from "./Wizard";

interface OnboardingProps {
  onComplete: () => void;
}

export function Onboarding({ onComplete }: OnboardingProps) {
  return <Wizard onComplete={onComplete} />;
}
