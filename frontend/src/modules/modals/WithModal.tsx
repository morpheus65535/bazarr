import { FunctionComponent, useMemo, useState } from "react";
import {
  ModalData,
  ModalDataContext,
  ModalSetter,
  ModalSetterContext,
} from "./ModalContext";
import ModalWrapper from "./ModalWrapper";

export interface ModalProps {}

export type ModalComponent<P> = FunctionComponent<P> & {
  modalKey: string;
};

export default function withModal<T>(
  Content: FunctionComponent<T>,
  key: string
) {
  const Comp: ModalComponent<T> = (props: ModalProps & T) => {
    const [closeable, setCloseable] = useState(true);
    const [size, setSize] = useState<ModalData["size"]>(undefined);
    const data: ModalData = useMemo(
      () => ({
        key,
        size,
        closeable,
      }),
      [closeable, size]
    );

    const setter: ModalSetter = useMemo(
      () => ({
        closeable: setCloseable,
        size: setSize,
      }),
      []
    );

    return (
      <ModalDataContext.Provider value={data}>
        <ModalSetterContext.Provider value={setter}>
          <ModalWrapper>
            <Content {...props}></Content>
          </ModalWrapper>
        </ModalSetterContext.Provider>
      </ModalDataContext.Provider>
    );
  };
  Comp.modalKey = key;
  return Comp;
}
