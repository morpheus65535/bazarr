import { FunctionComponent, PropsWithChildren, ReactElement } from "react";
import { useForm } from "@mantine/form";
import { describe, it } from "vitest";
import { FormContext, FormValues } from "@/pages/Settings/utilities/FormValues";
import { customRender, screen } from "@/tests";
import { Number, Text } from "./forms";

const FormSupport: FunctionComponent<PropsWithChildren> = ({ children }) => {
  const form = useForm<FormValues>({
    initialValues: {
      settings: {},
      hooks: {},
    },
  });
  return <FormContext.Provider value={form}>{children}</FormContext.Provider>;
};

const formRender = (ui: ReactElement) =>
  customRender(<FormSupport>{ui}</FormSupport>);

describe("Settings form", () => {
  describe("number component", () => {
    it("should be able to render", () => {
      formRender(<Number settingKey="test-numberValue"></Number>);

      expect(screen.getByRole("textbox")).toBeDefined();
    });
  });

  describe("text component", () => {
    it("should be able to render", () => {
      formRender(<Text settingKey="test-textValue"></Text>);

      expect(screen.getByRole("textbox")).toBeDefined();
    });
  });
});
