import React, { FunctionComponent, useMemo } from "react";
import { connect } from "react-redux";
import { SidebarDef } from "./types";
import {
  faPlay,
  faFilm,
  faExclamationTriangle,
  faCogs,
  faLaptop,
  faClock,
} from "@fortawesome/free-solid-svg-icons";
import { Accordion, ListGroup, Container, Image } from "react-bootstrap";

import SidebarItem from "./SidebarItem";
import { useHistory } from "react-router-dom";

import logo from "../@static/logo128.png";

interface Props {
  movies_badge: number;
  episodes_badge: number;
  providers_badge: number;
  open?: boolean;
  onToggle?: () => void;
}

function mapStateToProps({ badges }: StoreState) {
  return {
    movies_badge: badges.movies,
    episodes_badge: badges.episodes,
    providers_badge: badges.providers,
  };
}

const Sidebar: FunctionComponent<Props> = ({
  movies_badge,
  episodes_badge,
  providers_badge,
  open,
  onToggle,
}) => {
  const sidebar = useMemo<SidebarDef[]>(
    () => [
      {
        icon: faPlay,
        name: "Series",
        to: "/series",
      },
      {
        icon: faFilm,
        name: "Movies",
        to: "/movies",
      },
      {
        icon: faClock,
        name: "History",
        children: [
          {
            name: "Series",
            to: "/history/series",
          },
          {
            name: "Movies",
            to: "/history/movies",
          },
        ],
      },
      {
        icon: faExclamationTriangle,
        name: "Wanted",
        badge:
          movies_badge + episodes_badge === 0
            ? undefined
            : (movies_badge + episodes_badge).toString(),
        children: [
          {
            name: "Series",
            to: "/wanted/series",
            badge: episodes_badge === 0 ? undefined : episodes_badge.toString(),
          },
          {
            name: "Movies",
            to: "/wanted/movies",
            badge: movies_badge === 0 ? undefined : movies_badge.toString(),
          },
        ],
      },
      {
        icon: faCogs,
        name: "Settings",
        children: [
          {
            name: "General",
            to: "/settings/general",
          },
          {
            name: "Sonarr",
            to: "/settings/sonarr",
          },
          {
            name: "Radarr",
            to: "/settings/radarr",
          },
          {
            name: "Subtitles",
            to: "/settings/subtitles",
          },
          {
            name: "Languages",
            to: "/settings/languages",
          },
          {
            name: "Schedular",
            to: "/settings/schedular",
          },
        ],
      },
      {
        icon: faLaptop,
        name: "System",
        badge: providers_badge === 0 ? undefined : providers_badge.toString(),
        children: [
          {
            name: "Tasks",
            to: "/system/tasks",
          },
          {
            name: "Logs",
            to: "/system/logs",
          },
          {
            name: "Providers",
            to: "/system/providers",
            badge:
              providers_badge === 0 ? undefined : providers_badge.toString(),
          },
          {
            name: "Status",
            to: "/system/status",
          },
        ],
      },
    ],
    [movies_badge, episodes_badge, providers_badge]
  );

  const history = useHistory();

  const path = history.location.pathname.split("/");
  const active = path.length >= 2 ? path[1] : "";

  const cls = ["sidebar-container"];
  const overlay = ["sidebar-overlay"];

  if (open && open === true) {
    cls.push("open");
    overlay.push("open");
  }

  return (
    <React.Fragment>
      <aside className={cls.join(" ")}>
        <Container className="sidebar-title d-flex align-items-center d-md-none">
          <Image alt="brand" src={logo} width="32" height="32"></Image>
        </Container>
        <Accordion defaultActiveKey={active}>
          <ListGroup variant="flush">
            {sidebar.map((def) => (
              <SidebarItem
                key={def.name}
                def={def}
                onClick={onToggle}
              ></SidebarItem>
            ))}
          </ListGroup>
        </Accordion>
      </aside>
      <div className={overlay.join(" ")} onClick={onToggle}></div>
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(Sidebar);
