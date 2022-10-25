import {
  createContext,
  FunctionComponent,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";
import { enabledLanguageKey, languageProfileKey } from "../keys";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type HookType = (value: any) => unknown;

export type SubmitHookType = {
  [key: string]: HookType;
};

export type SubmitHookModifierType = {
  add: (key: string, fn: HookType) => void;
  remove: (key: string) => void;
  invoke: (settings: LooseObject) => void;
};

const SubmitHooksContext = createContext<SubmitHookModifierType | null>(null);

type SubmitHooksProviderProps = {
  value: SubmitHookModifierType;
};

export const SubmitHooksProvider: FunctionComponent<
  SubmitHooksProviderProps
> = ({ value, children }) => {
  return (
    <SubmitHooksContext.Provider value={value}>
      {children}
    </SubmitHooksContext.Provider>
  );
};

export function useSubmitHooks() {
  const context = useContext(SubmitHooksContext);

  if (context === null) {
    throw new Error(
      "useSubmitHooksModifier must be used within a SubmitHooksProvider"
    );
  }

  return context;
}

export function useSubmitHooksSource(): SubmitHookModifierType {
  const [submitHooks, setSubmitHooks] = useState<SubmitHookType>({
    [languageProfileKey]: (value) => JSON.stringify(value),
    [enabledLanguageKey]: (value: Language.Info[]) => value.map((v) => v.code2),
  });
  const hooksRef = useRef(submitHooks);

  const invokeHooks = useCallback((settings: LooseObject) => {
    const hooks = hooksRef.current;
    for (const key in settings) {
      if (key in hooks) {
        const value = settings[key];
        const fn = hooks[key];
        settings[key] = fn(value);
      }
    }
  }, []);

  const addHook = useCallback(
    (key: string, fn: (value: unknown) => unknown) => {
      setSubmitHooks((hooks) => ({ ...hooks, [key]: fn }));
    },
    []
  );

  const removeHook = useCallback((key: string) => {
    setSubmitHooks((hooks) => {
      const newHooks = { ...hooks };
      delete newHooks[key];

      return newHooks;
    });
  }, []);

  return useMemo(
    () => ({
      add: addHook,
      remove: removeHook,
      invoke: invokeHooks,
    }),
    [addHook, invokeHooks, removeHook]
  );
}
