import { SelectorOption, SelectorProps } from "@/components";
import { Dispatch, SetStateAction, useCallback, useMemo, useRef } from "react";
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
export function useArrayAction<T>(setData: Dispatch<SetStateAction<T[]>>) {
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
