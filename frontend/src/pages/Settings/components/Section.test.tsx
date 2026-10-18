import { Text } from "@mantine/core";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { customRender, screen } from "@/tests";
import { Section } from "./Section";

describe("Settings section", () => {
  const header = "Section Header";

  it("should show header", () => {
    customRender(<Section header="Section Header"></Section>);

    expect(screen.getByText(header)).toBeDefined();
    expect(screen.getByRole("separator")).toBeDefined();
  });

  it("should show children", () => {
    const text = "Section Child";
    customRender(
      <Section header="Section Header">
        <Text>{text}</Text>
      </Section>,
    );

    expect(screen.getByText(header)).toBeDefined();
    expect(screen.getByText(text)).toBeDefined();
  });

  it("should work with hidden", () => {
    const text = "Section Child";
    customRender(
      <Section header="Section Header" hidden>
        <Text>{text}</Text>
      </Section>,
    );

    expect(screen.getByText(header)).not.toBeVisible();
    expect(screen.getByText(text)).not.toBeVisible();
  });

  it("renders a toggle button when collapsible", () => {
    customRender(
      <Section header="Collapsible" collapsible>
        <Text>child</Text>
      </Section>,
    );

    const button = screen.getByTestId("section-toggle-Collapsible");
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-expanded", "true");
  });

  it("renders collapsed when defaultCollapsed is set", () => {
    customRender(
      <Section header="Closed" collapsible defaultCollapsed>
        <Text>closed child</Text>
      </Section>,
    );

    const button = screen.getByTestId("section-toggle-Closed");
    expect(button).toHaveAttribute("aria-expanded", "false");
    // Content stays in the DOM (form state is preserved) but is hidden.
    expect(screen.getByText("closed child")).toBeInTheDocument();
    expect(screen.getByText("closed child")).not.toBeVisible();
  });

  it("toggles aria-expanded when the header is clicked", async () => {
    const user = userEvent.setup();

    customRender(
      <Section header="Clickable" collapsible>
        <Text>toggle child</Text>
      </Section>,
    );

    const button = screen.getByTestId("section-toggle-Clickable");
    const child = screen.getByText("toggle child");
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(child).toBeVisible();

    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(child).not.toBeVisible();

    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(child).toBeVisible();
  });

  it("renders the summary next to the header when provided", () => {
    customRender(
      <Section header="With Summary" summary="extra info">
        <Text>child</Text>
      </Section>,
    );

    expect(screen.getByText("extra info")).toBeInTheDocument();
  });
});
