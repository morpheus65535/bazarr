import { MantineThemeOverride } from "@mantine/core";

const Theme: MantineThemeOverride = {
  fontFamily: [
    "Roboto",
    "open sans",
    "Helvetica Neue",
    "Helvetica",
    "Arial",
    "sans-serif",
  ],
  colors: {
    brand: [
      "#F8F0FC",
      "#F3D9FA",
      "#EEBEFA",
      "#E599F7",
      "#DA77F2",
      "#CC5DE8",
      "#BE4BDB",
      "#AE3EC9",
      "#9C36B5",
      "#862E9C",
    ],
  },
  primaryColor: "brand",
};

export default Theme;
