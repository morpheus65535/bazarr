import { describe, it } from "vitest";
import { render } from "@/tests";
import App from ".";

describe("App", () => {
  it("should render without crash", () => {
    render(<App />);
  });
});
