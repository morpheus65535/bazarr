import { faStickyNote } from "@fortawesome/free-regular-svg-icons";
import { fireEvent, render, RenderResult } from "@testing-library/react";
import { describe, it, vitest } from "vitest";
import Action from "./Action";

describe("Action button", () => {
  const testLabel = "Test Label";
  const testIcon = faStickyNote;

  const onClickFn = vitest.fn();

  let renderResult: RenderResult;
  beforeEach(() => {
    renderResult = render(
      <Action icon={testIcon} label={testLabel} onClick={onClickFn}></Action>
    );
  });

  it.concurrent("should be a button", () => {
    const element = renderResult.container.querySelector("button");
    expect(element).toBeDefined();
    expect(element?.type).toEqual("button");

    expect(element?.getAttribute("aria-label")).toEqual(testLabel);
  });

  it.concurrent("should call on-click event when clicked", () => {
    fireEvent(
      renderResult.container,
      new MouseEvent("click", { bubbles: true, cancelable: true })
    );
    expect(onClickFn).toHaveBeenCalled();
  });

  it.concurrent("should show icon", () => {
    const element = renderResult.container.querySelector("svg");
    expect(element).toBeDefined();

    expect(element?.getAttribute("data-prefix")).toEqual(testIcon.prefix);
    expect(element?.getAttribute("data-icon")).toEqual(testIcon.iconName);
  });
});
