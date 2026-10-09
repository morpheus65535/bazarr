import { FunctionComponent, PropsWithChildren, ReactElement } from "react";
import { useForm } from "@mantine/form";
import { faSync } from "@fortawesome/free-solid-svg-icons";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { FormContext, FormValues } from "@/pages/Settings/utilities/FormValues";
import { SettingsProvider } from "@/pages/Settings/utilities/SettingsProvider";
import { customRender, screen } from "@/tests";
import {
  Action,
  Check,
  Chips,
  File,
  MultiSelector,
  Number,
  Password,
  Selector,
  Slider,
  Text,
} from "./forms";

const FormSupport: FunctionComponent<PropsWithChildren> = ({ children }) => {
  const form = useForm<FormValues>({
    initialValues: {
      settings: {
        "test-numberValue": 5,
        "test-textValue": "hello",
        "test-passwordValue": "secret",
        "test-check": true,
        "test-slider": 50,
        "test-chips": ["a"],
        "test-file": "/some/path/",
      },
      hooks: {},
    },
  });

  const settings = {
    test: {
      numberValue: 5,
      textValue: "hello",
      passwordValue: "secret",
      check: true,
      slider: 50,
      chips: ["a"],
      file: "/some/path/",
    },
  } as unknown as Settings;

  return (
    <SettingsProvider value={settings}>
      <FormContext.Provider value={form}>{children}</FormContext.Provider>
    </SettingsProvider>
  );
};

const formRender = (ui: ReactElement) =>
  customRender(<FormSupport>{ui}</FormSupport>);

