import { FunctionComponent, useMemo } from "react";
import { Code, Text } from "@mantine/core";
import { withModal } from "@/modules/modals";

interface Props {
  stack: string;
}

const SystemLogModal: FunctionComponent<Props> = ({ stack }) => {
  const result = useMemo(
    () =>
      stack.split("\\n").map((v, idx) => (
        <Text my="xs" inherit key={idx}>
          {v}
        </Text>
      )),
    [stack],
  );

  return <Code block>{result}</Code>;
};

export default withModal(SystemLogModal, "system-log", {
  title: "Stack Traceback",
  size: "xl",
});
