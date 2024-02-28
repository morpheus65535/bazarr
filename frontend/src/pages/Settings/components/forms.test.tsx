import { rawRender, RenderOptions, screen } from "@/tests";
import { useForm } from "@mantine/form";
import { FunctionComponent, PropsWithChildren, ReactElement } from "react";
import { describe, it } from "vitest";
import { FormContext, FormValues } from "../utilities/FormValues";
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

const formRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => rawRender(ui, { wrapper: FormSupport, ...options });

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
