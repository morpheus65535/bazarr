import { FunctionComponent, PropsWithChildren } from "react";
import type { UseFormReturnType } from "@mantine/form";
import { renderHook } from "@testing-library/react";
import { describe, expect, it, vitest } from "vitest";
import { FormContext, FormValues } from "@/pages/Settings/utilities/FormValues";
import {
  useBaseInput,
  useSettingValue,
  useUpdateArray,
} from "@/pages/Settings/utilities/hooks";
import { SettingsProvider } from "@/pages/Settings/utilities/SettingsProvider";

function createForm(
  values: FormValues = { settings: {}, hooks: {} },
  setValues = vitest.fn(),
): UseFormReturnType<FormValues> {
  return {
    values,
    setValues,
  } as unknown as UseFormReturnType<FormValues>;
}

function createWrapper(
  form: UseFormReturnType<FormValues>,
  settings: Settings,
) {
  const Wrapper: FunctionComponent<PropsWithChildren> = ({ children }) => (
    <SettingsProvider value={settings}>
      <FormContext.Provider value={form}>{children}</FormContext.Provider>
    </SettingsProvider>
  );
  return Wrapper;
}

describe("Settings hooks", () => {
  const settings = {
    test: { key: "original" },
  } as unknown as Settings;

  describe("useBaseInput", () => {
    it("returns the staged value and an update function", () => {
      const form = createForm({
        settings: { "test-key": "staged" },
        hooks: {},
      });
      const { result } = renderHook(
        () => useBaseInput({ settingKey: "test-key" }),
        {
          wrapper: createWrapper(form, settings),
        },
      );

      expect(result.current.value).toBe("staged");
      expect(result.current.rest).toEqual({});
    });
  });

  describe("useSettingValue", () => {
    it("returns the staged value when available", () => {
      const form = createForm({
        settings: { "test-key": "staged" },
        hooks: {},
      });
      const { result } = renderHook(() => useSettingValue("test-key"), {
        wrapper: createWrapper(form, settings),
      });

      expect(result.current).toBe("staged");
    });

    it("returns the original value when no staged value exists", () => {
      const form = createForm({ settings: {}, hooks: {} });
      const { result } = renderHook(
        () => useSettingValue("settings-test-key"),
        {
          wrapper: createWrapper(form, settings),
        },
      );

      expect(result.current).toBe("original");
    });

    it("uses the onLoaded loader when provided", () => {
      const onLoaded = vitest.fn().mockReturnValue("loaded");
      const form = createForm({ settings: {}, hooks: {} });
      const { result } = renderHook(
        () => useSettingValue("test-key", { onLoaded }),
        {
          wrapper: createWrapper(form, settings),
        },
      );

      expect(onLoaded).toHaveBeenCalledWith(settings);
      expect(result.current).toBe("loaded");
    });

    it("falls back to defaultValue when the original value is null", () => {
      const form = createForm({ settings: {}, hooks: {} });
      const { result } = renderHook(
        () => useSettingValue("missing-key", { defaultValue: "fallback" }),
        {
          wrapper: createWrapper(form, settings),
        },
      );

      expect(result.current).toBe("fallback");
    });

    it("returns the original value when original option is true", () => {
      const form = createForm({
        settings: { "settings-test-key": "staged" },
        hooks: {},
      });
      const { result } = renderHook(
        () => useSettingValue("settings-test-key", { original: true }),
        {
          wrapper: createWrapper(form, settings),
        },
      );

      expect(result.current).toBe("original");
    });
  });

  describe("useUpdateArray", () => {
    it("updates the array with a unique item", () => {
      const setValues = vitest.fn();
      const form = createForm({ settings: {}, hooks: {} }, setValues);
      const { result } = renderHook(
        () => useUpdateArray("arr-key", [{ id: 1 }, { id: 2 }], "id"),
        {
          wrapper: createWrapper(form, settings),
        },
      );

      result.current({ id: 3 });

      expect(setValues).toHaveBeenCalled();
      const updater = setValues.mock.calls[0][0] as (
        values: FormValues,
      ) => FormValues;
      expect(updater({ settings: {}, hooks: {} })).toEqual({
        settings: { "arr-key": [{ id: 3 }, { id: 1 }, { id: 2 }] },
        hooks: {},
      });
    });

    it("uses the staged array when available", () => {
      const setValues = vitest.fn();
      const form = createForm(
        {
          settings: { "arr-key": [{ id: 10 }, { id: 20 }] },
          hooks: {},
        },
        setValues,
      );
      const { result } = renderHook(
        () => useUpdateArray("arr-key", [{ id: 1 }, { id: 2 }], "id"),
        {
          wrapper: createWrapper(form, settings),
        },
      );

      result.current({ id: 30 });

      const updater = setValues.mock.calls[0][0] as (
        values: FormValues,
      ) => FormValues;
      expect(updater({ settings: {}, hooks: {} })).toEqual({
        settings: { "arr-key": [{ id: 30 }, { id: 10 }, { id: 20 }] },
        hooks: {},
      });
    });
  });
});
