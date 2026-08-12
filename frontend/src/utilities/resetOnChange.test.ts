import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useResetOnChange } from "@/utilities/resetOnChange";

describe("useResetOnChange", () => {
  it("does not call onChange on mount", () => {
    const onChange = vi.fn();
    renderHook(() => useResetOnChange("a", onChange));

    expect(onChange).not.toHaveBeenCalled();
  });

  it("calls onChange when the key changes", () => {
    const onChange = vi.fn();
    const { rerender } = renderHook(
      ({ key }) => useResetOnChange(key, onChange),
      { initialProps: { key: "a" } },
    );

    rerender({ key: "b" });

    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("does not call onChange again when the key stays the same", () => {
    const onChange = vi.fn();
    const { rerender } = renderHook(
      ({ key }) => useResetOnChange(key, onChange),
      { initialProps: { key: "a" } },
    );

    rerender({ key: "a" });

    expect(onChange).not.toHaveBeenCalled();
  });
});
