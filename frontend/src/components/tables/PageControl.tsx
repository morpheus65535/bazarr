import { Group, Pagination, Text } from "@mantine/core";
import { FunctionComponent } from "react";
import { PageControlAction } from "./types";
interface Props {
  count: number;
  index: number;
  size: number;
  total: number;
  canPrevious: boolean;
  previous: () => void;
  canNext: boolean;
  next: () => void;
  goto: (idx: number) => void;
  loadState?: PageControlAction;
}

const PageControl: FunctionComponent<Props> = ({
  count,
  index,
  size,
  total,
  canPrevious,
  previous,
  canNext,
  next,
  goto,
  loadState,
}) => {
  const empty = total === 0;
  const start = empty ? 0 : size * index + 1;
  const end = Math.min(size * (index + 1), total);

  const loading = loadState !== undefined;

  return (
    <Group>
      <Text>
        Show {start} to {end} of {total} entries
      </Text>
      <Pagination hidden={count <= 1} total={size}></Pagination>
    </Group>
  );
};

export default PageControl;
