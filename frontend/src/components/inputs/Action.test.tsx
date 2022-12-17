import { faStickyNote } from "@fortawesome/free-regular-svg-icons";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, vitest } from "vitest";
import Action from "./Action";

const testLabel = "Test Label";
const testIcon = faStickyNote;

describe("Action button", () => {
  const onClickFn = vitest.fn();

  beforeEach(() => {
    render(
      <Action icon={testIcon} label={testLabel} onClick={onClickFn}></Action>
    );
  });

  it("should be a button", () => {
    const element = screen.getByRole("button", { name: testLabel });

    expect(element.getAttribute("type")).toEqual("button");
    expect(element.getAttribute("aria-label")).toEqual(testLabel);
  });

  it("should show icon", () => {
    // TODO: use getBy...
    const element = screen.getByRole("button").querySelector("svg");

    expect(element?.getAttribute("data-prefix")).toEqual(testIcon.prefix);
    expect(element?.getAttribute("data-icon")).toEqual(testIcon.iconName);
  });

  it("should call on-click event when clicked", async () => {
    await userEvent.click(screen.getByRole("button", { name: testLabel }));

    expect(onClickFn).toHaveBeenCalled();
  });
});
