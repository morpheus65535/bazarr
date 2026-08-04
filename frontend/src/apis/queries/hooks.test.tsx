import { FunctionComponent, PropsWithChildren } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vitest } from "vitest";
import queryClient from "@/apis/queries";
import { renderHook, waitFor } from "@/tests";
import { useInfinitePaginationQuery } from "./hooks";

const wrapper: FunctionComponent<PropsWithChildren> = ({ children }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

// The settings mock in the test setup provides no page_size, so usePageSize
// falls back to 50.
const pageSize = 50;

function buildItems(start: number, count: number): Item.Movie[] {
  return Array(count)
    .fill(0)
    .map(
      (_, i) =>
        ({ radarrId: start + i, title: `Movie ${start + i}` }) as Item.Movie,
    );
}

describe("useInfinitePaginationQuery", () => {
  it("accumulates pages and stops at the total count", async () => {
    const total = pageSize + 10;

    const queryFn = vitest.fn((param: Parameter.Range) =>
      Promise.resolve({
        data: buildItems(
          param.start,
          Math.min(param.length, total - param.start),
        ),
        total,
      }),
    );

    const { result } = renderHook(
      () => useInfinitePaginationQuery(["test-infinite"], queryFn, false),
      { wrapper },
    );

    await waitFor(() => expect(result.current.items).toHaveLength(pageSize));
    expect(result.current.paginationStatus.hasNextPage).toBe(true);
    expect(result.current.paginationStatus.totalCount).toBe(total);

    result.current.controls.fetchNextPage();

    await waitFor(() => expect(result.current.items).toHaveLength(total));
    expect(result.current.paginationStatus.hasNextPage).toBe(false);
    expect(queryFn).toHaveBeenCalledTimes(2);

    // No more pages: further calls are no-ops
    result.current.controls.fetchNextPage();
    expect(queryFn).toHaveBeenCalledTimes(2);

    expect(queryFn).toHaveBeenCalledWith({ start: 0, length: pageSize });
    expect(queryFn).toHaveBeenCalledWith({ start: pageSize, length: pageSize });
  });

  it("seeds the individual item cache when enabled", async () => {
    const queryKey = ["test-infinite-seed"];

    const queryFn = vitest.fn(() =>
      Promise.resolve({
        data: [{ radarrId: 42, title: "Seeded" } as Item.Movie],
        total: 1,
      }),
    );

    const { result } = renderHook(
      () => useInfinitePaginationQuery(queryKey, queryFn, true),
      { wrapper },
    );

    await waitFor(() => expect(result.current.items).toHaveLength(1));

    expect(queryClient.getQueryData([...queryKey, 42])).toEqual({
      radarrId: 42,
      title: "Seeded",
    });
  });
});
