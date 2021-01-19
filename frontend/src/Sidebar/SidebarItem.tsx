import React, { FunctionComponent } from "react";
import { Accordion, Badge } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { NavLink } from "react-router-dom";

import { SidebarDef } from "./types";
import { IconDefinition } from "@fortawesome/free-solid-svg-icons";

const Content: FunctionComponent<{
  name: string;
  icon: IconDefinition;
  badge?: string;
}> = (props) => (
  <React.Fragment>
    <FontAwesomeIcon
      size="1x"
      className="icon"
      icon={props.icon}
    ></FontAwesomeIcon>
    <span>
      {props.name} <Badge variant="secondary">{props.badge}</Badge>
    </span>
  </React.Fragment>
);

const ChildContent: FunctionComponent<{ name: string; badge?: string }> = (
  props
) => (
  <span className="ml-4">
    {props.name} <Badge variant="secondary">{props.badge}</Badge>
  </span>
);

const Item: FunctionComponent<{ def: SidebarDef; onClick?: () => void }> = (
  props
) => {
  const { to, name, children } = props.def;
  const { onClick } = props;
  if (to) {
    return (
      <NavLink
        activeClassName="sb-active"
        className="list-group-item list-group-item-action sidebar-button"
        to={to}
        onClick={onClick}
      >
        <Content {...props.def}></Content>
      </NavLink>
    );
  } else if (children) {
    return (
      <React.Fragment>
        <Accordion.Toggle
          eventKey={name.toLowerCase()}
          className="list-group-item list-group-item-action sidebar-button sb-action"
        >
          <Content {...props.def}></Content>
        </Accordion.Toggle>
        <Accordion.Collapse
          className="sidebar-collapse"
          eventKey={name.toLowerCase()}
        >
          <React.Fragment>
            {children.map((ch) => (
              <NavLink
                key={ch.name}
                activeClassName="sb-active"
                className="list-group-item list-group-item-action sidebar-button sb-collapse"
                to={ch.to}
                onClick={onClick}
              >
                <ChildContent name={ch.name} badge={ch.badge}></ChildContent>
              </NavLink>
            ))}
          </React.Fragment>
        </Accordion.Collapse>
      </React.Fragment>
    );
  } else {
    return null;
  }
};

export default Item;
