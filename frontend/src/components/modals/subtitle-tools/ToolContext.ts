import { createContext, useContext } from "react";

export type ProcessSubtitleType = (
  action: string,
  override?: Partial<FormType.ModifySubtitle>
) => void;

export const ProcessSubtitleContext = createContext<ProcessSubtitleType>(() => {
  throw new Error("ProcessSubtitleContext not initialized");
});

export function useProcess() {
  return useContext(ProcessSubtitleContext);
}
