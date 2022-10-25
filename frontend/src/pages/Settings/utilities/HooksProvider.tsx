import { LOG } from "@/utilities/console";
import {
  createContext,
  FunctionComponent,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

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

export function useSubmitHookWith(key: string, fn?: HookType) {
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const hooks = useSubmitHooks();

  useEffect(() => {
    const currentFn = fnRef.current;
    if (currentFn) {
      LOG("info", "Adding submit hook for", key);
      hooks.add(key, currentFn);
    }

    return () => {
      LOG("info", "Removing submit hook for", key);
      hooks.remove(key);
    };
  }, [key, hooks]);
}

export function useSubmitHooksSource(): SubmitHookModifierType {
  const [submitHooks, setSubmitHooks] = useState<SubmitHookType>({});
  const hooksRef = useRef(submitHooks);
  hooksRef.current = submitHooks;

  const invokeHooks = useCallback((settings: LooseObject) => {
    const hooks = hooksRef.current;
    for (const key in settings) {
      if (key in hooks) {
        LOG("info", "Running submit hook for", key, settings[key]);
        const value = settings[key];
        const fn = hooks[key];
        settings[key] = fn(value);
        LOG("info", "Finish submit hook", key, settings[key]);
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

      if (key in newHooks) {
        delete newHooks[key];
      }

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
