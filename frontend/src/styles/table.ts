import { createStyles } from "@mantine/core";

export const useTableStyles = createStyles((theme) => ({
  primary: {
    display: "inline-block",
    [theme.fn.smallerThan("sm")]: {
      minWidth: "12rem",
    },
  },
  noWrap: {
    whiteSpace: "nowrap",
  },
  select: {
    display: "inline-block",
    [theme.fn.smallerThan("sm")]: {
      minWidth: "10rem",
    },
  },
}));
