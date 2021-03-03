import React, {
  FunctionComponent,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Container, Image, ListGroup } from "react-bootstrap";
import { useHistory } from "react-router-dom";
import { useReduxStore } from "../@redux/hooks/base";
import logo from "../@static/logo64.png";
import { SidebarToggleContext } from "../App";
import {
  ActiveKeyContext,
  BadgesContext,
  CollapseItem,
  LinkItem,
} from "./items";
import { SidebarList } from "./list";
import "./style.scss";
import { BadgeProvider } from "./types";

interface Props {
  open?: boolean;
}

const Sidebar: FunctionComponent<Props> = ({ open }) => {
  const toggle = useContext(SidebarToggleContext);

  const { movies, episodes, providers } = useReduxStore(({ badges }) => ({
    movies: badges.movies,
    episodes: badges.episodes,
    providers: badges.providers,
  }));

  const badges = useMemo<BadgeProvider>(
    () => ({
      Wanted: {
        Series: episodes,
        Movies: movies,
      },
      System: {
        Providers: providers,
      },
    }),
    [episodes, movies, providers]
  );

  const history = useHistory();

  const [activeKey, setActiveKey] = useState("");

  useEffect(() => {
    const path = history.location.pathname.split("/");
    const len = path.length;
    if (len >= 3) {
      setActiveKey(path[len - 2]);
    } else {
      setActiveKey(path[len - 1]);
    }
  }, [history.location.pathname]);

  const cls = ["sidebar-container"];
  const overlay = ["sidebar-overlay"];

  if (open && open === true) {
    cls.push("open");
    overlay.push("open");
  }

  const sidebarItems = useMemo(
    () =>
      SidebarList.map((v) => {
        if ("children" in v) {
          return <CollapseItem key={v.name} {...v}></CollapseItem>;
        } else {
          return <LinkItem key={v.link} {...v}></LinkItem>;
        }
      }),
    []
  );

  return (
    <React.Fragment>
      <aside className={cls.join(" ")}>
        <Container className="sidebar-title d-flex align-items-center d-md-none">
          <Image alt="brand" src={logo} width="32" height="32"></Image>
        </Container>
        <ActiveKeyContext.Provider value={[activeKey, setActiveKey]}>
          <BadgesContext.Provider value={badges}>
            <ListGroup variant="flush">{sidebarItems}</ListGroup>
          </BadgesContext.Provider>
        </ActiveKeyContext.Provider>
      </aside>
      <div className={overlay.join(" ")} onClick={toggle}></div>
    </React.Fragment>
  );
};

export default Sidebar;
