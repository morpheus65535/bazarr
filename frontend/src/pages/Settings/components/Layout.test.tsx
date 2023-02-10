import queryClient from "@/apis/queries";
import { Text } from "@mantine/core";
import { render, screen } from "@testing-library/react";
import { QueryClientProvider } from "react-query";
import { BrowserRouter } from "react-router-dom";
import { describe, it } from "vitest";
import Layout from "./Layout";

const renderLayout = () => {
  render(
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <Layout name="Test Settings">
          <Text>Value</Text>
        </Layout>
      </QueryClientProvider>
    </BrowserRouter>
  );
};

describe("Settings layout", () => {
  it.concurrent("should be able to render without issues", () => {
    renderLayout();
  });

  it.concurrent("save button should be disabled by default", () => {
    renderLayout();

    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });
});
