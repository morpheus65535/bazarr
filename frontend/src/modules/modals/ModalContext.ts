import { createContext, Dispatch, SetStateAction } from "react";

export interface ModalData {
  key: string;
  closeable: boolean;
  size: "sm" | "lg" | "xl" | undefined;
}

export type ModalSetter = {
  [P in keyof Omit<ModalData, "key">]: Dispatch<SetStateAction<ModalData[P]>>;
};

export const ModalDataContext = createContext<ModalData | null>(null);
export const ModalSetterContext = createContext<ModalSetter | null>(null);
