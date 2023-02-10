import { rawRender, screen } from "@/tests";
import { Text } from "@mantine/core";
import { describe, it } from "vitest";
import { Section } from "./Section";

describe("Settings section", () => {
  const header = "Section Header";
  it("should show header", () => {
    rawRender(<Section header="Section Header"></Section>);

    expect(screen.getByText(header)).toBeDefined();
    expect(screen.getByRole("separator")).toBeDefined();
  });

  it("should show children", () => {
    const text = "Section Child";
    rawRender(
      <Section header="Section Header">
        <Text>{text}</Text>
      </Section>
    );

    expect(screen.getByText(header)).toBeDefined();
    expect(screen.getByText(text)).toBeDefined();
  });

  it("should work with hidden", () => {
    const text = "Section Child";
    rawRender(
      <Section header="Section Header" hidden>
        <Text>{text}</Text>
      </Section>
    );

    expect(screen.getByText(header)).not.toBeVisible();
    expect(screen.getByText(text)).not.toBeVisible();
  });
});
