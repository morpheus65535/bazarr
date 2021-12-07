import { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { faSpinner } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  MouseEvent,
  PropsWithChildren,
  useCallback,
  useState,
} from "react";
import { Button } from "react-bootstrap";

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
      variant="dark"
      className="py-1"
      disabled={disabled || updating}
      onClick={onClick}
    >
      <div className="d-flex flex-column text-nowrap">
        <FontAwesomeIcon
          className="mx-auto my-1"
          icon={displayIcon}
          spin={updating}
        ></FontAwesomeIcon>
        <span className="align-bottom text-themecolor small text-center">
          {children}
        </span>
      </div>
    </Button>
  );
};

type CHAsyncButtonProps<T extends () => Promise<any>> = {
  promise: T;
  onSuccess?: (item: PromiseType<ReturnType<T>>) => void;
} & Omit<CHButtonProps, "updating" | "updatingIcon" | "onClick">;

export function ContentHeaderAsyncButton<T extends () => Promise<any>>(
  props: PropsWithChildren<CHAsyncButtonProps<T>>
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
