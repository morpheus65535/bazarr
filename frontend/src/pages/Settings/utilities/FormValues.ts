import { createContext, useCallback, useContext, useRef } from "react";
import type { UseFormReturnType } from "@mantine/form";
import { LOG } from "@/utilities/console";

export const FormContext = createContext<UseFormReturnType<FormValues> | null>(
  null,
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

  const setValue = useCallback((v: unknown, key: string, hook?: HookType) => {
    LOG("info", `Updating value of ${key}`, v);
    formRef.current.setValues((values) => {
      const changes = { ...values.settings, [key]: v };
      const hooks = { ...values.hooks };

      if (hook) {
        LOG(
          "info",
          `Adding submit hook ${key}, will be executed before submitting`,
        );
        hooks[key] = hook;
      }

      return { ...values, settings: changes, hooks };
    });
  }, []);

  return { update, setValue };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type HookType = (value: any) => unknown;

export type FormKey = keyof FormValues;
export type FormValues = {
  // Settings that saved to the backend
  settings: LooseObject;
  // Settings that saved to the frontend
  // storages: LooseObject;

  // submit hooks
  hooks: StrictObject<HookType>;
};

export function runHooks(
  hooks: FormValues["hooks"],
  settings: FormValues["settings"],
) {
  for (const key in settings) {
    if (key in hooks) {
      LOG("info", "Running submit hook for", key, settings[key]);
      const value = settings[key];
      const fn = hooks[key];
      settings[key] = fn(value);
      LOG("info", "Finish submit hook", key, settings[key]);
    }
  }
}
