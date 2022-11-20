import { LOG } from "@/utilities/console";
import type { UseFormReturnType } from "@mantine/form";
import { createContext, useCallback, useContext, useRef } from "react";

export const FormContext = createContext<UseFormReturnType<FormValues> | null>(
  null
);

export function useFormValues() {
  const context = useContext(FormContext);

  if (context === null) {
    throw new Error("useFormValues must be used within a FormContext");
  }

  return context;
}

export function useStagedValues() {
  const form = useFormValues();
  return { ...form.values.settings };
}

export function useFormActions() {
  const form = useFormValues();

  const formRef = useRef(form);
  formRef.current = form;

  const update = useCallback((object: LooseObject) => {
    LOG("info", `Updating values`, object);
    formRef.current.setValues((values) => {
      const changes = { ...values.settings, ...object };
      return { ...values, settings: changes };
    });
  }, []);

  const setValue = useCallback((v: unknown, key: string) => {
    LOG("info", `Updating value of ${key}`, v);
    formRef.current.setValues((values) => {
      const changes = { ...values.settings, [key]: v };
      return { ...values, settings: changes };
    });
  }, []);

  return { update, setValue };
}

export type FormKey = keyof FormValues;
export type FormValues = {
  // Settings that saved to the backend
  settings: LooseObject;
  // Settings that saved to the frontend
  // storages: LooseObject;
};
