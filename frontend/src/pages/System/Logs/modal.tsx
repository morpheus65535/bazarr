import { useModal, usePayload, withModal } from "@/modules/modals";
import { FunctionComponent, useMemo } from "react";

const SystemLogModal: FunctionComponent = () => {
  const stack = usePayload<string>();

  const Modal = useModal();

  const result = useMemo(
    () =>
      stack?.split("\\n").map((v, idx) => (
        <p key={idx} className="text-nowrap my-1">
          {v}
        </p>
      )),
    [stack]
  );

  return (
    <Modal title="Stack traceback">
      <pre>
        <code>{result}</code>
      </pre>
    </Modal>
  );
};

export default withModal(SystemLogModal, "system-log");
