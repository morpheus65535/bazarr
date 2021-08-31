import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";

interface Modal {
  key: string;
  payload: any;
}

interface ModalControl {
  push: (modal: Modal) => void;
  peek: () => Modal | undefined;
  pop: (key: string | undefined) => void;
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
  const [stack, setStack] = useState<Modal[]>([]);

  const push = useCallback<ModalControl["push"]>((model) => {
    setStack((old) => {
      return [...old, model];
    });
  }, []);

  const pop = useCallback<ModalControl["pop"]>((key) => {
    setStack((old) => {
      if (old.length === 0) {
        return [];
      }

      if (key === undefined) {
        const newOld = old;
        newOld.pop();
        return newOld;
      }

      // find key
      const index = old.findIndex((v) => v.key === key);
      if (index !== -1) {
        return old.slice(0, index);
      } else {
        return old;
      }
    });
  }, []);

  const peek = useCallback<ModalControl["peek"]>(() => {
    return stack.length > 0 ? stack[stack.length - 1] : undefined;
  }, [stack]);

  const context = useMemo<ModalContextType>(
    () => ({ modals: stack, control: { push, pop, peek } }),
    [stack, push, pop, peek]
  );

  return (
    <ModalContext.Provider value={context}>{children}</ModalContext.Provider>
  );
};

export default ModalProvider;
