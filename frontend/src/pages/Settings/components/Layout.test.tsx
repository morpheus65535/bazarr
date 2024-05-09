import { Text } from "@mantine/core";
import { render, screen } from "@/tests";
import Layout from "./Layout";

import { describe, it } from "vitest";

describe("Settings layout", () => {
  it.concurrent("should be able to render without issues", () => {
    render(
      <Layout name="Test Settings">
        <Text>Value</Text>
      </Layout>,
    );
  });

  it.concurrent("save button should be disabled by default", () => {
    render(
      <Layout name="Test Settings">
        <Text>Value</Text>
      </Layout>,
    );

    expect(screen.getAllByRole("button", { name: "Save" })[0]).toBeDisabled();
  });
});
