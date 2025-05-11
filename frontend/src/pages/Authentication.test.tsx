import { describe, it } from "vitest";
import { customRender, screen } from "@/tests";
import Authentication from "./Authentication";

describe("Authentication", () => {
  it("should render without crash", () => {
    customRender(<Authentication></Authentication>);

    expect(screen.getByPlaceholderText("Username")).toBeDefined();
    expect(screen.getByPlaceholderText("Password")).toBeDefined();
    expect(screen.getByRole("button", { name: "Login" })).toBeDefined();
  });
});
