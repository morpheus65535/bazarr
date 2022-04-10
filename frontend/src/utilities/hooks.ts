import { SelectorOption, SelectorProps } from "@/components";
import {
  Dispatch,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
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
    [options]
  );

  return useMemo(
    () => ({
      options: wrappedOptions,
      getkey: keyRef.current ?? labelRef.current,
    }),
    [wrappedOptions]
  );
}

// High performance action wrapper for array, typically used for table updates
export function useArrayAction<T>(setData: Dispatch<(prev: T[]) => T[]>) {
  const setDataRef = useRef(setData);
  setDataRef.current = setData;

  const add = useCallback((row: T) => {
    setDataRef.current((data) => {
      return [...data, row];
    });
  }, []);

  const mutate = useCallback((index: number, row: T) => {
    setDataRef.current((data) => {
      if (index !== -1) {
        const list = [...data];
        list[index] = row;
        return list;
      }

      return data;
    });
  }, []);

  const remove = useCallback((index: number) => {
    setDataRef.current((data) => {
      if (index !== -1) {
        const list = [...data];
        list.splice(index, 1);
        return list;
      }

      return data;
    });
  }, []);

  const update = useCallback((fn: (item: T) => T) => {
    setDataRef.current((data) => {
      return data.map(fn);
    });
  }, []);

  return useMemo(
    () => ({
      add,
      mutate,
      remove,
      update,
    }),
    [add, mutate, remove, update]
  );
}

export function useThrottle<F extends GenericFunction>(fn: F, ms: number) {
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const timer = useRef<number>();

  return useCallback(
    (...args: Parameters<F>) => {
      if (timer.current) {
        clearTimeout(timer.current);
        timer.current = undefined;
      }
      timer.current = window.setTimeout(() => fnRef.current(...args), ms);
    },
    [ms]
  );
}

export function useDebouncedValue<T>(item: T, ms: number) {
  const [value, setValue] = useState(item);

  const debouncedSetValue = useThrottle(setValue, ms);

  useEffect(() => {
    debouncedSetValue(item);
  }, [debouncedSetValue, item]);

  return value;
}
