import { ReactNode } from "react";
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
    <>
      <button
        type="button"
        data-testid="stage-button"
        onClick={() => setValue("staged-value", "settings-general-theme")}
      >
        Stage
      </button>
      <button
        type="button"
        data-testid="stage-newer-button"
        onClick={() => setValue("newer-value", "settings-general-theme")}
      >
        Stage newer
      </button>
    </>
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

const renderLayout = (
  children: ReactNode,
  settings?: Settings,
  mutation = vitest.fn(),
) => {
  const mutate = setupMocks(mutation, settings);
  return {
    mutate,
    ...customRender(<Layout name="Test">{children}</Layout>),
  };
};

const renderLayoutModal = (
  children: ReactNode,
  callbackModal = vitest.fn(),
  settings?: Settings,
  mutation = vitest.fn(),
) => {
  const mutate = setupMocks(mutation, settings);
  return {
    mutate,
    callbackModal,
    ...customRender(
      <LayoutModal callbackModal={callbackModal}>{children}</LayoutModal>,
    ),
  };
};

const succeedMutation = (mutate: Mock) => {
  const options = mutate.mock.calls[0][1] as { onSuccess?: () => void };
  options.onSuccess?.();
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

  it("disables Discard when there are no staged changes", () => {
    renderLayout(<Stager />);

    expect(screen.getByRole("button", { name: /Discard/ })).toBeDisabled();
  });

  it("clears staged changes when Discard is clicked", async () => {
    renderLayout(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));
    expect(screen.getByRole("button", { name: /Save/ })).toBeEnabled();

    await userEvent.click(screen.getByRole("button", { name: /Discard/ }));

    expect(screen.getByRole("button", { name: /Save/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Discard/ })).toBeDisabled();
  });

  it("submits staged settings when Save is clicked", async () => {
    const { mutate } = renderLayout(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalledWith(
      {
        "settings-general-theme": "staged-value",
      },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });

  it("preserves staged changes across unrelated settings refetches", async () => {
    const { rerender } = renderLayout(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));

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

    expect(screen.getByRole("button", { name: /Save/ })).toBeEnabled();
  });

  it("clears unchanged values after their save refetch completes", async () => {
    const { mutate, rerender } = renderLayout(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));
    succeedMutation(mutate);

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

  it("preserves edits made after a save started", async () => {
    const { mutate, rerender } = renderLayout(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));
    await userEvent.click(screen.getByTestId("stage-newer-button"));
    succeedMutation(mutate);

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

    expect(screen.getByRole("button", { name: /Save/ })).toBeEnabled();
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));
    expect(mutate).toHaveBeenLastCalledWith(
      {
        "settings-general-theme": "newer-value",
      },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
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

  it("keeps the modal open until the save succeeds", async () => {
    const { mutate, callbackModal } = renderLayoutModal(<Stager />);

    await userEvent.click(screen.getByTestId("stage-button"));
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalled();
    expect(callbackModal).not.toHaveBeenCalled();
  });

  it("submits staged settings and closes the modal on success", async () => {
    const mutation = vitest.fn(
      (
        _settings: Record<string, unknown>,
        options?: { onSuccess?: () => void },
      ) => options?.onSuccess?.(),
    );
    const { mutate, callbackModal } = renderLayoutModal(
      <Stager />,
      vitest.fn(),
      undefined,
      mutation,
    );

    await userEvent.click(screen.getByTestId("stage-button"));
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalledWith(
      {
        "settings-general-theme": "staged-value",
      },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
    expect(callbackModal).toHaveBeenCalledWith(true);
  });
});
