import { FunctionComponent, useEffect } from "react";
import { Group, Pagination, Text } from "@mantine/core";
import { useIsLoading } from "@/contexts";

interface Props {
  count: number;
  index: number;
  size: number;
  total: number;
  goto: (idx: number) => void;
}

const PageControl: FunctionComponent<Props> = ({
  count,
  index,
  size,
  total,
  goto,
}) => {
  const empty = total === 0;
  const start = empty ? 0 : size * index + 1;
  const end = Math.min(size * (index + 1), total);

  const isLoading = useIsLoading();

  // Jump to first page if total page count changes
  useEffect(() => {
    goto(0);
  }, [total, goto]);

  return (
    <Group p={16} justify="space-between">
      <Text size="sm">
        Show {start} to {end} of {total} entries
      </Text>
      <Pagination
        size="sm"
        color={isLoading ? "gray" : "primary"}
        value={index + 1}
        onChange={(page) => goto(page - 1)}
        hidden={count <= 1}
        total={count}
      ></Pagination>
    </Group>
  );
};

export default PageControl;
