import { act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, Mock, vi } from "vitest";
import { useSystemSettings } from "@/apis/hooks";
import OnboardingProvider from "@/contexts/OnboardingProvider";
import { customRender, screen } from "@/tests";
import OnboardingTour from "./OnboardingTour";

const environment = vi.hoisted(() => ({ isConfigured: false }));

vi.mock("@/utilities", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/utilities")>();
  return {
    ...actual,
    Environment: {
      ...actual.Environment,
      get isConfigured() {
        return environment.isConfigured;
      },
    },
  };
});

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystemSettings: vi.fn(),
  };
});

const mockedUseSystemSettings = useSystemSettings as Mock;

const renderTour = () =>
  customRender(
    <OnboardingProvider>
      <OnboardingTour />
    </OnboardingProvider>,
  );

const advanceAutoStart = async () => {
  await act(async () => {
    vi.advanceTimersByTime(1000);
  });
};

describe("OnboardingTour", () => {
  beforeEach(() => {
    environment.isConfigured = false;
    mockedUseSystemSettings.mockReturnValue({ data: { general: {} } });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("auto-starts the tour on a fresh install", async () => {
    vi.useFakeTimers();
    renderTour();

    await advanceAutoStart();

    expect(screen.getByTestId("onboarding-tour-title")).toBeInTheDocument();
  });

  it("does not auto-start on an already configured install", async () => {
    environment.isConfigured = true;
    vi.useFakeTimers();
    renderTour();

    await advanceAutoStart();

    expect(
      screen.queryByTestId("onboarding-tour-title"),
    ).not.toBeInTheDocument();
  });
});
