import { rawRender, screen } from "@/tests";
import userEvent from "@testing-library/user-event";
import { describe, it, vitest } from "vitest";
import ChipInput from "./ChipInput";

describe("ChipInput", () => {
  const existedValues = ["value_1", "value_2"];

  // TODO: Support default value
  it.skip("should works with default value", () => {
    rawRender(<ChipInput defaultValue={existedValues}></ChipInput>);

    existedValues.forEach((value) => {
      expect(screen.getByText(value)).toBeDefined();
    });
  });

  it("should works with value", () => {
    rawRender(<ChipInput value={existedValues}></ChipInput>);

    existedValues.forEach((value) => {
      expect(screen.getByText(value)).toBeDefined();
    });
  });

  it.skip("should allow user creates new value", async () => {
    const typedValue = "value_3";
    const mockedFn = vitest.fn((values: string[]) => {
      expect(values).toContain(typedValue);
    });

    rawRender(
      <ChipInput value={existedValues} onChange={mockedFn}></ChipInput>
    );

    const element = screen.getByRole("searchbox");

    await userEvent.type(element, typedValue);

    expect(element).toHaveValue(typedValue);

    const createBtn = screen.getByText(`Add "${typedValue}"`);

    await userEvent.click(createBtn);

    expect(mockedFn).toBeCalledTimes(1);
  });
});
