import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useViewMode } from "./viewMode";

describe("useViewMode", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("defaults to table view", () => {
    const { result } = renderHook(() => useViewMode("test-view-mode"));

    expect(result.current[0]).toBe("table");
  });

  it("persists the selection to localStorage", () => {
    const { result } = renderHook(() => useViewMode("test-view-mode"));

    act(() => {
      result.current[1]("poster");
    });

    expect(result.current[0]).toBe("poster");
    expect(window.localStorage.getItem("test-view-mode")).toBe(
      JSON.stringify("poster"),
    );
  });

  it("restores the persisted value on mount", () => {
    window.localStorage.setItem("test-view-mode", JSON.stringify("poster"));

    const { result } = renderHook(() => useViewMode("test-view-mode"));

    expect(result.current[0]).toBe("poster");
  });

  it("keeps independent modes per key", () => {
    const { result: seriesResult } = renderHook(() =>
      useViewMode("series-view-mode"),
    );
    const { result: moviesResult } = renderHook(() =>
      useViewMode("movies-view-mode"),
    );

    act(() => {
      seriesResult.current[1]("poster");
    });

    expect(seriesResult.current[0]).toBe("poster");
    expect(moviesResult.current[0]).toBe("table");
  });
});
