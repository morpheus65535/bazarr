import React, { FunctionComponent, useMemo } from "react";
import { useStackState } from "rooks";

interface Modal {
  key: string;
  payload: any;
}

interface ModalControl {
  push: (modal: Modal) => void;
  peek: () => Modal | undefined;
  pop: () => Modal | undefined;
}

interface ModalContextType {
  modals: Modal[];
  control: ModalControl;
}

export const ModalContext = React.createContext<ModalContextType>({
  modals: [],
  control: {
    push: () => {
      throw new Error("Unimplemented");
    },
    pop: () => {
      throw new Error("Unimplemented");
    },
    peek: () => {
      throw new Error("Unimplemented");
    },
  },
});

const ModalProvider: FunctionComponent = ({ children }) => {
  const [stack, { push, pop, peek }] = useStackState([]);

  const context = useMemo<ModalContextType>(
    () => ({ modals: stack, control: { push, pop, peek } }),
    [stack, push, pop, peek]
  );

  return (
    <ModalContext.Provider value={context}>{children}</ModalContext.Provider>
  );
};

export default ModalProvider;
