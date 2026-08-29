import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
} from "react";
import type { UseFormReturnType } from "@mantine/form";
import { LOG } from "@/utilities/console";

export const FormContext = createContext<UseFormReturnType<FormValues> | null>(
  null,
);

export const useFormValues = () => {
  const context = useContext(FormContext);

  if (context === null) {
    throw new Error("useFormValues must be used within a FormContext");
  }

  return context;
};

export const useStagedValues = () => {
  const form = useFormValues();
  return { ...form.values.settings };
};

export const useFormActions = () => {
  const form = useFormValues();

  const formRef = useRef(form);

  useEffect(() => {
    formRef.current = form;
  });

  const update = useCallback((object: Record<string, unknown>) => {
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

  // Removes a previously staged value, e.g. when a field is reverted back to
  // its original value so it no longer counts as an unsaved change.
  const removeValue = useCallback((key: string) => {
    LOG("info", `Removing staged value of ${key}`);
    formRef.current.setValues((values) => {
      const changes = { ...values.settings };
      const hooks = { ...values.hooks };
      delete changes[key];
      delete hooks[key];
      return { ...values, settings: changes, hooks };
    });
  }, []);

  return { update, setValue, removeValue };
};

export type HookType = (value: unknown) => unknown;

export type FormKey = keyof FormValues;
export type FormValues = {
  // Settings that saved to the backend
  settings: Record<string, unknown>;

  // submit hooks
  hooks: StrictObject<HookType>;
};

export const runHooks = (
  hooks: FormValues["hooks"],
  settings: FormValues["settings"],
) => {
  for (const key in settings) {
    if (key in hooks) {
      LOG("info", "Running submit hook for", key, settings[key]);
      const value = settings[key];
      const fn = hooks[key];
      settings[key] = fn(value);
      LOG("info", "Finish submit hook", key, settings[key]);
    }
  }
};
