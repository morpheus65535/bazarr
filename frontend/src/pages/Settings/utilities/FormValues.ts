import { LOG } from "@/utilities/console";
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
  return { ...form.values.settings, ...form.values.storages };
}

export function useFormActions() {
  const form = useFormValues();

  const formRef = useRef(form);
  formRef.current = form;

  const update = useCallback(
    (object: LooseObject, location: FormKey = "settings") => {
      LOG("info", `Updating values in ${location}`, object);
      formRef.current.setValues((values) => {
        const changes = { ...values[location], ...object };
        return { ...values, [location]: changes };
      });
    },
    []
  );

  const setValue = useCallback(
    (v: unknown, key: string, location: FormKey = "settings") => {
      LOG("info", `Updating value of ${key} in ${location}`, v);
      formRef.current.setValues((values) => {
        const changes = { ...values[location], [key]: v };
        return { ...values, [location]: changes };
      });
    },
    []
  );

  return { update, setValue };
}

export type FormKey = keyof FormValues;
export type FormValues = {
  // Settings that saved to the backend
  settings: LooseObject;
  // Settings that saved to the frontend
  storages: LooseObject;
};
