import { Action } from "@/components";
import { Layout } from "@/constants";
import { useNavbar } from "@/contexts/Navbar";
import { useRouteItems } from "@/Router";
import { CustomRouteObject, Route } from "@/Router/type";
import { BuildKey, pathJoin } from "@/utilities";
import { LOG } from "@/utilities/console";
import {
  faHeart,
  faMoon,
  faSun,
  IconDefinition,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Anchor,
  Badge,
  Collapse,
  createStyles,
  Divider,
  Group,
  Navbar as MantineNavbar,
  Stack,
  Text,
  useMantineColorScheme,
} from "@mantine/core";
import { useHover } from "@mantine/hooks";
import clsx from "clsx";
import {
  createContext,
  FunctionComponent,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { matchPath, NavLink, RouteObject, useLocation } from "react-router-dom";

const Selection = createContext<{
  selection: string | null;
  select: (path: string | null) => void;
}>({
  selection: null,
  select: () => {
    LOG("error", "Selection context not initialized");
  },
});

function useSelection() {
  return useContext(Selection);
}

function useBadgeValue(route: Route.Item) {
  const { badge, children } = route;
  return useMemo(() => {
    if (typeof badge === "string") {
      return badge;
    }

    let value = badge ?? 0;

    if (children === undefined) {
      return value;
    }

    value +=
      children.reduce((acc, child: Route.Item) => {
        const childBadgeValue = child.badge;
        if (typeof childBadgeValue === "number" && child.hidden !== true) {
          return acc + childBadgeValue;
        }
        return acc;
      }, 0) ?? 0;

    return value === 0 ? undefined : value;
  }, [badge, children]);
}

function useIsActive(parent: string, route: RouteObject) {
  const { path, children } = route;

  const { pathname } = useLocation();
  const root = useMemo(() => pathJoin(parent, path ?? ""), [parent, path]);

  const paths = useMemo(
    () => [root, ...(children?.map((v) => pathJoin(root, v.path ?? "")) ?? [])],
    [root, children],
  );

  const selection = useSelection().selection;
  return useMemo(
    () =>
      selection?.includes(root) ||
      paths.some((path) => matchPath(path, pathname)),
    [pathname, paths, root, selection],
  );
}

const AppNavbar: FunctionComponent = () => {
  const { showed } = useNavbar();
  const [selection, select] = useState<string | null>(null);

  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const dark = colorScheme === "dark";

  const routes = useRouteItems();

  const { pathname } = useLocation();
  useEffect(() => {
    select(null);
  }, [pathname]);

  return (
    <MantineNavbar
      p="xs"
      hiddenBreakpoint={Layout.MOBILE_BREAKPOINT}
      hidden={!showed}
      width={{ [Layout.MOBILE_BREAKPOINT]: Layout.NAVBAR_WIDTH }}
      styles={(theme) => ({
        root: {
          backgroundColor:
            theme.colorScheme === "light"
              ? theme.colors.gray[2]
              : theme.colors.dark[6],
        },
      })}
    >
      <Selection.Provider value={{ selection, select }}>
        <MantineNavbar.Section grow>
          <Stack spacing={0}>
            {routes.map((route, idx) => (
              <RouteItem
                key={BuildKey("nav", idx)}
                parent="/"
                route={route}
              ></RouteItem>
            ))}
          </Stack>
        </MantineNavbar.Section>
        <Divider></Divider>
        <MantineNavbar.Section mt="xs">
          <Group spacing="xs">
            <Action
              label="Change Theme"
              color={dark ? "yellow" : "indigo"}
              variant="subtle"
              onClick={() => toggleColorScheme()}
              icon={dark ? faSun : faMoon}
            ></Action>
            <Anchor
              href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url"
              target="_blank"
            >
              <Action
                label="Donate"
                icon={faHeart}
                variant="subtle"
                color="red"
              ></Action>
            </Anchor>
          </Group>
        </MantineNavbar.Section>
      </Selection.Provider>
    </MantineNavbar>
  );
};

const RouteItem: FunctionComponent<{
  route: CustomRouteObject;
  parent: string;
}> = ({ route, parent }) => {
  const { children, name, path, icon, hidden, element } = route;

  const { select } = useSelection();

  const link = useMemo(() => pathJoin(parent, path ?? ""), [parent, path]);

  const badge = useBadgeValue(route);

  const isOpen = useIsActive(parent, route);

  // Ignore path if it is using match
  if (hidden === true || path === undefined || path.includes(":")) {
    return null;
  }

  if (children !== undefined) {
    const elements = (
      <Stack spacing={0}>
        {children.map((child, idx) => (
          <RouteItem
            parent={link}
            key={BuildKey(link, "nav", idx)}
            route={child}
          ></RouteItem>
        ))}
      </Stack>
    );

    if (name) {
      return (
        <Stack spacing={0}>
          <NavbarItem
            primary
            name={name}
            link={link}
            icon={icon}
            badge={badge}
            onClick={(event) => {
              LOG("info", "clicked", link);

              const validated =
                element !== undefined ||
                children?.find((v) => v.index === true) !== undefined;

              if (!validated) {
                event.preventDefault();
              }

              if (isOpen) {
                select(null);
              } else {
                select(link);
              }
            }}
          ></NavbarItem>
          <Collapse hidden={children.length === 0} in={isOpen}>
            {elements}
          </Collapse>
        </Stack>
      );
    } else {
      return elements;
    }
  } else {
    return (
      <NavbarItem
        name={name ?? link}
        link={link}
        icon={icon}
        badge={badge}
      ></NavbarItem>
    );
  }
};

const useStyles = createStyles((theme) => {
  const borderColor =
    theme.colorScheme === "light" ? theme.colors.gray[5] : theme.colors.dark[4];

  const activeBorderColor =
    theme.colorScheme === "light"
      ? theme.colors.brand[4]
      : theme.colors.brand[8];

  const activeBackgroundColor =
    theme.colorScheme === "light" ? theme.colors.gray[1] : theme.colors.dark[8];

  const hoverBackgroundColor =
    theme.colorScheme === "light" ? theme.colors.gray[0] : theme.colors.dark[7];

  const textColor =
    theme.colorScheme === "light" ? theme.colors.gray[8] : theme.colors.gray[5];

  return {
    text: {
      display: "inline-flex",
      alignItems: "center",
      width: "100%",
      color: textColor,
    },
    anchor: {
      textDecoration: "none",
      borderLeft: `2px solid ${borderColor}`,
    },
    active: {
      backgroundColor: activeBackgroundColor,
      borderLeft: `2px solid ${activeBorderColor}`,
      boxShadow: theme.shadows.xs,
    },
    hover: {
      backgroundColor: hoverBackgroundColor,
    },
    icon: { width: "1.4rem", marginRight: theme.spacing.xs },
    badge: {
      marginLeft: "auto",
      textDecoration: "none",
      boxShadow: theme.shadows.xs,
      color: textColor,
    },
  };
});

interface NavbarItemProps {
  name: string;
  link: string;
  icon?: IconDefinition;
  badge?: number | string;
  primary?: boolean;
  onClick?: (event: React.MouseEvent<HTMLAnchorElement>) => void;
}

const NavbarItem: FunctionComponent<NavbarItemProps> = ({
  icon,
  link,
  name,
  badge,
  onClick,
  primary = false,
}) => {
  const { classes } = useStyles();

  const { show } = useNavbar();

  const { ref, hovered } = useHover();

  const shouldHideBadge = useMemo(() => {
    if (typeof badge === "number") {
      return badge === 0;
    } else if (typeof badge === "string") {
      return badge.length === 0;
    }

    return true;
  }, [badge]);

  return (
    <NavLink
      to={link}
      onClick={(event: React.MouseEvent<HTMLAnchorElement>) => {
        onClick?.(event);
        if (!event.isDefaultPrevented()) {
          show(false);
        }
      }}
      className={({ isActive }) =>
        clsx(
          clsx(classes.anchor, {
            [classes.active]: isActive,
            [classes.hover]: hovered,
          }),
        )
      }
    >
      <Text
        ref={ref}
        inline
        p="xs"
        size="sm"
        weight={primary ? "bold" : "normal"}
        className={classes.text}
      >
        {icon && (
          <FontAwesomeIcon
            className={classes.icon}
            icon={icon}
          ></FontAwesomeIcon>
        )}
        {name}
        {shouldHideBadge === false && (
          <Badge className={classes.badge} radius="xs">
            {badge}
          </Badge>
        )}
      </Text>
    </NavLink>
  );
};

export default AppNavbar;
