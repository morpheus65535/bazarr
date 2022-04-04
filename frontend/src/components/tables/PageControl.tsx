import { Group, Pagination, Text } from "@mantine/core";
import { FunctionComponent } from "react";
interface Props {
  count: number;
  index: number;
  size: number;
  total: number;
  goto: (idx: number) => void;
  loading?: boolean;
}

const PageControl: FunctionComponent<Props> = ({
  count,
  index,
  size,
  total,
  goto,
  loading = false,
}) => {
  const empty = total === 0;
  const start = empty ? 0 : size * index + 1;
  const end = Math.min(size * (index + 1), total);

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
