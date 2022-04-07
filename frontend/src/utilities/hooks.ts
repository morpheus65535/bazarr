import { SelectorOption, SelectorProps } from "@/components";
import { useDidUpdate } from "@mantine/hooks";
import { useCallback, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

export function useGotoHomepage() {
  const navigate = useNavigate();
  return useCallback(() => navigate("/"), [navigate]);
}

export function useIsArrayExtended(arr: unknown[]) {
  const [size, setSize] = useState(arr.length);
  const [isExtended, setExtended] = useState(arr.length !== 0);

  useDidUpdate(() => {
    setExtended(arr.length > size);
    setSize(arr.length);
  }, [arr.length]);

  return isExtended;
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
