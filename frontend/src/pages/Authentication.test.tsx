import userEvent from "@testing-library/user-event";
import { describe, expect, it, type Mock, vi } from "vitest";
import { useSystem } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import Authentication from "./Authentication";

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystem: vi.fn(),
  };
});

const mockLogin = vi.fn();

const setupUseSystem = (isLoggingIn = false) => {
  const mocked = useSystem as Mock;
  mocked.mockReturnValue({
    login: mockLogin,
    logout: vi.fn(),
    shutdown: vi.fn(),
    restart: vi.fn(),
    isMutating: isLoggingIn,
    isLoggingIn,
  });
};

describe("Authentication", () => {
  beforeEach(() => {
    mockLogin.mockClear();
  });

  it("renders login form", () => {
    setupUseSystem();
    customRender(<Authentication />);

    expect(screen.getByRole("heading", { name: "Bazarr" })).toBeInTheDocument();
    expect(
      screen.getByLabelText(/Username/i, { selector: "input" }),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(/Password/i, { selector: "input" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Login" })).toBeInTheDocument();
  });

  it("submits credentials", async () => {
    setupUseSystem();
    customRender(<Authentication />);

    const user = userEvent.setup();
    await user.type(
      screen.getByLabelText(/Username/i, { selector: "input" }),
      "admin",
    );
    await user.type(
      screen.getByLabelText(/Password/i, { selector: "input" }),
      "secret",
    );
    await user.click(screen.getByRole("button", { name: "Login" }));

    expect(mockLogin).toHaveBeenCalledWith(
      { username: "admin", password: "secret" },
      expect.any(Object),
    );
  });

  it("disables form while logging in", () => {
    setupUseSystem(true);
    customRender(<Authentication />);

    expect(
      screen.getByLabelText(/Username/i, { selector: "input" }),
    ).toBeDisabled();
    expect(
      screen.getByLabelText(/Password/i, { selector: "input" }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Login" })).toBeDisabled();
  });

  it("shows inline error when login fails", async () => {
    mockLogin.mockImplementation((_, { onError }) => {
      onError(new Error("Authentication failed"));
    });
    setupUseSystem();

    customRender(<Authentication />);

    const user = userEvent.setup();
    await user.type(
      screen.getByLabelText(/Username/i, { selector: "input" }),
      "admin",
    );
    await user.type(
      screen.getByLabelText(/Password/i, { selector: "input" }),
      "secret",
    );
    await user.click(screen.getByRole("button", { name: "Login" }));

    expect(
      await screen.findByText("Authentication failed"),
    ).toBeInTheDocument();
  });
});
