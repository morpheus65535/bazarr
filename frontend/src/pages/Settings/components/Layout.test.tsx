import { Text } from "@mantine/core";
import { describe, it } from "vitest";
import { customRender, screen } from "@/tests";
import Layout from "./Layout";

describe("Settings layout", () => {
  it.concurrent("should be able to render without issues", () => {
    customRender(
      <Layout name="Test Settings">
        <Text>Value</Text>
      </Layout>,
    );
  });

  it.concurrent("save button should be disabled by default", () => {
    customRender(
      <Layout name="Test Settings">
        <Text>Value</Text>
      </Layout>,
    );

    expect(screen.getAllByRole("button", { name: "Save" })[0]).toBeDisabled();
  });
});
