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
import { Accordion, ListGroup } from "react-bootstrap";

import SidebarItem from "./SidebarItem";
import { useHistory } from "react-router-dom";

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

const Sidebar: FunctionComponent<Props> = ({
  movies_badge,
  episodes_badge,
  providers_badge,
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
            name: "Subtitles",
            to: "/settings/subtitles",
          },
          {
            name: "Languages",
            to: "/settings/languages",
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

  return (
    <aside>
      <Accordion defaultActiveKey={active}>
        <ListGroup variant="flush">
          {sidebar.map((def) => (
            <SidebarItem key={def.name} def={def}></SidebarItem>
          ))}
        </ListGroup>
      </Accordion>
    </aside>
  );
};

export default connect(mapStateToProps)(Sidebar);
