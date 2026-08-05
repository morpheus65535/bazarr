import { afterEach, beforeEach, describe, expect, it, vitest } from "vitest";
import { UseInfinitePaginationQueryResult } from "@/apis/queries/hooks";
import { customRender, screen, waitFor } from "@/tests";
import QueryPosterGrid from "./QueryPosterGrid";

const item = { title: "My Movie", radarrId: 1 } as Item.Movie;

const observer: { callback?: IntersectionObserverCallback } = {};

class MockIntersectionObserver {
  constructor(callback: IntersectionObserverCallback) {
    observer.callback = callback;
  }
  observe() {
    return undefined;
  }
  unobserve() {
    return undefined;
  }
  disconnect() {
    return undefined;
  }
}

const intersect = (isIntersecting: boolean) => {
  observer.callback?.(
    [{ isIntersecting } as IntersectionObserverEntry],
    {} as IntersectionObserver,
  );
};

interface QueryOverrides {
  hasNextPage?: boolean;
  isFetchingNextPage?: boolean;
}

const buildQuery = (
  overrides: QueryOverrides = {},
): UseInfinitePaginationQueryResult<Item.Movie> => {
  return {
    items: [item],
    paginationStatus: {
      isInitialLoading: false,
      isFetchingNextPage: overrides.isFetchingNextPage ?? false,
      hasNextPage: overrides.hasNextPage ?? true,
      totalCount: 1,
      pageSize: 50,
    },
    controls: { fetchNextPage: vitest.fn() },
  } as unknown as UseInfinitePaginationQueryResult<Item.Movie>;
};

const renderPoster = (item: Item.Movie) => {
  return <div data-testid="poster-card">{item.title}</div>;
};

describe("QueryPosterGrid", () => {
  const OriginalIntersectionObserver = window.IntersectionObserver;

  beforeEach(() => {
    observer.callback = undefined;
    window.IntersectionObserver =
      MockIntersectionObserver as unknown as typeof window.IntersectionObserver;
  });

  afterEach(() => {
    window.IntersectionObserver = OriginalIntersectionObserver;
  });

  it("renders the posters and the sentinel while more pages exist", () => {
    customRender(
      <QueryPosterGrid query={buildQuery()} renderPoster={renderPoster} />,
    );

    expect(screen.getByTestId("poster-card")).toBeInTheDocument();
    expect(screen.getByTestId("poster-grid-sentinel")).toBeInTheDocument();
  });

  it("fetches the next page when the sentinel intersects", async () => {
    const query = buildQuery();

    customRender(<QueryPosterGrid query={query} renderPoster={renderPoster} />);

    intersect(true);

    await waitFor(() =>
      expect(query.controls.fetchNextPage).toHaveBeenCalledTimes(1),
    );
  });

  it("does not fetch when the sentinel leaves the viewport", async () => {
    const query = buildQuery();

    customRender(<QueryPosterGrid query={query} renderPoster={renderPoster} />);

    intersect(false);

    await screen.findByTestId("poster-card");
    expect(query.controls.fetchNextPage).not.toHaveBeenCalled();
  });

  it("hides the sentinel when no more pages exist", () => {
    customRender(
      <QueryPosterGrid
        query={buildQuery({ hasNextPage: false })}
        renderPoster={renderPoster}
      />,
    );

    expect(screen.getByTestId("poster-card")).toBeInTheDocument();
    expect(
      screen.queryByTestId("poster-grid-sentinel"),
    ).not.toBeInTheDocument();
  });
});
