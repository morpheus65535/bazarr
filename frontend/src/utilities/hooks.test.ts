import { useState } from "react";
import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  useArrayAction,
  useDebouncedValue,
  useInterval,
  useOnValueChange,
  useSelectorOptions,
  useSliderMarks,
  useThrottle,
} from "@/utilities/hooks";

describe("hooks utilities", () => {
  describe("useSelectorOptions", () => {
    it("maps options with labels and keys", () => {
      const options = ["a", "b"] as const;
      const { result } = renderHook(() =>
        useSelectorOptions(
          options,
          (v) => v.toUpperCase(),
          (v) => v,
        ),
      );

      expect(result.current.options).toEqual([
        { value: "a", label: "A" },
        { value: "b", label: "B" },
      ]);
      expect(result.current.getkey?.("a")).toBe("a");
    });
  });

  describe("useSliderMarks", () => {
    it("converts numbers into slider marks", () => {
      const { result } = renderHook(() => useSliderMarks([10, 20]));

      expect(result.current).toEqual([
        { value: 10, label: "10" },
        { value: 20, label: "20" },
      ]);
    });
  });

  describe("useArrayAction", () => {
    function useArrayActionWithState() {
      const [data, setData] = useState<string[]>([]);
      const action = useArrayAction<string>(setData);
      return { data, action };
    }

    it("adds rows", () => {
      const { result } = renderHook(() => useArrayActionWithState());

      act(() => result.current.action.add("foo"));

      expect(result.current.data).toEqual(["foo"]);
    });

    it("mutates rows by index", () => {
      const { result } = renderHook(() => useArrayActionWithState());

      act(() => result.current.action.add("foo"));
      act(() => result.current.action.mutate(0, "bar"));

      expect(result.current.data).toEqual(["bar"]);
    });

    it("ignores mutate when index is -1", () => {
      const { result } = renderHook(() => useArrayActionWithState());

      act(() => result.current.action.add("foo"));
      act(() => result.current.action.mutate(-1, "bar"));

      expect(result.current.data).toEqual(["foo"]);
    });

    it("removes rows by index", () => {
      const { result } = renderHook(() => useArrayActionWithState());

      act(() => result.current.action.add("foo"));
      act(() => result.current.action.add("bar"));
      act(() => result.current.action.remove(0));

      expect(result.current.data).toEqual(["bar"]);
    });

    it("ignores remove when index is -1", () => {
      const { result } = renderHook(() => useArrayActionWithState());

      act(() => result.current.action.add("foo"));
      act(() => result.current.action.remove(-1));

      expect(result.current.data).toEqual(["foo"]);
    });

    it("updates all rows with a mapper", () => {
      const { result } = renderHook(() => useArrayActionWithState());

      act(() => result.current.action.add("foo"));
      act(() => result.current.action.update((item) => item + "!"));

      expect(result.current.data).toEqual(["foo!"]);
    });
  });

  describe("useThrottle", () => {
    it("only executes the last call after the throttle window", () => {
      vi.useFakeTimers();
      const fn = vi.fn();
      const { result } = renderHook(() => useThrottle(fn, 100));

      act(() => result.current("a"));
      act(() => result.current("b"));
      act(() => result.current("c"));

      expect(fn).not.toHaveBeenCalled();

      act(() => vi.advanceTimersByTime(1000));

      expect(fn).toHaveBeenCalledTimes(1);
      expect(fn).toHaveBeenCalledWith("c");

      vi.useRealTimers();
    });
  });

  describe("useDebouncedValue", () => {
    it("delays updating the value until the debounce window passes", () => {
      vi.useFakeTimers();
      const { result, rerender } = renderHook(
        ({ value }) => useDebouncedValue(value, 100),
        { initialProps: { value: "a" } },
      );

      expect(result.current).toBe("a");

      rerender({ value: "b" });

      expect(result.current).toBe("a");

      act(() => vi.advanceTimersByTime(1000));

      expect(result.current).toBe("b");

      vi.useRealTimers();
    });
  });

  describe("useOnValueChange", () => {
    it("calls the callback when the value changes", () => {
      const onChange = vi.fn();
      const { rerender } = renderHook(
        ({ value }) => useOnValueChange(value, onChange),
        { initialProps: { value: 1 } },
      );

      expect(onChange).toHaveBeenCalledWith(1);

      rerender({ value: 2 });

      expect(onChange).toHaveBeenCalledWith(2);
      expect(onChange).toHaveBeenCalledTimes(2);
    });

    it("does not call the callback when the value is unchanged", () => {
      const onChange = vi.fn();
      const { rerender } = renderHook(
        ({ value }) => useOnValueChange(value, onChange),
        { initialProps: { value: 1 } },
      );

      rerender({ value: 1 });

      expect(onChange).toHaveBeenCalledTimes(1);
    });
  });

  describe("useInterval", () => {
    it("calls the callback repeatedly on the configured interval", () => {
      vi.useFakeTimers();
      const fn = vi.fn();

      renderHook(() => useInterval(fn, 1000));

      act(() => vi.advanceTimersByTime(3000));

      expect(fn).toHaveBeenCalledTimes(3);

      vi.useRealTimers();
    });
  });
});
