import { render } from "@/tests";
import { describe, it } from "vitest";
import App from ".";

describe("App", () => {
  it("should render without crash", () => {
    render(<App />);
  });
});
