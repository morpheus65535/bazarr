import { useCallback, useState } from "react";
import { UseMutationResult } from "@tanstack/react-query";
import { Action } from "@/components/inputs";
import { ActionProps } from "@/components/inputs/Action";

type MutateActionProps<DATA, VAR> = Omit<
  ActionProps,
  "onClick" | "loading" | "color"
> & {
  mutation: UseMutationResult<DATA, unknown, VAR>;
  args: () => VAR | null;
  onSuccess?: (args: DATA) => void;
  onError?: () => void;
};

function MutateAction<DATA, VAR>({
  mutation,
  onSuccess,
  onError,
  args,
  ...props
}: MutateActionProps<DATA, VAR>) {
  const { mutateAsync } = mutation;

  const [isLoading, setLoading] = useState(false);

  const onClick = useCallback(async () => {
    setLoading(true);
    try {
      const argument = args();
      if (argument !== null) {
        const data = await mutateAsync(argument);
        onSuccess?.(data);
      } else {
        onError?.();
      }
    } catch (error) {
      onError?.();
    }
    setLoading(false);
  }, [args, mutateAsync, onError, onSuccess]);

  return <Action {...props} loading={isLoading} onClick={onClick}></Action>;
}

export default MutateAction;
