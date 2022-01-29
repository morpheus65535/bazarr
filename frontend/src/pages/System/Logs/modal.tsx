import { BaseModal, BaseModalProps, useModalPayload } from "@/components";
import { FunctionComponent, useMemo } from "react";

const SystemLogModal: FunctionComponent<BaseModalProps> = ({ ...modal }) => {
  const stack = useModalPayload<string>(modal.modalKey);
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
    <BaseModal title="Stack traceback" {...modal}>
      <pre>
        <code>{result}</code>
      </pre>
    </BaseModal>
  );
};

export default SystemLogModal;
