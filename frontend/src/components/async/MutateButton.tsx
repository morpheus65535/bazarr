import { Button, ButtonProps } from "@mantine/core";
import { useCallback, useState } from "react";
import { UseMutationResult } from "react-query";

type MutateButtonProps<DATA, VAR> = Omit<
  ButtonProps,
  "onClick" | "loading" | "color"
> & {
  mutation: UseMutationResult<DATA, unknown, VAR>;
  args: () => VAR | null;
  onSuccess?: (args: DATA) => void;
  onError?: () => void;
  noReset?: boolean;
};

function MutateButton<DATA, VAR>({
  mutation,
  noReset,
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
