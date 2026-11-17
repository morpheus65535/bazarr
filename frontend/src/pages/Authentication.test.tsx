import userEvent from "@testing-library/user-event";
import { describe, expect, it, type Mock, vi } from "vitest";
import { useSystem } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import { Environment } from "@/utilities";
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
    vi.restoreAllMocks();
    window.history.replaceState(null, "", "/");
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

  it("offers OIDC login without password fields and preserves the destination", () => {
    setupUseSystem();
    vi.spyOn(Environment, "authType", "get").mockReturnValue("oidc");
    window.history.replaceState(
      null,
      "",
      "/?returnTo=%2Fseries%3Fwanted%3Dtrue",
    );
    customRender(<Authentication />);

    const login = screen.getByRole("link", {
      name: "Sign in with OpenID Connect",
    });
    const url = new URL(login.getAttribute("href")!, window.location.origin);
    expect(url.pathname).toBe("/auth/oidc/login");
    expect(url.searchParams.get("returnTo")).toBe("/series?wanted=true");
    expect(screen.queryByLabelText(/Password/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Username/i)).not.toBeInTheDocument();
  });

  it("shows a safe access denial message and offers another login", () => {
    setupUseSystem();
    vi.spyOn(Environment, "authType", "get").mockReturnValue("oidc");
    window.history.replaceState(null, "", "/?oidcError=denied");
    customRender(<Authentication />);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Your account does not have access to Bazarr.",
    );
    expect(
      screen.getByRole("link", { name: "Sign in with OpenID Connect" }),
    ).toBeInTheDocument();
  });

  it("does not echo provider error content", () => {
    setupUseSystem();
    vi.spyOn(Environment, "authType", "get").mockReturnValue("oidc");
    window.history.replaceState(null, "", "/?oidcError=private-provider-error");
    customRender(<Authentication />);

    expect(screen.getByRole("alert")).toHaveTextContent("Unable to sign in.");
    expect(
      screen.queryByText("private-provider-error"),
    ).not.toBeInTheDocument();
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
