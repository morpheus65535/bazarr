import { ReactNode } from "react";
import { Box, Skeleton, Text } from "@mantine/core";
import { useIsLoading } from "@/contexts";
import { usePageSize } from "@/utilities/storage";
import styles from "./PosterGrid.module.scss";

export interface PosterGridProps<T extends object> {
  data: T[];
  renderPoster: (item: T) => ReactNode;
  emptyText?: string;
  // Number of skeleton posters appended after the data, shown while the next
  // page of an infinite scroll is loading.
  loadingMoreCount?: number;
}

const PosterGrid = <T extends object>(props: PosterGridProps<T>) => {
  const { data, renderPoster, emptyText, loadingMoreCount = 0 } = props;

  const isLoading = useIsLoading();
  const pageSize = usePageSize();

  if (isLoading) {
    return (
      <Box className={styles.grid}>
        {Array(pageSize)
          .fill(0)
          .map((_, i) => (
            <Skeleton key={i} className={styles.skeleton}></Skeleton>
          ))}
      </Box>
    );
  }

  if (data.length === 0) {
    return emptyText ? (
      <Text ta="center" p="md">
        {emptyText}
      </Text>
    ) : null;
  }

  return (
    <Box className={styles.grid}>
      {data.map(renderPoster)}
      {Array(loadingMoreCount)
        .fill(0)
        .map((_, i) => (
          <Skeleton
            key={`loading-more-${i}`}
            className={styles.skeleton}
          ></Skeleton>
        ))}
    </Box>
  );
};

export default PosterGrid;
