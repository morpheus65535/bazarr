import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "@mantine/core";
import { FunctionComponent, MouseEvent } from "react";

export const ActionBadge: FunctionComponent<{
  icon: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}> = ({ icon, onClick }) => {
  return (
    <Button className="mx-1 p-1" onClick={onClick}>
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    </Button>
  );
};

// interface ActionButtonProps extends ActionButtonItemProps {
//   disabled?: boolean;
//   destructive?: boolean;
//   color?: string;
//   onClick?: (e: MouseEvent) => void;
//   className?: string;
//   size?: ButtonProps["size"];
// }

// export const ActionButton: FunctionComponent<ActionButtonProps> = ({
//   onClick,
//   destructive,
//   disabled,
//   color,
//   className,
//   size,
//   ...other
// }) => {
//   return (
//     <Button
//       disabled={other.loading || disabled}
//       size={size ?? "sm"}
//       color={color ?? "light"}
//       className={`text-nowrap ${className ?? ""}`}
//       onClick={onClick}
//     >
//       <ActionButtonItem {...other}></ActionButtonItem>
//     </Button>
//   );
// };

// interface ActionButtonItemProps {
//   loading?: boolean;
//   alwaysShowText?: boolean;
//   icon: IconDefinition;
//   children?: string;
// }

// export const ActionButtonItem: FunctionComponent<ActionButtonItemProps> = ({
//   icon,
//   children,
//   loading,
//   alwaysShowText,
// }) => {
//   const showText = alwaysShowText === true || loading !== true;
//   return (
//     <>
//       <FontAwesomeIcon
//         style={{ width: "1rem" }}
//         icon={loading ? faCircleNotch : icon}
//         spin={loading}
//       ></FontAwesomeIcon>
//       {children && showText ? (
//         <span className="ml-2 font-weight-bold">{children}</span>
//       ) : null}
//     </>
//   );
// };
