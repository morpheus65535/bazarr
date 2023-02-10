import { render } from "@/tests";
import CriticalError from "./CriticalError";
import NotFound from "./NotFound";
import UIError from "./UIError";

describe("Not found page", () => {
  it("should display message", () => {
    render(<NotFound />);
  });
});

describe("Critical error page", () => {
  it("should disable error", () => {
    render(<CriticalError message="Test error"></CriticalError>);
  });
});

describe("UI error page", () => {
  it("should disable error", () => {
    render(<UIError error={new Error("Test error")}></UIError>);
  });
});
