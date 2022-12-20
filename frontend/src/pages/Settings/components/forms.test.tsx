import { useForm } from "@mantine/form";
import { render, screen } from "@testing-library/react";
import { FunctionComponent } from "react";
import { describe, it } from "vitest";
import { FormContext, FormValues } from "../utilities/FormValues";
import { Number, Text } from "./forms";

const FormSupport: FunctionComponent = ({ children }) => {
  const form = useForm<FormValues>({
    initialValues: {
      settings: {},
      hooks: {},
    },
  });
  return <FormContext.Provider value={form}>{children}</FormContext.Provider>;
};

describe("Settings form", () => {
  describe("number component", () => {
    it("should be able to render", () => {
      render(
        <FormSupport>
          <Number settingKey="test-numberValue"></Number>
        </FormSupport>
      );

      expect(screen.getByRole("textbox")).toBeDefined();
    });
  });

  describe("text component", () => {
    it("should be able to render", () => {
      render(
        <FormSupport>
          <Text settingKey="test-textValue"></Text>
        </FormSupport>
      );

      expect(screen.getByRole("textbox")).toBeDefined();
    });
  });
});
