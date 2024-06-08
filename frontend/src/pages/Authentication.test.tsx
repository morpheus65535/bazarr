import { describe, it } from "vitest";
import { render, screen } from "@/tests";
import Authentication from "./Authentication";

describe("Authentication", () => {
  it("should render without crash", () => {
    render(<Authentication></Authentication>);

    expect(screen.getByPlaceholderText("Username")).toBeDefined();
    expect(screen.getByPlaceholderText("Password")).toBeDefined();
    expect(screen.getByRole("button", { name: "Login" })).toBeDefined();
  });
});
