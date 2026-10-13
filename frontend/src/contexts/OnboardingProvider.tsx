import {
  FunctionComponent,
  PropsWithChildren,
  useCallback,
  useMemo,
  useState,
} from "react";
import OnboardingContext, { OnboardingControls } from "@/contexts/Onboarding";

const OnboardingProvider: FunctionComponent<PropsWithChildren> = ({
  children,
}) => {
  const [isTourOpen, setIsTourOpen] = useState(false);
  const [tourSession, setTourSession] = useState(0);

  const startTour = useCallback(() => {
    setTourSession((current) => current + 1);
    setIsTourOpen(true);
  }, []);

  const finishTour = useCallback(() => {
    setIsTourOpen(false);
  }, []);

  const value = useMemo<OnboardingControls>(
    () => ({ isTourOpen, tourSession, startTour, finishTour }),
    [isTourOpen, tourSession, startTour, finishTour],
  );

  return (
    <OnboardingContext.Provider value={value}>
      {children}
    </OnboardingContext.Provider>
  );
};

export default OnboardingProvider;
