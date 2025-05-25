import userEvent from "@testing-library/user-event";
import { describe, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import { Selector, SelectorOption } from "./Selector";

const selectorName = "Test Selections";
const testOptions: SelectorOption<string>[] = [
  {
    label: "Option 1",
    value: "option_1",
  },
  {
    label: "Option 2",
    value: "option_2",
  },
];

describe("Selector", () => {
  describe("options", () => {
    it("should work with the SelectorOption", () => {
      customRender(
        <Selector name={selectorName} options={testOptions}></Selector>,
      );

      testOptions.forEach((o) => {
        expect(screen.getByText(o.label)).toBeDefined();
      });
    });

    it("should display when clicked", async () => {
      customRender(
        <Selector name={selectorName} options={testOptions}></Selector>,
      );

      const element = screen.getByTestId("input-selector");

      await userEvent.click(element);

      for (const option of testOptions) {
        expect(screen.getByText(option.label)).toBeInTheDocument();
      }

      testOptions.forEach((option) => {
        expect(screen.getByText(option.label)).toBeDefined();
      });
    });

    it("shouldn't show default value", async () => {
      const option = testOptions[0];
      customRender(
        <Selector
          name={selectorName}
          options={testOptions}
          defaultValue={option.value}
        ></Selector>,
      );

      expect(screen.getByDisplayValue(option.label)).toBeDefined();
    });

    it("shouldn't show value", async () => {
      const option = testOptions[0];
      customRender(
        <Selector
          name={selectorName}
          options={testOptions}
          value={option.value}
        ></Selector>,
      );

      expect(screen.getByDisplayValue(option.label)).toBeDefined();
    });
  });

  describe("event", () => {
    it("should fire on-change event when clicking option", async () => {
      const clickedOption = testOptions[0];
      const mockedFn = vitest.fn((value: string | null) => {
        expect(value).toEqual(clickedOption.value);
      });
      customRender(
        <Selector
          name={selectorName}
          options={testOptions}
          onChange={mockedFn}
        ></Selector>,
      );

      const element = screen.getByTestId("input-selector");

      await userEvent.click(element);

      await userEvent.click(screen.getByText(clickedOption.label));

      expect(mockedFn).toHaveBeenCalled();
    });
  });

  describe("with object options", () => {
    const objectOptions: SelectorOption<{ name: string }>[] = [
      {
        label: "Option 1",
        value: {
          name: "option_1",
        },
      },
      {
        label: "Option 2",
        value: {
          name: "option_2",
        },
      },
    ];

    it("should fire on-change event with payload", async () => {
      const clickedOption = objectOptions[0];

      const mockedFn = vitest.fn((value: { name: string } | null) => {
        expect(value).toEqual(clickedOption.value);
      });
      customRender(
        <Selector
          name={selectorName}
          options={objectOptions}
          onChange={mockedFn}
          getkey={(v) => v.name}
        ></Selector>,
      );

      const element = screen.getByTestId("input-selector");

      await userEvent.click(element);

      await userEvent.click(screen.getByText(clickedOption.label));

      expect(mockedFn).toHaveBeenCalled();
    });
  });

  describe("placeholder", () => {
    it("should show when no selection", () => {
      const placeholder = "Empty Selection";
      customRender(
        <Selector
          name={selectorName}
          options={testOptions}
          placeholder={placeholder}
        ></Selector>,
      );

      expect(screen.getByPlaceholderText(placeholder)).toBeDefined();
    });
  });
});
