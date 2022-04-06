import { createStyles, Group } from "@mantine/core";
import { FunctionComponent } from "react";
import ToolboxButton, { ToolboxMutateButton } from "./Button";

const useStyles = createStyles((theme) => ({
  group: {
    backgroundColor:
      theme.colorScheme === "light" ? theme.colors.dark[1] : undefined,
  },
}));

declare type ToolboxComp = FunctionComponent & {
  Button: typeof ToolboxButton;
  MutateButton: typeof ToolboxMutateButton;
};

export const Toolbox: ToolboxComp = ({ children }) => {
  const { classes } = useStyles();
  return (
    <Group p={12} position="apart" className={classes.group}>
      {children}
    </Group>
  );
};

Toolbox.Button = ToolboxButton;
Toolbox.MutateButton = ToolboxMutateButton;

export default Toolbox;
