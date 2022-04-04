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
  goto,
  loadState,
}) => {
  const empty = total === 0;
  const start = empty ? 0 : size * index + 1;
  const end = Math.min(size * (index + 1), total);

  const loading = loadState !== undefined;

  return (
    <Group p={16} position="apart">
      <Text size="sm">
        Show {start} to {end} of {total} entries
      </Text>
      <Pagination
        size="sm"
        color={loading ? "gray" : "primary"}
        page={index + 1}
        onChange={(page) => goto(page - 1)}
        hidden={count <= 1}
        total={count}
      ></Pagination>
    </Group>
  );
};

export default PageControl;
