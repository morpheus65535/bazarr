import { FunctionComponent, PropsWithChildren, useMemo } from "react";
import { em } from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";
import {
  ModalsProvider as MantineModalsProvider,
  ModalsProviderProps as MantineModalsProviderProps,
} from "@mantine/modals";
import { ModalComponent, StaticModals } from "./WithModal";

const ModalsProvider: FunctionComponent<PropsWithChildren> = ({ children }) => {
  const isMobile = useMediaQuery(`(max-width: ${em(750)})`);

  // On phones, render modals full-screen so their content isn't cramped into a
  // small centered box.
  const modalProps = useMemo<MantineModalsProviderProps["modalProps"]>(
    () => ({
      centered: true,
      fullScreen: isMobile,
    }),
    [isMobile],
  );

  const modals = useMemo(
    () =>
      StaticModals.reduce<Record<string, ModalComponent>>((prev, curr) => {
        prev[curr.modalKey] = curr;
        return prev;
      }, {}),
    [],
  );

  return (
    <MantineModalsProvider modalProps={modalProps} modals={modals}>
      {children}
    </MantineModalsProvider>
  );
};

export default ModalsProvider;
