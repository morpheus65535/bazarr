import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import ErrorBoundary from "./ErrorBoundary";

const ThrowError: React.FC = () => {
  throw new Error("boom");
};

describe("ErrorBoundary", () => {
  it("renders its children when no error is thrown", () => {
    customRender(
      <ErrorBoundary>
        <div>Child</div>
      </ErrorBoundary>,
    );

    expect(screen.getByText("Child")).toBeInTheDocument();
  });

  it("renders the error UI when a child throws", () => {
    const consoleError = vitest
      .spyOn(console, "error")
      .mockImplementation(() => undefined);

    customRender(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Oops! UI is crashed!")).toBeInTheDocument();

    consoleError.mockRestore();
  });
});
