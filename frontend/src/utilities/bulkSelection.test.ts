import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useBulkSelection } from "@/utilities/bulkSelection";

describe("useBulkSelection", () => {
  it("starts inactive with no selection or staged changes", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    expect(result.current.active).toBe(false);
    expect(result.current.selectedIds.size).toBe(0);
    expect(result.current.dirties.size).toBe(0);
  });

  it("toggleActive turns select mode on and off", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    act(() => result.current.toggleActive());
    expect(result.current.active).toBe(true);

    act(() => result.current.toggleActive());
    expect(result.current.active).toBe(false);
  });

  it("toggleActive off clears the selection and staged changes", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    act(() => result.current.toggleActive());
    act(() => result.current.toggle(1));
    act(() => result.current.stage(2));

    expect(result.current.dirties.get(1)).toBe(2);

    act(() => result.current.toggleActive());

    expect(result.current.active).toBe(false);
    expect(result.current.selectedIds.size).toBe(0);
    expect(result.current.dirties.size).toBe(0);
  });

  it("toggle adds and removes an id from the selection", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    act(() => result.current.toggle(1));
    expect(result.current.isSelected(1)).toBe(true);

    act(() => result.current.toggle(1));
    expect(result.current.isSelected(1)).toBe(false);
  });

  it("setMany selects or deselects a batch of ids", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    act(() => result.current.setMany([1, 2, 3], true));
    expect(result.current.selectedIds).toEqual(new Set([1, 2, 3]));

    act(() => result.current.setMany([2], false));
    expect(result.current.selectedIds).toEqual(new Set([1, 3]));
  });

  it("stage moves the current selection into dirties and clears the selection", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    act(() => result.current.setMany([1, 2], true));
    act(() => result.current.stage(5));

    expect(result.current.selectedIds.size).toBe(0);
    expect(result.current.dirties.get(1)).toBe(5);
    expect(result.current.dirties.get(2)).toBe(5);
  });

  it("stage supports staging a null profile", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    act(() => result.current.setMany([1], true));
    act(() => result.current.stage(null));

    expect(result.current.dirties.get(1)).toBeNull();
  });

  it("a later stage overwrites an earlier one for the same id", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    act(() => result.current.setMany([1], true));
    act(() => result.current.stage(5));
    act(() => result.current.setMany([1], true));
    act(() => result.current.stage(9));

    expect(result.current.dirties.get(1)).toBe(9);
    expect(result.current.dirties.size).toBe(1);
  });

  it("clear empties the selection and staged changes without exiting select mode", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    act(() => result.current.toggleActive());
    act(() => result.current.setMany([1], true));
    act(() => result.current.stage(5));
    act(() => result.current.clear());

    expect(result.current.active).toBe(true);
    expect(result.current.selectedIds.size).toBe(0);
    expect(result.current.dirties.size).toBe(0);
  });

  it("deactivate exits select mode and clears state, and is a no-op-safe when already inactive", () => {
    const { result } = renderHook(() => useBulkSelection("key"));

    act(() => result.current.toggleActive());
    act(() => result.current.setMany([1], true));
    act(() => result.current.stage(5));
    act(() => result.current.deactivate());

    expect(result.current.active).toBe(false);
    expect(result.current.selectedIds.size).toBe(0);
    expect(result.current.dirties.size).toBe(0);

    act(() => result.current.deactivate());

    expect(result.current.active).toBe(false);
  });

  it("resets the selection, but not staged changes, when the key changes", () => {
    const { result, rerender } = renderHook(
      ({ key }) => useBulkSelection(key),
      { initialProps: { key: "a" } },
    );

    act(() => result.current.setMany([1], true));
    act(() => result.current.stage(5));
    act(() => result.current.setMany([2], true));

    expect(result.current.selectedIds).toEqual(new Set([2]));
    expect(result.current.dirties.get(1)).toBe(5);

    rerender({ key: "b" });

    expect(result.current.selectedIds.size).toBe(0);
    expect(result.current.dirties.get(1)).toBe(5);
  });
});
