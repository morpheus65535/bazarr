import { FunctionComponent, useEffect, useMemo, useRef } from "react";
import { useLanguageProfiles, useSystemSettings } from "@/apis/hooks";
import { useEnabledStatus } from "@/apis/hooks/site";
import Tour, { TourStep } from "@/components/tour";
import { useOnboarding } from "@/contexts/Onboarding";
import { Environment } from "@/utilities";
import { useEnabledLanguages } from "@/utilities/languages";
import { onboardingSteps } from "./steps";

const autoStartDelayMs = 600;

/**
 * Renders the first-run tour and decides when to launch it automatically.
 * A fresh install starts it once; completion is persisted on the backend.
 */
const OnboardingTour: FunctionComponent = () => {
  const { isTourOpen, tourSession, startTour, finishTour } = useOnboarding();
  const { data: settings } = useSystemSettings();
  const { sonarr, radarr } = useEnabledStatus();
  const { data: profiles } = useLanguageProfiles();
  const { data: enabledLanguages } = useEnabledLanguages();
  const hasProfiles = (profiles?.length ?? 0) > 0;
  const hasProviders = (settings?.general?.enabled_providers?.length ?? 0) > 0;
  const hasLanguages = (enabledLanguages?.length ?? 0) > 0;
  const isSonarrConfigured = Boolean(
    sonarr && settings?.sonarr?.ip && settings?.sonarr?.apikey,
  );
  const isRadarrConfigured = Boolean(
    radarr && settings?.radarr?.ip && settings?.radarr?.apikey,
  );
  const hasCompleted = settings?.general?.onboarding_completed ?? false;
  const hasEvaluatedAutoStart = useRef(false);

  // Steps whose target lives in a hidden section are dropped when their library
  // is disabled; the rest skip themselves automatically once fulfilled.
  const steps = useMemo(() => {
    const visibilityById: Record<string, boolean> = {
      "sonarr-host": sonarr,
      "radarr-host": radarr,
      "path-mappings-sonarr": sonarr,
      "path-mappings-radarr": radarr,
    };
    const overridesById: Record<string, Partial<TourStep>> = {
      "sonarr-enable": { isFulfilled: sonarr },
      "radarr-enable": { isFulfilled: radarr, isBlocked: !sonarr && !radarr },
      "sonarr-host": { isFulfilled: isSonarrConfigured },
      "radarr-host": { isFulfilled: isRadarrConfigured },
      languages: { isFulfilled: hasLanguages },
      profiles: { isFulfilled: hasProfiles, isBlocked: !hasProfiles },
      providers: { isFulfilled: hasProviders, isBlocked: !hasProviders },
    };

    return onboardingSteps
      .filter((step) => {
        if (step.id.startsWith("library-movies")) {
          return radarr;
        }
        if (step.id.startsWith("library-series")) {
          return sonarr;
        }
        return visibilityById[step.id] ?? true;
      })
      .map((step) => ({ ...step, ...(overridesById[step.id] ?? {}) }));
  }, [
    sonarr,
    radarr,
    hasProfiles,
    hasProviders,
    hasLanguages,
    isSonarrConfigured,
    isRadarrConfigured,
  ]);

  useEffect(() => {
    if (hasEvaluatedAutoStart.current) {
      return;
    }
    if (settings === undefined) {
      return;
    }
    hasEvaluatedAutoStart.current = true;

    // Development switch to keep the tour visible for testing. Set
    // VITE_FORCE_ONBOARDING=true in .env.local and restart the dev server.
    if (Environment.isOnboardingForced) {
      const forcedTimer = window.setTimeout(startTour, autoStartDelayMs);
      return () => window.clearTimeout(forcedTimer);
    }

    if (hasCompleted || Environment.isConfigured) {
      return;
    }

    const timer = window.setTimeout(startTour, autoStartDelayMs);
    return () => window.clearTimeout(timer);
  }, [settings, hasCompleted, startTour]);

  return (
    <Tour
      key={tourSession}
      opened={isTourOpen}
      steps={steps}
      onFinish={finishTour}
    />
  );
};

export default OnboardingTour;
