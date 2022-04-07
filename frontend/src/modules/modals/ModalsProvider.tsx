import { ModalsProvider as MantineModalsProvider } from "@mantine/modals";
import { FunctionComponent, useMemo } from "react";
import { ModalComponent, StaticModals } from "./WithModal";

const ModalsProvider: FunctionComponent = ({ children }) => {
  const modals = useMemo(
    () =>
      StaticModals.reduce<Record<string, ModalComponent>>((prev, curr) => {
        prev[curr.modalKey] = curr;
        return prev;
      }, {}),
    []
  );

  return (
    <MantineModalsProvider modals={modals}>{children}</MantineModalsProvider>
  );
};

export default ModalsProvider;
