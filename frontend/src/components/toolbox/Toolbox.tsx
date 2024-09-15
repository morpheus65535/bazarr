import { FunctionComponent, PropsWithChildren } from "react";
import { Group } from "@mantine/core";
import ToolboxButton, { ToolboxMutateButton } from "./Button";
import styles from "./Toolbox.module.scss";

declare type ToolboxComp = FunctionComponent<PropsWithChildren> & {
  Button: typeof ToolboxButton;
  MutateButton: typeof ToolboxMutateButton;
};

const Toolbox: ToolboxComp = ({ children }) => {
  return (
    <Group p={12} justify="space-between" className={styles.group}>
      {children}
    </Group>
  );
};

Toolbox.Button = ToolboxButton;
Toolbox.MutateButton = ToolboxMutateButton;

export default Toolbox;
