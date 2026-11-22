import { ReactNode } from "react";
import { act, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw/http";
import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";
import { customRender, screen } from "@/tests";
import server from "@/tests/mocks/node";
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

const SettingStager = ({
  settingKey,
  settingValue,
}: {
  settingKey: string;
  settingValue: unknown;
}) => {
  const { setValue } = useFormActions();
  return (
    <button
      type="button"
      data-testid="stage-setting-button"
      onClick={() => setValue(settingValue, settingKey)}
    >
      Stage setting
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

const Submitter = () => {
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
      <button type="submit" data-testid="submit-button">
        Submit
      </button>
    </>
  );
};

const renderEditorLayout = (props: {
  isEditorActive?: boolean;
  isDraftDirty?: boolean;
}) => {
  const mutate = setupMocks();
  return {
    mutate,
    ...customRender(
      <Layout name="Test" {...props}>
        <Submitter />
      </Layout>,
    ),
  };
};

const succeedMutation = (mutate: Mock, submissionIndex = 0) => {
  const options = mutate.mock.calls[submissionIndex][1] as {
    onSuccess?: () => void;
  };
  act(() => {
    options.onSuccess?.();
  });
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

describe("Settings Layout authentication changes", () => {
  const reload = vi.fn(() =>
    window.dispatchEvent(new Event("beforeunload", { cancelable: true })),
  );

  beforeEach(() => {
    vitest.clearAllMocks();
    vi.spyOn(window.location, "reload").mockImplementation(reload);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it.each([
    { settingKey: "settings-auth-type", settingValue: "form" },
    { settingKey: "settings-auth-type", settingValue: "basic" },
    { settingKey: "settings-auth-type", settingValue: null },
    { settingKey: "settings-auth-username", settingValue: "new-username" },
    { settingKey: "settings-auth-password", settingValue: "new-password" },
  ])(
    "reloads without an unsaved changes prompt after saving $settingKey as $settingValue",
    async ({ settingKey, settingValue }) => {
      const { mutate } = renderLayout(
        <SettingStager settingKey={settingKey} settingValue={settingValue} />,
      );

      await userEvent.click(screen.getByTestId("stage-setting-button"));
      expect(
        window.dispatchEvent(new Event("beforeunload", { cancelable: true })),
      ).toBe(false);

      await userEvent.click(screen.getByRole("button", { name: /Save/ }));
      expect(reload).not.toHaveBeenCalled();

      succeedMutation(mutate);

      expect(screen.getByRole("button", { name: /Save/ })).toBeDisabled();
      expect(reload).toHaveBeenCalledTimes(1);
      expect(reload).toHaveReturnedWith(true);
    },
  );

  it.each(["settings-general-theme", "settings-auth-apikey"])(
    "does not reload after saving %s",
    async (settingKey) => {
      const { mutate } = renderLayout(
        <SettingStager settingKey={settingKey} settingValue="new-value" />,
      );

      await userEvent.click(screen.getByTestId("stage-setting-button"));
      await userEvent.click(screen.getByRole("button", { name: /Save/ }));
      succeedMutation(mutate);

      expect(screen.getByRole("button", { name: /Save/ })).toBeDisabled();
      expect(reload).not.toHaveBeenCalled();
    },
  );

  it("keeps authentication edits after a failed save and reloads after a successful retry", async () => {
    const { useSettingsMutation: useActualSettingsMutation } =
      await vi.importActual<typeof import("@/apis/hooks")>("@/apis/hooks");
    setupMocks();
    mockedUseSettingsMutation.mockImplementation(useActualSettingsMutation);
    server.use(
      http.post("/api/system/settings", () => {
        return new HttpResponse("Settings rejected", { status: 500 });
      }),
    );
    customRender(
      <Layout name="Test">
        <SettingStager
          settingKey="settings-auth-username"
          settingValue="new-username"
        />
      </Layout>,
    );

    await userEvent.click(screen.getByTestId("stage-setting-button"));
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));
    await screen.findByText("Save failed");

    expect(screen.getByRole("button", { name: /Save/ })).toBeEnabled();
    expect(reload).not.toHaveBeenCalled();
    expect(
      window.dispatchEvent(new Event("beforeunload", { cancelable: true })),
    ).toBe(false);

    server.use(
      http.post("/api/system/settings", () => {
        return new HttpResponse(null, { status: 204 });
      }),
    );
    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    await waitFor(() => expect(reload).toHaveBeenCalledTimes(1));
    expect(reload).toHaveReturnedWith(true);
  });

  it.each(["Save", "Discard"])(
    "protects edits made during an authentication save until %s",
    async (action) => {
      const { mutate } = renderLayout(
        <>
          <SettingStager
            settingKey="settings-auth-username"
            settingValue="new-username"
          />
          <Stager />
        </>,
      );

      await userEvent.click(screen.getByTestId("stage-setting-button"));
      await userEvent.click(screen.getByRole("button", { name: /Save/ }));
      await userEvent.click(screen.getByTestId("stage-button"));
      succeedMutation(mutate);

      expect(reload).not.toHaveBeenCalled();
      expect(screen.getByRole("button", { name: /Save/ })).toBeEnabled();
      expect(
        window.dispatchEvent(new Event("beforeunload", { cancelable: true })),
      ).toBe(false);

      await userEvent.click(
        screen.getByRole("button", { name: new RegExp(action) }),
      );

      if (action === "Save") {
        expect(reload).not.toHaveBeenCalled();
        expect(mutate).toHaveBeenLastCalledWith(
          { "settings-general-theme": "staged-value" },
          expect.objectContaining({ onSuccess: expect.any(Function) }),
        );
        succeedMutation(mutate, 1);
      }

      expect(reload).toHaveBeenCalledTimes(1);
      expect(reload).toHaveReturnedWith(true);
    },
  );
});

describe("Settings Layout with an active editor", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("disables Save and Discard while an editor is active", () => {
    renderEditorLayout({ isEditorActive: true });

    expect(screen.getByRole("button", { name: /Save/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Discard/ })).toBeDisabled();
  });

  it("does not submit staged settings while an editor is active", async () => {
    const { mutate } = renderEditorLayout({ isEditorActive: true });

    await userEvent.click(screen.getByTestId("stage-button"));
    await userEvent.click(screen.getByTestId("submit-button"));

    expect(mutate).not.toHaveBeenCalled();
  });

  it("keeps the default behaviour when the editor props are absent", async () => {
    const { mutate } = renderEditorLayout({});

    await userEvent.click(screen.getByTestId("stage-button"));

    expect(screen.getByRole("button", { name: /Save/ })).toBeEnabled();

    await userEvent.click(screen.getByTestId("submit-button"));

    expect(mutate).toHaveBeenCalled();
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
