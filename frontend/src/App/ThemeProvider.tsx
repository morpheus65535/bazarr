import { FunctionComponent, PropsWithChildren } from "react";
import {
  ActionIcon,
  Badge,
  Button,
  createTheme,
  CSSVariablesResolver,
  MantineColorsTuple,
  MantineProvider,
  Pagination,
  virtualColor,
} from "@mantine/core";
import ThemeLoader from "@/App/ThemeLoader";
import "@mantine/core/styles.layer.css";
import "@mantine/notifications/styles.layer.css";
import "@mantine/spotlight/styles.layer.css";
import styleVars from "@/assets/_variables.module.scss";
import actionIconClasses from "@/assets/action_icon.module.scss";
import badgeClasses from "@/assets/badge.module.scss";
import buttonClasses from "@/assets/button.module.scss";
import paginationClasses from "@/assets/pagination.module.scss";

// Build a 10-shade Mantine color tuple from the `color<Name>0..9` values
// exported by _variables.module.scss.
const buildColor = (prefix: string): MantineColorsTuple =>
  Array.from(
    { length: 10 },
    (_, i) => styleVars[`${prefix}${i}`],
  ) as unknown as MantineColorsTuple;

const themeProvider = createTheme({
  fontFamily: "Roboto, open sans, Helvetica Neue, Helvetica, Arial, sans-serif",
  colors: {
    brand: buildColor("colorBrand"),
    // Semantic tokens — use these instead of raw palette names so intent is
    // explicit and both color schemes stay consistent.
    danger: buildColor("colorDanger"),
    success: buildColor("colorSuccess"),
    warning: buildColor("colorWarning"),
    info: buildColor("colorInfo"),
    // Neutral/secondary automatically swaps per color scheme.
    secondary: virtualColor({
      name: "secondary",
      light: "gray",
      dark: "dark",
    }),
  },
  primaryColor: "brand",
  defaultRadius: "sm",
  components: {
    ActionIcon: ActionIcon.extend({
      classNames: actionIconClasses,
    }),
    Badge: Badge.extend({
      classNames: badgeClasses,
    }),
    Button: Button.extend({
      classNames: buttonClasses,
    }),
    Pagination: Pagination.extend({
      classNames: paginationClasses,
    }),
  },
});

// Mantine's default light `dimmed` (gray-6) fails WCAG AA on white/near-white
// backgrounds. Bump it a shade for readability; dark mode keeps the default.
const resolveCssVariables: CSSVariablesResolver = () => ({
  variables: {},
  light: {
    "--mantine-color-dimmed": "var(--mantine-color-gray-7)",
  },
  dark: {},
});

const ThemeProvider: FunctionComponent<PropsWithChildren> = ({ children }) => {
  return (
    <MantineProvider
      theme={themeProvider}
      defaultColorScheme="auto"
      cssVariablesResolver={resolveCssVariables}
    >
      <ThemeLoader />
      {children}
    </MantineProvider>
  );
};

export default ThemeProvider;
