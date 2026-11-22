import { createContext, useContext } from "react";

export interface OnboardingControls {
  isTourOpen: boolean;
  /** Increments on every start so the tour restarts from the first step. */
  tourSession: number;
  startTour: () => void;
  finishTour: () => void;
}

const OnboardingContext = createContext<OnboardingControls | null>(null);

export const useOnboarding = () => {
  const context = useContext(OnboardingContext);

  if (context === null) {
    throw new Error("useOnboarding must be used within an OnboardingProvider");
  }

  return context;
};

export default OnboardingContext;
