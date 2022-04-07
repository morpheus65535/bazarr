import { withModal } from "@/modules/modals";
import { Code, ScrollArea, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";

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
    [stack]
  );

  return (
    <ScrollArea>
      <pre>
        <Code>{result}</Code>
      </pre>
    </ScrollArea>
  );
};

export default withModal(SystemLogModal, "system-log");
