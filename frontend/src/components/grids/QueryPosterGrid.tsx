import { useEffect } from "react";
import { Box } from "@mantine/core";
import { useIntersection } from "@mantine/hooks";
import { UseInfinitePaginationQueryResult } from "@/apis/queries/hooks";
import { LoadingProvider } from "@/contexts";
import PosterGrid, { PosterGridProps } from "./PosterGrid";

// Cap the trailing skeletons so a large configured page size does not render
// dozens of placeholders on every page fetch
const loadingMoreSkeletonCount = 10;

type Props<T extends object> = Omit<
  PosterGridProps<T>,
  "data" | "loadingMoreCount"
> & {
  query: UseInfinitePaginationQueryResult<T>;
};

const QueryPosterGrid = <T extends object>(props: Props<T>) => {
  const { query, ...remain } = props;

  const {
    items,
    paginationStatus: {
      isInitialLoading,
      isFetchingNextPage,
      hasNextPage,
      pageSize,
    },
    controls: { fetchNextPage },
  } = query;

  const { ref, entry } = useIntersection({ rootMargin: "400px" });

  const isIntersecting = entry?.isIntersecting ?? false;

  useEffect(() => {
    if (isIntersecting) {
      fetchNextPage();
    }
  }, [isIntersecting, fetchNextPage]);

  return (
    <LoadingProvider value={isInitialLoading}>
      <PosterGrid
        {...remain}
        data={items}
        loadingMoreCount={
          isFetchingNextPage ? Math.min(pageSize, loadingMoreSkeletonCount) : 0
        }
      ></PosterGrid>
      {hasNextPage && (
        <Box ref={ref} data-testid="poster-grid-sentinel" h={1}></Box>
      )}
    </LoadingProvider>
  );
};

export default QueryPosterGrid;
