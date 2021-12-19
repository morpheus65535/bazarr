import { IconDefinition } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import clsx from "clsx";
import React, {
  createContext,
  FunctionComponent,
  useContext,
  useMemo,
  useState,
} from "react";
import {
  Badge,
  Collapse,
  Container,
  Image,
  ListGroup,
  ListGroupItem,
} from "react-bootstrap";
import { NavLink, useHistory, useRouteMatch } from "react-router-dom";
import { siteChangeSidebarVisibility } from "../@redux/actions";
import { useReduxAction, useReduxStore } from "../@redux/hooks/base";
import logo from "../@static/logo64.png";
import { useNavigationItems } from "../Navigation";
import { Navigation } from "../Navigation/nav";
import { BuildKey } from "../utilities";
import { useGotoHomepage } from "../utilities/hooks";
import s from "./style.module.scss";

const SelectionContext = createContext<{
  selection: string | null;
  select: (selection: string | null) => void;
}>({ selection: null, select: () => {} });

const Sidebar: FunctionComponent = () => {
  const open = useReduxStore((s) => s.site.showSidebar);

  const changeSidebar = useReduxAction(siteChangeSidebarVisibility);

  const goHome = useGotoHomepage();

  const [selection, setSelection] = useState<string | null>(null);

  return (
    <SelectionContext.Provider
      value={{ selection: selection, select: setSelection }}
    >
      <aside className={clsx(s["sidebar-container"], { open: open })}>
        <Container
          className={clsx(
            s["sidebar-title"],
            "d-flex",
            "align-items-center",
            "d-md-none"
          )}
        >
          <Image
            alt="brand"
            src={logo}
            width="32"
            height="32"
            onClick={goHome}
            className="cursor-pointer"
          ></Image>
        </Container>
        <SidebarNavigation></SidebarNavigation>
      </aside>
      <div
        className={clsx(s["sidebar-overlay"], { open: open })}
        onClick={() => changeSidebar(false)}
      ></div>
    </SelectionContext.Provider>
  );
};

const SidebarNavigation: FunctionComponent = () => {
  const navItems = useNavigationItems();

  return (
    <ListGroup variant="flush">
      {navItems.map((v, idx) => {
        if ("routes" in v) {
          return (
            <SidebarParent key={BuildKey(idx, v.name)} {...v}></SidebarParent>
          );
        } else {
          return (
            <SidebarChild
              parent=""
              key={BuildKey(idx, v.name)}
              {...v}
            ></SidebarChild>
          );
        }
      })}
    </ListGroup>
  );
};

const SidebarParent: FunctionComponent<Navigation.RouteWithChild> = ({
  icon,
  badge,
  name,
  path,
  routes,
  enabled,
  component,
}) => {
  const computedBadge = useMemo(() => {
    let computed = badge ?? 0;

    computed += routes.reduce((prev, curr) => {
      return prev + (curr.badge ?? 0);
    }, 0);

    return computed !== 0 ? computed : undefined;
  }, [badge, routes]);

  const enabledRoutes = useMemo(
    () => routes.filter((v) => v.enabled !== false && v.routeOnly !== true),
    [routes]
  );

  const changeSidebar = useReduxAction(siteChangeSidebarVisibility);

  const { selection, select } = useContext(SelectionContext);

  const match = useRouteMatch({ path });
  const open = match !== null || selection === path;

  const history = useHistory();

  if (enabled === false) {
    return null;
  } else if (enabledRoutes.length === 0) {
    if (component) {
      return (
        <NavLink
          activeClassName={s["active"]}
          className={clsx(
            s["sidebar-button"],
            "list-group-item",
            "list-group-item-action"
          )}
          to={path}
          onClick={() => changeSidebar(false)}
        >
          <SidebarContent
            icon={icon}
            name={name}
            badge={computedBadge}
          ></SidebarContent>
        </NavLink>
      );
    } else {
      return null;
    }
  }

  return (
    <div className={clsx(s["sidebar-collapse-box"], { [s["active"]]: open })}>
      <ListGroupItem
        action
        className={s["sidebar-button"]}
        onClick={() => {
          if (open) {
            select(null);
          } else {
            select(path);
          }
          if (component !== undefined) {
            history.push(path);
          }
        }}
      >
        <SidebarContent
          icon={icon}
          name={name}
          badge={computedBadge}
        ></SidebarContent>
      </ListGroupItem>
      <Collapse in={open}>
        <div className={s["sidebar-collapse"]}>
          {enabledRoutes.map((v, idx) => (
            <SidebarChild
              key={BuildKey(idx, v.name, "child")}
              parent={path}
              {...v}
            ></SidebarChild>
          ))}
        </div>
      </Collapse>
    </div>
  );
};

interface SidebarChildProps {
  parent: string;
}

const SidebarChild: FunctionComponent<
  SidebarChildProps & Navigation.RouteWithoutChild
> = ({ icon, name, path, badge, enabled, routeOnly, parent }) => {
  const changeSidebar = useReduxAction(siteChangeSidebarVisibility);
  const { select } = useContext(SelectionContext);

  if (enabled === false || routeOnly === true) {
    return null;
  }

  return (
    <NavLink
      activeClassName="sb-active"
      className={clsx(
        s["sidebar-button"],
        s["sb-collapse"],
        "list-group-item",
        "list-group-item-action"
      )}
      to={parent + path}
      onClick={() => {
        select(null);
        changeSidebar(false);
      }}
    >
      <SidebarContent icon={icon} name={name} badge={badge}></SidebarContent>
    </NavLink>
  );
};

const SidebarContent: FunctionComponent<{
  icon?: IconDefinition;
  name: string;
  badge?: number;
}> = ({ icon, name, badge }) => {
  return (
    <React.Fragment>
      {icon && (
        <FontAwesomeIcon
          size="1x"
          className={s["icon"]}
          icon={icon}
        ></FontAwesomeIcon>
      )}
      <span className="d-flex flex-grow-1 justify-content-between">
        {name} <Badge bg="secondary">{badge !== 0 ? badge : null}</Badge>
      </span>
    </React.Fragment>
  );
};

export default Sidebar;
