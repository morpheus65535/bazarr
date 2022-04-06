import { createStyles, Group } from "@mantine/core";
import { FunctionComponent } from "react";
import ContentHeaderButton, { ContentHeaderAsyncButton } from "./Button";

const useStyles = createStyles((theme) => ({
  group: {
    backgroundColor:
      theme.colorScheme === "light" ? theme.colors.dark[0] : undefined,
  },
}));

declare type Header = FunctionComponent & {
  Button: typeof ContentHeaderButton;
  AsyncButton: typeof ContentHeaderAsyncButton;
};

export const ContentHeader: Header = ({ children }) => {
  const { classes } = useStyles();
  return (
    <Group p={12} position="apart" className={classes.group}>
      {children}
    </Group>
  );
};

ContentHeader.Button = ContentHeaderButton;
ContentHeader.AsyncButton = ContentHeaderAsyncButton;

export default ContentHeader;
