import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import ChipInput from "./ChipInput";

describe("ChipInput", () => {
  const existedValues = ["value_1", "value_2"];

  it("should works with value", () => {
    customRender(<ChipInput value={existedValues}></ChipInput>);

    existedValues.forEach((value) => {
      expect(screen.getByText(value)).toBeDefined();
    });
  });

  it("should allow user creates new value", async () => {
    const typedValue = "value_3";
    const mockedFn = vitest.fn((values: string[]) => {
      expect(values).toContain(typedValue);
    });

    customRender(
      <ChipInput value={existedValues} onChange={mockedFn}></ChipInput>,
    );

    const input = screen.getByRole("combobox");

    await userEvent.type(input, `${typedValue}{enter}`);

    expect(mockedFn).toHaveBeenCalledTimes(1);
  });
});
