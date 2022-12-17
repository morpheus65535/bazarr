import { render, screen } from "@testing-library/react";
import { QueryClientProvider } from "react-query";
import { describe, it } from "vitest";
import Authentication from "./Authentication";

import queryClient from "@/apis/queries";

describe("Authentication", () => {
  it("should render without crash", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Authentication></Authentication>
      </QueryClientProvider>
    );

    expect(screen.getByPlaceholderText("Username")).toBeDefined();
    expect(screen.getByPlaceholderText("Password")).toBeDefined();
    expect(screen.getByRole("button", { name: "Login" })).toBeDefined();
  });
});
