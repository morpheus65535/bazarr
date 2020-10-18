import React from "react";
import { Badge, ListGroup, Navbar } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  faPlay,
  faFilm,
  faExclamationTriangle,
  faCogs,
  faLaptop,
} from "@fortawesome/free-solid-svg-icons";
import { NavLink } from "react-router-dom";

import { StoreState } from "../redux/types";
import { connect } from "react-redux";

interface ListItemProps {
  name: string;
  icon: IconDefinition;
  href: string;
  badge?: string;
}

class ListItem extends React.Component<ListItemProps, object> {
  render(): JSX.Element {
    const { name, icon, href, badge } = this.props;
    return (
      <NavLink
        activeClassName="active"
        className="list-group-item list-group-item-action py-2 d-flex align-items-center"
        to={href}
      >
        <FontAwesomeIcon
          size="1x"
          className="mr-3"
          icon={icon}
        ></FontAwesomeIcon>
        <span>{name}</span>
        <Badge variant="secondary" className="ml-2" hidden={badge === null}>
          {badge}
        </Badge>
      </NavLink>
    );
  }
}

interface SidebarProps {
  movies_badge: number;
  episodes_badge: number;
  providers_badge: number;
}

export function mapStateToProps({ badges }: StoreState): SidebarProps {
  return {
    movies_badge: badges.movies,
    episodes_badge: badges.episodes,
    providers_badge: badges.providers,
  };
}

class Sidebar extends React.Component<SidebarProps, {}> {
  render() {
    const { movies_badge, episodes_badge, providers_badge } = this.props;
    const totalWanted = movies_badge + episodes_badge;

    return (
      <aside id="sidebar-wrapper" className="px-0 col-md-3 col-xl-2">
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
          <ListItem
            name="Wanted"
            icon={faExclamationTriangle}
            href="/wanted"
            badge={totalWanted === 0 ? undefined : totalWanted.toString()}
          ></ListItem>
          <ListItem name="Settings" icon={faCogs} href="/settings"></ListItem>
          <ListItem
            name="System"
            icon={faLaptop}
            href="/system"
            badge={
              providers_badge === 0 ? undefined : providers_badge.toString()
            }
          ></ListItem>
        </ListGroup>
      </aside>
    );
  }
}

export default connect(mapStateToProps)(Sidebar);
