import { useCallback, useState } from "react";
import { Button, ButtonProps } from "@mantine/core";
import { UseMutationResult } from "@tanstack/react-query";

type MutateButtonProps<DATA, VAR> = Omit<
  ButtonProps,
  "onClick" | "loading" | "color"
> & {
  mutation: UseMutationResult<DATA, unknown, VAR>;
  args: () => VAR | null;
  onSuccess?: (args: DATA) => void;
  onError?: () => void;
};

function MutateButton<DATA, VAR>({
  mutation,
  onSuccess,
  onError,
  args,
  ...props
}: MutateButtonProps<DATA, VAR>) {
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

  return <Button {...props} loading={isLoading} onClick={onClick}></Button>;
}

export default MutateButton;
