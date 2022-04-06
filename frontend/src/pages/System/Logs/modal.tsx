import { useModal, usePayload, withModal } from "@/modules/modals";
import { Code, ScrollArea, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";

const SystemLogModal: FunctionComponent = () => {
  const stack = usePayload<string>();

  const Modal = useModal({ size: "xl" });

  const result = useMemo(
    () =>
      stack?.split("\\n").map((v, idx) => (
        <Text my="xs" inherit key={idx}>
          {v}
        </Text>
      )),
    [stack]
  );

  return (
    <Modal title="Stack traceback">
      <ScrollArea>
        <pre>
          <Code>{result}</Code>
        </pre>
      </ScrollArea>
    </Modal>
  );
};

export default withModal(SystemLogModal, "system-log");
