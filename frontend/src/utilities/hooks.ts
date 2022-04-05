import { SelectorOption } from "@/components";
import { useCallback, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDidUpdate } from "rooks";

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
  label: (value: T) => string
): { options: SelectorOption<T>[]; getLabel: (value: T) => string } {
  const labelRef = useRef(label);
  labelRef.current = label;

  const wrappedOptions = useMemo(
    () => options.map((value) => ({ value, label: labelRef.current(value) })),
    [options, labelRef]
  );

  return { options: wrappedOptions, getLabel: labelRef.current };
}
