import { ReactNode } from "react";
import { Box, Skeleton, Text } from "@mantine/core";
import { useIsLoading } from "@/contexts";
import { usePageSize } from "@/utilities/storage";
import styles from "./PosterGrid.module.scss";

export interface PosterGridProps<T extends object> {
  data: T[];
  renderPoster: (item: T) => ReactNode;
  emptyText?: string;
}

export default function PosterGrid<T extends object>(
  props: PosterGridProps<T>,
) {
  const { data, renderPoster, emptyText } = props;

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

  return <Box className={styles.grid}>{data.map(renderPoster)}</Box>;
}
