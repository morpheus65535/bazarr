import {
  ComponentProps,
  FunctionComponent,
  JSX,
  PropsWithChildren,
  useCallback,
  useState,
} from "react";
import { Button, ButtonProps, Text } from "@mantine/core";
import { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

type ToolboxButtonProps = Omit<ButtonProps, "color" | "variant" | "leftIcon"> &
  Omit<ComponentProps<"button">, "ref"> & {
    icon: IconDefinition;
    children: string;
  };

const ToolboxButton: FunctionComponent<ToolboxButtonProps> = ({
  icon,
  children,
  ...props
}) => {
  return (
    <Button
      color="dark"
      variant="subtle"
      leftSection={<FontAwesomeIcon icon={icon}></FontAwesomeIcon>}
      {...props}
    >
      <Text size="xs">{children}</Text>
    </Button>
  );
};

type ToolboxMutateButtonProps<R, T extends () => Promise<R>> = {
  promise: T;
  onSuccess?: (item: R) => void;
} & Omit<ToolboxButtonProps, "onClick" | "loading">;

export function ToolboxMutateButton<R, T extends () => Promise<R>>(
  props: PropsWithChildren<ToolboxMutateButtonProps<R, T>>,
): JSX.Element {
  const { promise, onSuccess, ...button } = props;

  const [loading, setLoading] = useState(false);

  const click = useCallback(() => {
    setLoading(true);
    promise().then((val) => {
      setLoading(false);
      onSuccess && onSuccess(val);
    });
  }, [onSuccess, promise]);

  return (
    <ToolboxButton
      loading={loading}
      onClick={click}
      {...button}
    ></ToolboxButton>
  );
}

export default ToolboxButton;
