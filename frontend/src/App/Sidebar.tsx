import React, { FunctionComponent } from "react";
import { Accordion, Badge, ListGroup, Navbar, Col } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  faPlay,
  faFilm,
  faExclamationTriangle,
  faCogs,
  faLaptop,
  faClock,
} from "@fortawesome/free-solid-svg-icons";
import { NavLink } from "react-router-dom";

import { connect } from "react-redux";

interface BaseItemProps {
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

const LinkListItem: FunctionComponent<LinkListItemProps> = (props) => {
  const { children, icon, href, badge } = props;
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
        <span>{children}</span>
        <Badge variant="secondary" className="ml-2" hidden={badge === null}>
          {badge}
        </Badge>
      </Col>
    </NavLink>
  );
};

const ToggleListItem: FunctionComponent<ToggleItemProps> = (props) => {
  const { children, icon, badge, eventKey } = props;
  return (
    <Accordion.Toggle
      as={ListGroup.Item}
      action
      eventKey={eventKey}
      className="d-flex align-items-center py-2"
    >
      <Col sm={1} className="justify-content-center">
        <FontAwesomeIcon
          size="1x"
          className="mr-3"
          icon={icon}
        ></FontAwesomeIcon>
      </Col>
      <Col>
        <span>{children}</span>
        <Badge variant="secondary" className="ml-2" hidden={badge === null}>
          {badge}
        </Badge>
      </Col>
    </Accordion.Toggle>
  );
};

const ListCollapseItem: FunctionComponent<CollapseItemProps> = (props) => {
  const { children, href, badge } = props;
  return (
    <NavLink
      activeClassName="active"
      className="list-group-item list-group-item-action py-2 d-flex align-items-center border-0"
      to={href}
    >
      <span className="ml-4">{children}</span>
      <Badge variant="secondary" className="ml-2" hidden={badge === null}>
        {badge}
      </Badge>
    </NavLink>
  );
};

interface Props {
  movies_badge: number;
  episodes_badge: number;
  providers_badge: number;
}

interface State {
  active: string;
}

function mapStateToProps({ badges }: StoreState): Props {
  return {
    movies_badge: badges.movies,
    episodes_badge: badges.episodes,
    providers_badge: badges.providers,
  };
}

class Sidebar extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      active: "",
    };
  }

  render() {
    const { movies_badge, episodes_badge, providers_badge } = this.props;
    const totalWanted = movies_badge + episodes_badge;

    const { active } = this.state;

    const history = (
      <ToggleListItem icon={faClock} eventKey="history-toggle">
        History
      </ToggleListItem>
    );

    const historyItems: JSX.Element = (
      <Accordion.Collapse eventKey="history-toggle">
        <div>
          <ListCollapseItem href="/history/series">Series</ListCollapseItem>
          <ListCollapseItem href="/history/movies">Movies</ListCollapseItem>
        </div>
      </Accordion.Collapse>
    );

    const wanted: JSX.Element = (
      <ToggleListItem
        icon={faExclamationTriangle}
        badge={totalWanted === 0 ? undefined : totalWanted.toString()}
        eventKey="wanted-toggle"
      >
        Wanted
      </ToggleListItem>
    );

    const wantedItems: JSX.Element = (
      <Accordion.Collapse eventKey="wanted-toggle">
        <div>
          <ListCollapseItem
            href="/wanted/series"
            badge={episodes_badge === 0 ? undefined : episodes_badge.toString()}
          >
            Series
          </ListCollapseItem>
          <ListCollapseItem
            href="/wanted/movies"
            badge={movies_badge === 0 ? undefined : movies_badge.toString()}
          >
            Movies
          </ListCollapseItem>
        </div>
      </Accordion.Collapse>
    );

    const settings: JSX.Element = (
      <ToggleListItem icon={faCogs} eventKey="settings-toggle">
        Settings
      </ToggleListItem>
    );

    const settingsItems: JSX.Element = (
      <Accordion.Collapse eventKey="settings-toggle">
        <div>
          <ListCollapseItem href="/settings/general">General</ListCollapseItem>
          <ListCollapseItem href="/settings/subtitles">
            Subtitles
          </ListCollapseItem>
          <ListCollapseItem href="/settings/languages">
            Languages
          </ListCollapseItem>
        </div>
      </Accordion.Collapse>
    );

    const system: JSX.Element = (
      <ToggleListItem
        icon={faLaptop}
        eventKey="system-toggle"
        badge={providers_badge === 0 ? undefined : providers_badge.toString()}
      >
        System
      </ToggleListItem>
    );

    const systemItems: JSX.Element = (
      <Accordion.Collapse eventKey="system-toggle">
        <div>
          <ListCollapseItem href="/system/tasks">Tasks</ListCollapseItem>
          <ListCollapseItem href="/system/status">Status</ListCollapseItem>
        </div>
      </Accordion.Collapse>
    );

    return (
      <aside>
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
        <Accordion defaultActiveKey={active}>
          <ListGroup variant="flush">
            <LinkListItem icon={faPlay} href="/series">
              Series
            </LinkListItem>
            <LinkListItem icon={faFilm} href="/movies">
              Movies
            </LinkListItem>
            {history}
            {historyItems}
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
