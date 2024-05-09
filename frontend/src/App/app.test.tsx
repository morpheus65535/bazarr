import { render } from "@/tests";
import App from ".";

import { describe, it } from "vitest";

describe("App", () => {
  it("should render without crash", () => {
    render(<App />);
  });
});
