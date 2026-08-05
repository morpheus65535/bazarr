import { ReactNode } from "react";
import { waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";
import { customRender, screen } from "@/tests";
import Layout from "./Layout";
import LayoutModal from "./LayoutModal";

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
  };
});

const mockedUseSystemSettings = useSystemSettings as Mock;
const mockedUseSettingsMutation = useSettingsMutation as Mock;

const defaultSettings = {
  general: { theme: "auto" },
} as unknown as Settings;

const Stager = () => {
  const { setValue } = useFormActions();
  return (
    <button
      type="button"
      data-testid="stage-button"
      onClick={() => setValue("staged-value", "settings-general-theme")}
    >
      Stage
    </button>
  );
};

const setupMocks = (
  mutate = vitest.fn(),
  settings: Settings = defaultSettings,
) => {
  mockedUseSystemSettings.mockReturnValue({
    data: settings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate,
    isPending: false,
  });
  return mutate;
};

const renderLayout = (children: ReactNode, settings?: Settings) => {
  const mutate = setupMocks(vitest.fn(), settings);
  return {
    mutate,
    ...customRender(<Layout name="Test">{children}</Layout>),
  };
};

const renderLayoutModal = (
  children: ReactNode,
  callbackModal = vitest.fn(),
  settings?: Settings,
) => {
  const mutate = setupMocks(vitest.fn(), settings);
  return {
    mutate,
    callbackModal,
    ...customRender(
      <LayoutModal callbackModal={callbackModal}>{children}</LayoutModal>,
    ),
  };
};

describe("Settings Layout", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("renders children and disables Save when there are no staged changes", () => {
    renderLayout(<Stager />);

    expect(screen.getByTestId("stage-button")).toBeDefined();
    expect(screen.getByRole("button", { name: /Save/ })).toBeDisabled();
  });

  it("enables Save after a child stages a value", async () => {
    renderLayout(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));

    expect(screen.getByRole("button", { name: /Save/ })).toBeEnabled();
  });

  it("submits staged settings when Save is clicked", async () => {
    const { mutate } = renderLayout(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalledWith({
      "settings-general-theme": "staged-value",
    });
  });

  it("resets staged changes when refetching finishes", async () => {
    const { rerender } = renderLayout(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));
    expect(screen.getByRole("button", { name: /Save/ })).toBeEnabled();

    mockedUseSystemSettings.mockReturnValue({
      data: defaultSettings,
      isLoading: false,
      isRefetching: true,
    });
    rerender(
      <Layout name="Test">
        <Stager />
      </Layout>,
    );

    mockedUseSystemSettings.mockReturnValue({
      data: defaultSettings,
      isLoading: false,
      isRefetching: false,
    });
    rerender(
      <Layout name="Test">
        <Stager />
      </Layout>,
    );

    expect(screen.getByRole("button", { name: /Save/ })).toBeDisabled();
  });
});

describe("Settings LayoutModal", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("renders Save and Close buttons", () => {
    renderLayoutModal(<Stager />);

    expect(screen.getByRole("button", { name: /Save/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Close" })).toBeEnabled();
  });

  it("calls the modal callback when Close is clicked", async () => {
    const { callbackModal } = renderLayoutModal(<Stager />);

    await userEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(callbackModal).toHaveBeenCalledWith(true);
  });

  it("submits staged settings and closes the modal", async () => {
    const { mutate, callbackModal } = renderLayoutModal(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalledWith({
      "settings-general-theme": "staged-value",
    });

    await waitFor(() => expect(callbackModal).toHaveBeenCalledWith(true), {
      timeout: 1000,
    });
  });
});
