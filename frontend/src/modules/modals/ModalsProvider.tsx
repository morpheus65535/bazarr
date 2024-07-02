import { FunctionComponent, PropsWithChildren, useMemo } from "react";
import {
  ModalsProvider as MantineModalsProvider,
  ModalsProviderProps as MantineModalsProviderProps,
} from "@mantine/modals";
import { ModalComponent, StaticModals } from "./WithModal";

const DefaultModalProps: MantineModalsProviderProps["modalProps"] = {
  centered: true,
  styles: {
    // modals: {
    //   maxWidth: "100%",
    // },
  },
};

const ModalsProvider: FunctionComponent<PropsWithChildren> = ({ children }) => {
  const modals = useMemo(
    () =>
      StaticModals.reduce<Record<string, ModalComponent>>((prev, curr) => {
        prev[curr.modalKey] = curr;
        return prev;
      }, {}),
    [],
  );

  return (
    <MantineModalsProvider modalProps={DefaultModalProps} modals={modals}>
      {children}
    </MantineModalsProvider>
  );
};

export default ModalsProvider;
