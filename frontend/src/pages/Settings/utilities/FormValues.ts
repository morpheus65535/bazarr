import { UseForm } from "@mantine/hooks/lib/use-form/use-form";
import { createContext, useCallback, useContext, useRef } from "react";

export const FormContext = createContext<UseForm<FormValues> | null>(null);

export function useFormValues() {
  const context = useContext(FormContext);

  if (context === null) {
    throw new Error("useFormValues must be used within a FormContext");
  }

  return context;
}

export function useStagedValues() {
  const form = useFormValues();
  return form.values.settings;
}

export function useFormActions() {
  const form = useFormValues();

  const formRef = useRef(form);
  formRef.current = form;

  const update = useCallback((object: LooseObject) => {
    formRef.current.setValues((values) => {
      const changes = { ...values.settings, ...object };
      return { ...values, settings: changes };
    });
  }, []);

  const setValue = useCallback((v: unknown, key: string) => {
    formRef.current.setValues((values) => {
      const changes = { ...values.settings, [key]: v };
      return { ...values, settings: changes };
    });
  }, []);

  return { update, setValue };
}

export type FormValues = {
  settings: LooseObject;
};
