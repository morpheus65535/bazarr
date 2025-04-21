import { customRender } from "@/tests";
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
});

describe("UI error page", () => {
  it("should disable error", () => {
    customRender(<UIError error={new Error("Test error")}></UIError>);
  });
});
