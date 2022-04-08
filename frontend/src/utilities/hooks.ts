import { SelectorOption, SelectorProps } from "@/components";
import { useCallback, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";

export function useGotoHomepage() {
  const navigate = useNavigate();
  return useCallback(() => navigate("/"), [navigate]);
}

export function useSelectorOptions<T>(
  options: readonly T[],
  label: (value: T) => string,
  key?: (value: T) => string
): Pick<SelectorProps<T>, "options" | "getkey"> {
  const labelRef = useRef(label);
  labelRef.current = label;

  const keyRef = useRef(key);
  keyRef.current = key;

  const wrappedOptions = useMemo(
    () =>
      options.map<SelectorOption<T>>((value) => ({
        value,
        label: labelRef.current(value),
      })),
    [options, labelRef]
  );

  return {
    options: wrappedOptions,
    getkey: keyRef.current ?? labelRef.current,
  };
}

export function useLatestRef<T>(item: T) {
  const ref = useRef<T>(item);
  ref.current = item;

  return ref;
}
