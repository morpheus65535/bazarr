import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";
import { Popover } from "@mantine/core";
import { useHover } from "@mantine/hooks";
import { FunctionComponent } from "react";

interface MessageIconProps extends FontAwesomeIconProps {
  messages: string[];
}

const MessageIcon: FunctionComponent<MessageIconProps> = (props) => {
  const { messages, ...iconProps } = props;

  const { hovered, ref } = useHover();

  return (
    <Popover
      disabled={messages.length === 0}
      target={
        <FontAwesomeIcon forwardedRef={ref} {...iconProps}></FontAwesomeIcon>
      }
      opened={hovered}
    >
      {messages.map((m) => (
        <li key={m}>{m}</li>
      ))}
    </Popover>
  );
};

export default MessageIcon;
