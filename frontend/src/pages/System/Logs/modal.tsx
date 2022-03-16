import { BaseModal, BaseModalProps } from "@/components";
import { usePayload } from "@/modules/redux/hooks/modal";
import { FunctionComponent, useMemo } from "react";

const SystemLogModal: FunctionComponent<BaseModalProps> = ({ ...modal }) => {
  const stack = usePayload<string>(modal.modalKey);
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
