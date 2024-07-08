/* eslint-disable @typescript-eslint/ban-types */

import { createContext, FunctionComponent } from "react";
import { ContextModalProps } from "@mantine/modals";
import { ModalSettings } from "@mantine/modals/lib/context";

export type ModalComponent<P extends Record<string, unknown> = {}> =
  FunctionComponent<ContextModalProps<P>> & {
    modalKey: string;
    settings?: ModalSettings;
  };

export const StaticModals: ModalComponent[] = [];

export const ModalIdContext = createContext<string | null>(null);

export default function withModal<T extends {}>(
  Content: FunctionComponent<T>,
  key: string,
  defaultSettings?: ModalSettings,
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
  Comp.settings = defaultSettings;

  StaticModals.push(Comp as ModalComponent);
  return Comp;
}
