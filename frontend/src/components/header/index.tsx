import { createStyles, Group } from "@mantine/core";
import { FunctionComponent } from "react";
import ContentHeaderButton, { ContentHeaderAsyncButton } from "./Button";
import ContentHeaderGroup from "./Group";

const useStyles = createStyles((theme) => ({
  group: {
    backgroundColor: theme.colors.gray[4],
  },
}));

declare type Header = FunctionComponent & {
  Button: typeof ContentHeaderButton;
  AsyncButton: typeof ContentHeaderAsyncButton;
  Group: typeof ContentHeaderGroup;
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
ContentHeader.Group = ContentHeaderGroup;
ContentHeader.AsyncButton = ContentHeaderAsyncButton;

export default ContentHeader;
