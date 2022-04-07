/* eslint-disable @typescript-eslint/ban-types */

import { ContextModalProps } from "@mantine/modals";
import { createContext, FunctionComponent } from "react";

export type ModalComponent<P extends Record<string, unknown> = {}> =
  FunctionComponent<ContextModalProps<P>> & {
    modalKey: string;
  };

export const StaticModals: ModalComponent[] = [];

export const ModalIdContext = createContext<string | null>(null);

export default function withModal<T extends {}>(
  Content: FunctionComponent<T>,
  key: string
) {
  const Comp: ModalComponent<T> = (props) => {
    const { id, innerProps } = props;

    return (
      <ModalIdContext.Provider value={id}>
        <Content {...innerProps}></Content>
      </ModalIdContext.Provider>
    );
  };
  Comp.modalKey = key;

  StaticModals.push(Comp as ModalComponent);
  return Comp;
}
