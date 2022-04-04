import { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { faSpinner } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button, Text } from "@mantine/core";
import {
  FunctionComponent,
  MouseEvent,
  PropsWithChildren,
  useCallback,
  useState,
} from "react";

interface CHButtonProps {
  disabled?: boolean;
  hidden?: boolean;
  icon: IconDefinition;
  updating?: boolean;
  updatingIcon?: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}

const ContentHeaderButton: FunctionComponent<CHButtonProps> = (props) => {
  const { children, icon, disabled, updating, updatingIcon, onClick } = props;

  let displayIcon = icon;
  if (updating) {
    displayIcon = updatingIcon ? updatingIcon : faSpinner;
  }

  return (
    <Button
      color="dark"
      variant="subtle"
      disabled={disabled || updating}
      onClick={onClick}
      leftIcon={
        <FontAwesomeIcon icon={displayIcon} spin={updating}></FontAwesomeIcon>
      }
    >
      <Text size="xs">{children}</Text>
    </Button>
  );
};

type CHAsyncButtonProps<R, T extends () => Promise<R>> = {
  promise: T;
  onSuccess?: (item: R) => void;
} & Omit<CHButtonProps, "updating" | "updatingIcon" | "onClick">;

export function ContentHeaderAsyncButton<R, T extends () => Promise<R>>(
  props: PropsWithChildren<CHAsyncButtonProps<R, T>>
): JSX.Element {
  const { promise, onSuccess, ...button } = props;

  const [updating, setUpdate] = useState(false);

  const click = useCallback(() => {
    setUpdate(true);
    promise().then((val) => {
      setUpdate(false);
      onSuccess && onSuccess(val);
    });
  }, [onSuccess, promise]);

  return (
    <ContentHeaderButton
      updating={updating}
      onClick={click}
      {...button}
    ></ContentHeaderButton>
  );
}

export default ContentHeaderButton;
