import {
  FunctionComponent,
  PropsWithChildren,
  useCallback,
  useMemo,
  useState,
} from "react";
import { useSettingsMutation } from "@/apis/hooks";
import OnboardingContext, { OnboardingControls } from "@/contexts/Onboarding";

const OnboardingProvider: FunctionComponent<PropsWithChildren> = ({
  children,
}) => {
  const [isTourOpen, setIsTourOpen] = useState(false);
  const [tourSession, setTourSession] = useState(0);
  const { mutate } = useSettingsMutation({ silent: true });

  const startTour = useCallback(() => {
    setTourSession((current) => current + 1);
    setIsTourOpen(true);
  }, []);

  // Completion is stored on the backend so it is per-install, not per-browser.
  const finishTour = useCallback(() => {
    setIsTourOpen(false);
    mutate({ "settings-general-onboarding_completed": true });
  }, [mutate]);

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
