import React from "react";
import { Accordion, Badge, ListGroup, Navbar, Col } from "react-bootstrap";
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

import { connect } from "react-redux";

interface BaseItemProps {
  name: string;
  badge?: string;
}

interface ListItemProps extends BaseItemProps {
  icon: IconDefinition;
}

interface ToggleItemProps extends ListItemProps {
  eventKey: string;
}

interface LinkListItemProps extends ListItemProps {
  href: string;
}

interface CollapseItemProps extends BaseItemProps {
  href: string;
}

class LinkListItem extends React.Component<LinkListItemProps, {}> {
  render(): JSX.Element {
    const { name, icon, href, badge } = this.props;
    return (
      <NavLink
        activeClassName="active"
        className="list-group-item list-group-item-action py-2 d-flex align-items-center"
        to={href}
      >
        <Col sm={1}>
          <FontAwesomeIcon
            size="1x"
            className="mr-3"
            icon={icon}
          ></FontAwesomeIcon>
        </Col>
        <Col>
          <span>{name}</span>
          <Badge variant="secondary" className="ml-2" hidden={badge === null}>
            {badge}
          </Badge>
        </Col>
      </NavLink>
    );
  }
}

class ToggleListItem extends React.Component<ToggleItemProps, {}> {
  render(): JSX.Element {
    const { name, icon, badge, eventKey } = this.props;
    return (
      <Accordion.Toggle
        as={ListGroup.Item}
        action
        eventKey={eventKey}
        className="d-flex align-items-center py-2"
      >
        <Col sm={1}>
          <FontAwesomeIcon
            size="1x"
            className="mr-3"
            icon={icon}
          ></FontAwesomeIcon>
        </Col>
        <Col>
          <span>{name}</span>
          <Badge variant="secondary" className="ml-2" hidden={badge === null}>
            {badge}
          </Badge>
        </Col>
      </Accordion.Toggle>
    );
  }
}

class ListCollapseItem extends React.Component<CollapseItemProps, {}> {
  render(): JSX.Element {
    const { name, href, badge } = this.props;
    return (
      <NavLink
        activeClassName="active"
        className="list-group-item list-group-item-action py-2 d-flex align-items-center border-0"
        to={href}
      >
        <span className="ml-4">{name}</span>
        <Badge variant="secondary" className="ml-2" hidden={badge === null}>
          {badge}
        </Badge>
      </NavLink>
    );
  }
}

interface Props {
  movies_badge: number;
  episodes_badge: number;
  providers_badge: number;
}

function mapStateToProps({ badges }: StoreState): Props {
  return {
    movies_badge: badges.movies,
    episodes_badge: badges.episodes,
    providers_badge: badges.providers,
  };
}

class Sidebar extends React.Component<Props, {}> {
  render() {
    const { movies_badge, episodes_badge, providers_badge } = this.props;
    const totalWanted = movies_badge + episodes_badge;

    const wanted: JSX.Element = (
      <ToggleListItem
        name="Wanted"
        icon={faExclamationTriangle}
        badge={totalWanted === 0 ? undefined : totalWanted.toString()}
        eventKey="wanted-toggle"
      ></ToggleListItem>
    );

    const wantedItems: JSX.Element = (
      <Accordion.Collapse eventKey="wanted-toggle">
        <div>
          <ListCollapseItem
            name="Series"
            href="/wanted/series"
            badge={episodes_badge === 0 ? undefined : episodes_badge.toString()}
          ></ListCollapseItem>
        </div>
      </Accordion.Collapse>
    );

    const settings: JSX.Element = (
      <ToggleListItem
        name="Settings"
        icon={faCogs}
        eventKey="settings-toggle"
      ></ToggleListItem>
    );

    const settingsItems: JSX.Element = (
      <Accordion.Collapse eventKey="settings-toggle">
        <div>
          <ListCollapseItem
            name="General"
            href="/settings/general"
          ></ListCollapseItem>
          <ListCollapseItem
            name="Subtitles"
            href="/settings/subtitles"
          ></ListCollapseItem>
          <ListCollapseItem
            name="Languages"
            href="/settings/languages"
          ></ListCollapseItem>
        </div>
      </Accordion.Collapse>
    );

    const system: JSX.Element = (
      <ToggleListItem
        name="System"
        icon={faLaptop}
        eventKey="system-toggle"
        badge={providers_badge === 0 ? undefined : providers_badge.toString()}
      ></ToggleListItem>
    );

    const systemItems: JSX.Element = (
      <Accordion.Collapse eventKey="system-toggle">
        <div>
          <ListCollapseItem
            name="Tasks"
            href="/system/tasks"
          ></ListCollapseItem>
          <ListCollapseItem
            name="Status"
            href="/system/status"
          ></ListCollapseItem>
        </div>
      </Accordion.Collapse>
    );

    return (
      <aside id="sidebar-wrapper" className="px-0 col-md-3 col-xl-2">
        <Navbar bg="light" expand="lg" className="header">
          <Navbar.Brand href="/">
            <img
              alt="brand"
              src="/logo128.png"
              width="32"
              height="32"
              className="mr-2"
            ></img>
          </Navbar.Brand>
        </Navbar>
        <Accordion>
          <ListGroup variant="flush">
            <LinkListItem
              name="Series"
              icon={faPlay}
              href="/series"
            ></LinkListItem>
            <LinkListItem
              name="Movie"
              icon={faFilm}
              href="/movie"
            ></LinkListItem>
            {wanted}
            {wantedItems}
            {settings}
            {settingsItems}
            {system}
            {systemItems}
          </ListGroup>
        </Accordion>
      </aside>
    );
  }
}

export default connect(mapStateToProps)(Sidebar);
