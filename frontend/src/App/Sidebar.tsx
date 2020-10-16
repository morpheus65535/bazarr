import React from "react";
import { ListGroup, Navbar } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  faPlay,
  faFilm,
  faCogs,
  faLaptop,
} from "@fortawesome/free-solid-svg-icons";
import { NavLink } from "react-router-dom";

interface ListItemProps {
  name: string;
  icon: IconDefinition;
  href: string;
}

class ListItem extends React.Component<ListItemProps, object> {
  render(): JSX.Element {
    const { name, icon, href } = this.props;
    return (
      <NavLink
        activeClassName="active"
        className="list-group-item list-group-item-action"
        to={href}
      >
        <FontAwesomeIcon
          size="1x"
          className="mr-3"
          icon={icon}
        ></FontAwesomeIcon>
        <span>{name}</span>
      </NavLink>
    );
  }
}

class Sidebar extends React.Component {
  render() {
    return (
      <aside
        id="sidebar-wrapper"
        className="border-right px-0 col-md-3 col-xl-2"
      >
        <Navbar bg="light" expand="lg" className="header">
          <Navbar.Brand href="#home">
            <img
              alt="brand"
              src="logo128.png"
              width="32"
              height="32"
              className="mr-2"
            ></img>
          </Navbar.Brand>
        </Navbar>
        <ListGroup variant="flush">
          <ListItem name="Series" icon={faPlay} href="/series"></ListItem>
          <ListItem name="Movie" icon={faFilm} href="/movie"></ListItem>
          <ListItem name="Settings" icon={faCogs} href="/settings"></ListItem>
          <ListItem name="System" icon={faLaptop} href="/system"></ListItem>
        </ListGroup>
      </aside>
    );
  }
}

export default Sidebar;
