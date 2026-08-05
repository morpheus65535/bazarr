import { FunctionComponent, PropsWithChildren } from "react";
import type { UseFormReturnType } from "@mantine/form";
import { renderHook } from "@testing-library/react";
import { describe, expect, it, vitest } from "vitest";
import {
  FormContext,
  FormValues,
  runHooks,
  useFormActions,
  useFormValues,
  useStagedValues,
} from "@/pages/Settings/utilities/FormValues";

const createWrapper = (form: UseFormReturnType<FormValues>) => {
  const Wrapper: FunctionComponent<PropsWithChildren> = ({ children }) => (
    <FormContext.Provider value={form}>{children}</FormContext.Provider>
  );
  return Wrapper;
};

const createForm = (
  values: FormValues = { settings: {}, hooks: {} },
  setValues = vitest.fn(),
): UseFormReturnType<FormValues> =>
  ({
    values,
    setValues,
  }) as unknown as UseFormReturnType<FormValues>;

describe("FormValues utilities", () => {
  describe("runHooks", () => {
    it("runs matching hooks and updates settings", () => {
      const hooks = {
        name: (value: unknown) => `${value}-modified`,
      };

      const settings: FormValues["settings"] = {
        name: "original",
        untouched: "value",
      };

      runHooks(hooks, settings);

      expect(settings.name).toBe("original-modified");
      expect(settings.untouched).toBe("value");
    });

    it("does not mutate settings when no hook matches", () => {
      const settings: FormValues["settings"] = { name: "value" };

      runHooks({}, settings);

      expect(settings.name).toBe("value");
    });
  });

  describe("useFormValues", () => {
    it("throws when used outside a FormContext", () => {
      expect(() => renderHook(() => useFormValues())).toThrow(
        "useFormValues must be used within a FormContext",
      );
    });
  });

  describe("useStagedValues", () => {
    it("returns the current settings values", () => {
      const form = createForm({ settings: { foo: "bar" }, hooks: {} });
      const { result } = renderHook(() => useStagedValues(), {
        wrapper: createWrapper(form),
      });

      expect(result.current).toEqual({ foo: "bar" });
    });
  });

  describe("useFormActions", () => {
    it("update merges an object into settings", () => {
      const setValues = vitest.fn();
      const form = createForm(
        { settings: { existing: "value" }, hooks: {} },
        setValues,
      );
      const { result } = renderHook(() => useFormActions(), {
        wrapper: createWrapper(form),
      });

      result.current.update({ added: "new" });

      expect(setValues).toHaveBeenCalled();
      const updater = setValues.mock.calls[0][0] as (
        values: FormValues,
      ) => FormValues;
      expect(updater({ settings: { existing: "value" }, hooks: {} })).toEqual({
        settings: { existing: "value", added: "new" },
        hooks: {},
      });
    });

    it("setValue updates a single setting and registers a hook", () => {
      const setValues = vitest.fn();
      const form = createForm({ settings: {}, hooks: {} }, setValues);
      const { result } = renderHook(() => useFormActions(), {
        wrapper: createWrapper(form),
      });

      const hook = (value: unknown) => `${value}-hooked`;
      result.current.setValue("new-value", "key", hook);

      const updater = setValues.mock.calls[0][0] as (
        values: FormValues,
      ) => FormValues;
      expect(updater({ settings: {}, hooks: {} })).toEqual({
        settings: { key: "new-value" },
        hooks: { key: hook },
      });
    });

    it("setValue updates a setting without a hook", () => {
      const setValues = vitest.fn();
      const form = createForm({ settings: {}, hooks: {} }, setValues);
      const { result } = renderHook(() => useFormActions(), {
        wrapper: createWrapper(form),
      });

      result.current.setValue("new-value", "key");

      const updater = setValues.mock.calls[0][0] as (
        values: FormValues,
      ) => FormValues;
      expect(updater({ settings: {}, hooks: {} })).toEqual({
        settings: { key: "new-value" },
        hooks: {},
      });
    });
  });
});
