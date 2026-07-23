import { customRender, screen } from "@/tests";
import CriticalError from "./CriticalError";
import NotFound from "./NotFound";
import UIError from "./UIError";

describe("Not found page", () => {
  it("should display message", () => {
    customRender(<NotFound />);
  });
});

describe("Critical error page", () => {
  it("should disable error", () => {
    customRender(<CriticalError message="Test error"></CriticalError>);
  });

  it("should render message text with correct color style", () => {
    customRender(<CriticalError message="Test error"></CriticalError>);
    const textElement = screen.getByText("Test error");

    const computedColor = window.getComputedStyle(textElement).color;
    expect(computedColor).toMatch(
      /(rgb\(250, 82, 82\)|var\(--mantine-color-danger-text\))/,
    );
  });
});

describe("UI error page", () => {
  it("should disable error", () => {
    customRender(<UIError error={new Error("Test error")}></UIError>);
  });
});
