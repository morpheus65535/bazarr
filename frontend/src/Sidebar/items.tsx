import { IconDefinition } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useContext, useMemo } from "react";
import { Badge, Collapse, ListGroupItem } from "react-bootstrap";
import { NavLink } from "react-router-dom";
import { useSidebarKey, useUpdateSidebar } from ".";
import { SidebarToggleContext } from "../App";
import {
  BadgeProvider,
  ChildBadgeProvider,
  CollapseItemType,
  LinkItemType,
} from "./types";

export const BadgesContext = React.createContext<BadgeProvider>({});

export const LinkItem: FunctionComponent<LinkItemType> = ({
  link,
  name,
  icon,
}) => {
  const badges = useContext(BadgesContext);
  const toggle = useContext(SidebarToggleContext);

  const badgeValue = useMemo(() => {
    let badge: Nullable<number> = null;
    if (name in badges) {
      let item = badges[name];
      if (typeof item === "number") {
        badge = item;
      }
    }
    return badge;
  }, [badges, name]);

  return (
    <NavLink
      activeClassName="sb-active"
      className="list-group-item list-group-item-action sidebar-button"
      to={link}
      onClick={toggle}
    >
      <DisplayItem
        badge={badgeValue ?? undefined}
        name={name}
        icon={icon}
      ></DisplayItem>
    </NavLink>
  );
};

export const CollapseItem: FunctionComponent<CollapseItemType> = ({
  icon,
  name,
  children,
}) => {
  const badges = useContext(BadgesContext);
  const toggleSidebar = useContext(SidebarToggleContext);

  const itemKey = name.toLowerCase();

  const sidebarKey = useSidebarKey();
  const updateSidebar = useUpdateSidebar();

  const [badgeValue, childValue] = useMemo<
    [Nullable<number>, Nullable<ChildBadgeProvider>]
  >(() => {
    let badge: Nullable<number> = null;
    let child: Nullable<ChildBadgeProvider> = null;

    if (name in badges) {
      const item = badges[name];
      if (typeof item === "number") {
        badge = item;
      } else if (typeof item === "object") {
        badge = 0;
        child = item;
        for (const it in item) {
          badge += item[it];
        }
      }
    }
    return [badge, child];
  }, [badges, name]);

  const active = useMemo(() => sidebarKey === itemKey, [sidebarKey, itemKey]);

  const collapseBoxClass = useMemo(
    () => `sidebar-collapse-box ${active ? "active" : ""}`,
    [active]
  );

  return (
    <div className={collapseBoxClass}>
      <ListGroupItem
        action
        className="sidebar-button"
        onClick={() => {
          if (active) {
            updateSidebar("");
          } else {
            updateSidebar(itemKey);
          }
        }}
      >
        <DisplayItem
          badge={badgeValue === 0 ? undefined : badgeValue ?? undefined}
          icon={icon}
          name={name}
        ></DisplayItem>
      </ListGroupItem>
      <Collapse in={active}>
        <div className="sidebar-collapse">
          {children.map((ch) => {
            let badge: Nullable<number> = null;
            if (childValue && ch.name in childValue) {
              badge = childValue[ch.name];
            }
            return (
              <NavLink
                key={ch.name}
                activeClassName="sb-active"
                className="list-group-item list-group-item-action sidebar-button sb-collapse"
                to={ch.link}
                onClick={toggleSidebar}
              >
                <DisplayItem
                  badge={badge === 0 ? undefined : badge ?? undefined}
                  name={ch.name}
                ></DisplayItem>
              </NavLink>
            );
          })}
        </div>
      </Collapse>
    </div>
  );
};

interface DisplayProps {
  name: string;
  icon?: IconDefinition;
  badge?: number;
}

const DisplayItem: FunctionComponent<DisplayProps> = ({
  name,
  icon,
  badge,
}) => (
  <React.Fragment>
    {icon && (
      <FontAwesomeIcon size="1x" className="icon" icon={icon}></FontAwesomeIcon>
    )}
    <span className="d-flex flex-grow-1 justify-content-between">
      {name} <Badge variant="secondary">{badge}</Badge>
    </span>
  </React.Fragment>
);