describe("Settings form", () => {
  describe("number component", () => {
    it("should be able to render", () => {
      formRender(<Number settingKey="test-numberValue"></Number>);

      expect(screen.getByRole("textbox")).toBeDefined();
    });

    it("should reset to 0 when cleared", async () => {
      formRender(<Number settingKey="test-numberValue"></Number>);

      const input = screen.getByRole("textbox");
      await userEvent.clear(input);

      expect(input).toHaveValue("0");
    });

    it("should update the value when typed", async () => {
      formRender(<Number settingKey="test-numberValue"></Number>);

      const input = screen.getByRole("textbox");
      await userEvent.clear(input);
      await userEvent.type(input, "42");

      expect(input).toHaveValue("42");
    });

    it("should fall back to 0 when no value is set", () => {
      formRender(<Number settingKey="missing-number"></Number>);

      expect(screen.getByRole("textbox")).toHaveValue("0");
    });
  });

  describe("text component", () => {
    it("should be able to render", () => {
      formRender(<Text settingKey="test-textValue"></Text>);

      expect(screen.getByRole("textbox")).toBeDefined();
    });

    it("should update the value when typed", async () => {
      formRender(<Text settingKey="test-textValue"></Text>);

      const input = screen.getByRole("textbox");
      await userEvent.clear(input);
      await userEvent.type(input, "world");

      expect(input).toHaveValue("world");
    });

    it("should render with an empty value when no value is set", () => {
      formRender(<Text settingKey="missing-text"></Text>);

      expect(screen.getByRole("textbox")).toHaveValue("");
    });
  });

  describe("password component", () => {
    it("should be able to render", () => {
      formRender(<Password settingKey="test-passwordValue"></Password>);

      expect(screen.getByDisplayValue("secret")).toBeDefined();
    });

    it("should update the value when typed", async () => {
      formRender(<Password settingKey="test-passwordValue"></Password>);

      const input = screen.getByDisplayValue("secret");
      await userEvent.clear(input);
      await userEvent.type(input, "new-secret");

      expect(input).toHaveValue("new-secret");
    });

    it("should render with an empty value when no value is set", () => {
      formRender(<Password settingKey="missing-password"></Password>);

      expect(screen.getByDisplayValue("")).toHaveValue("");
    });
  });

  describe("check component", () => {
    it("should be able to render", () => {
      formRender(<Check settingKey="test-check" label="Enable"></Check>);

      expect(screen.getByRole("switch")).toBeDefined();
    });

    it("should toggle when clicked", async () => {
      formRender(<Check settingKey="test-check" label="Enable"></Check>);

      const input = screen.getByRole("switch");
      await userEvent.click(input);

      expect(input).not.toBeChecked();
    });

    it("should toggle from false when no value is set", async () => {
      formRender(<Check settingKey="missing-check" label="Enable"></Check>);

      const input = screen.getByRole("switch");
      expect(input).not.toBeChecked();

      await userEvent.click(input);

      expect(input).toBeChecked();
    });
  });

  describe("selector component", () => {
    it("should be able to render", () => {
      formRender(
        <Selector
          settingKey="test-textValue"
          options={[
            { value: "hello", label: "Hello" },
            { value: "world", label: "World" },
          ]}
        ></Selector>,
      );

      expect(screen.getByTestId("input-selector")).toBeDefined();
    });
  });

  describe("multi-selector component", () => {
    it("should be able to render", () => {
      formRender(
        <MultiSelector
          settingKey="test-chips"
          options={[
            { value: "a", label: "A" },
            { value: "b", label: "B" },
          ]}
          data-testid="input-multi-selector"
        ></MultiSelector>,
      );

      expect(screen.getByTestId("input-multi-selector")).toBeDefined();
    });

    it("should render without a value", () => {
      formRender(
        <MultiSelector
          settingKey="missing-chips"
          options={[
            { value: "a", label: "A" },
            { value: "b", label: "B" },
          ]}
          data-testid="input-multi-selector"
        ></MultiSelector>,
      );

      expect(screen.getByTestId("input-multi-selector")).toBeDefined();
    });
  });

  describe("slider component", () => {
    it("should be able to render", () => {
      formRender(<Slider settingKey="test-slider" min={0} max={100}></Slider>);

      expect(screen.getByRole("slider")).toBeDefined();
    });

    it("should fall back to 0 when no value is set", () => {
      formRender(
        <Slider settingKey="missing-slider" min={0} max={100}></Slider>,
      );

      expect(screen.getByRole("slider")).toHaveAttribute("aria-valuenow", "0");
    });
  });

  describe("chips component", () => {
    it("should be able to render", () => {
      formRender(<Chips settingKey="test-chips" label="Chips"></Chips>);

      expect(screen.getByText("a")).toBeDefined();
    });

    it("should remove a chip when the remove button is clicked", async () => {
      const sanitizeFn = vitest.fn().mockReturnValue(undefined);
      formRender(
        <Chips
          settingKey="test-chips"
          label="Chips"
          sanitizeFn={sanitizeFn}
        ></Chips>,
      );

      const input = screen.getByRole("combobox", { name: "Chips" });
      await userEvent.click(input);
      await userEvent.keyboard("{Backspace}");

      expect(screen.queryByText("a")).not.toBeInTheDocument();
      expect(sanitizeFn).toHaveBeenCalledWith([]);
    });

    it("should render without a value", () => {
      formRender(<Chips settingKey="missing-chips" label="Chips"></Chips>);

      expect(screen.getByRole("combobox")).toBeDefined();
    });

    it("should update with sanitized values", async () => {
      const sanitizeFn = vitest.fn().mockReturnValue(["b"]);
      formRender(
        <Chips
          settingKey="test-chips"
          label="Chips"
          sanitizeFn={sanitizeFn}
        ></Chips>,
      );

      const input = screen.getByRole("combobox", { name: "Chips" });
      await userEvent.click(input);
      await userEvent.keyboard("{Backspace}");

      expect(sanitizeFn).toHaveBeenCalledWith([]);
    });
  });

  describe("action component", () => {
    it("should be able to render and click", async () => {
      const onClick = vitest.fn();
      formRender(
        <Action
          settingKey="test-textValue"
          icon={faSync}
          label="Sync"
          onClick={onClick}
        ></Action>,
      );

      await userEvent.click(screen.getByRole("button", { name: "Sync" }));

      expect(onClick).toHaveBeenCalled();
    });

    it("should handle clicks without an onClick handler", async () => {
      formRender(
        <Action
          settingKey="test-textValue"
          icon={faSync}
          label="Sync"
        ></Action>,
      );

      await userEvent.click(screen.getByRole("button", { name: "Sync" }));

      expect(screen.getByRole("button", { name: "Sync" })).toBeDefined();
    });

    it("should pass undefined as the current value when none is set", async () => {
      const onClick = vitest.fn();
      formRender(
        <Action
          settingKey="missing-text"
          icon={faSync}
          label="Sync"
          onClick={onClick}
        ></Action>,
      );

      await userEvent.click(screen.getByRole("button", { name: "Sync" }));

      expect(onClick).toHaveBeenCalledWith(expect.any(Function), undefined);
    });
  });

  describe("file component", () => {
    it("should be able to render", () => {
      formRender(<File settingKey="test-file" type="bazarr"></File>);

      expect(screen.getByRole("combobox")).toHaveValue("/some/path/");
    });

    it("should render without a value", () => {
      formRender(<File settingKey="missing-file" type="bazarr"></File>);

      expect(screen.getByRole("combobox")).toBeDefined();
    });
  });
});
