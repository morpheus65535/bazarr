import React, { FunctionComponent } from "react";
import { Accordion, Badge, ListGroup } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { NavLink } from "react-router-dom";

import { SidebarDef } from "./types";
import { IconDefinition } from "@fortawesome/free-solid-svg-icons";

const Content: FunctionComponent<{
  name: string;
  icon: IconDefinition;
  badge?: string;
}> = (props) => {
  return (
    <React.Fragment>
      <FontAwesomeIcon
        size="1x"
        className="mr-2"
        icon={props.icon}
      ></FontAwesomeIcon>
      <span>
        {props.name} <Badge variant="secondary">{props.badge}</Badge>
      </span>
    </React.Fragment>
  );
};

const Item: FunctionComponent<{ def: SidebarDef }> = (props) => {
  const { to, name, children } = props.def;
  if (to) {
    return (
      <NavLink
        activeClassName="active"
        className="list-group-item list-group-item-action py-2"
        to={to}
      >
        <Content {...props.def}></Content>
      </NavLink>
    );
  } else if (children) {
    return (
      <React.Fragment>
        <Accordion.Toggle
          as={ListGroup.Item}
          action
          eventKey={name.toLowerCase()}
          className="py-2"
        >
          <Content {...props.def}></Content>
        </Accordion.Toggle>
        <Accordion.Collapse
          eventKey={name.toLowerCase()}
          className="list-group-flush"
        >
          <React.Fragment>
            {children.map((ch) => (
              <NavLink
                key={ch.name}
                activeClassName="active"
                className="list-group-item list-group-item-action py-2"
                to={ch.to}
              >
                <span className="ml-4">
                  {ch.name} <Badge variant="secondary">{ch.badge}</Badge>
                </span>
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
