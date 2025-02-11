import React, {
  createContext,
  FunctionComponent,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { matchPath, NavLink, RouteObject, useLocation } from "react-router";
import {
  Anchor,
  AppShell,
  Badge,
  Collapse,
  Divider,
  Group,
  Stack,
  Text,
  useComputedColorScheme,
  useMantineColorScheme,
} from "@mantine/core";
import { useHover } from "@mantine/hooks";
import {
  faHeart,
  faMoon,
  faSun,
  IconDefinition,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import clsx from "clsx";
import { Action } from "@/components";
import { useNavbar } from "@/contexts/Navbar";
import { useRouteItems } from "@/Router";
import { CustomRouteObject, Route } from "@/Router/type";
import { BuildKey, pathJoin } from "@/utilities";
import { LOG } from "@/utilities/console";
import styles from "./Navbar.module.scss";

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
  const [selection, select] = useState<string | null>(null);

  const { toggleColorScheme } = useMantineColorScheme();
  const computedColorScheme = useComputedColorScheme("light");

  const dark = computedColorScheme === "dark";

  const routes = useRouteItems();

  const { pathname } = useLocation();
  useEffect(() => {
    select(null);
  }, [pathname]);

  return (
    <AppShell.Navbar p="xs" className={styles.nav}>
      <Selection.Provider value={{ selection, select }}>
        <AppShell.Section
          grow
          style={{ overflowY: "auto", scrollbarWidth: "none" }}
        >
          <Stack gap={0}>
            {routes.map((route, idx) => (
              <RouteItem
                key={BuildKey("nav", idx)}
                parent="/"
                route={route}
              ></RouteItem>
            ))}
          </Stack>
        </AppShell.Section>
        <Divider></Divider>
        <AppShell.Section mt="xs">
          <Group gap="xs">
            <Action
              label="Change Theme"
              c={dark ? "yellow" : "indigo"}
              onClick={() => toggleColorScheme()}
              icon={dark ? faSun : faMoon}
            ></Action>
            <Anchor
              href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url"
              target="_blank"
            >
              <Action label="Donate" icon={faHeart} c="red"></Action>
            </Anchor>
          </Group>
        </AppShell.Section>
      </Selection.Provider>
    </AppShell.Navbar>
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
      <Stack gap={0}>
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
        <Stack gap={0}>
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
          clsx(styles.anchor, {
            [styles.active]: isActive,
            [styles.hover]: hovered,
          }),
        )
      }
    >
      <Text
        ref={ref}
        inline
        p="xs"
        size="sm"
        fw={primary ? "bold" : "normal"}
        className={styles.text}
        span
      >
        {icon && (
          <FontAwesomeIcon
            className={styles.icon}
            icon={icon}
          ></FontAwesomeIcon>
        )}
        {name}
        {!shouldHideBadge && (
          <Badge className={styles.badge} radius="xs">
            {badge}
          </Badge>
        )}
      </Text>
    </NavLink>
  );
};

export default AppNavbar;
