import React, { FunctionComponent, useMemo } from "react";
import { BaseModal, BaseModalProps, useModalPayload } from "../../components";

interface Props extends BaseModalProps {}

const SystemLogModal: FunctionComponent<Props> = ({ ...modal }) => {
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
        <code className="zmdi-language-python-alt">{result}</code>
      </pre>
    </BaseModal>
  );
};

export default SystemLogModal;
