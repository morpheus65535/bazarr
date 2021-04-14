import React, { FunctionComponent, useContext, useMemo } from "react";
import { Container, Image, ListGroup } from "react-bootstrap";
import { useReduxStore } from "../@redux/hooks/base";
import { useIsRadarrEnabled, useIsSonarrEnabled } from "../@redux/hooks/site";
import logo from "../@static/logo64.png";
import { SidebarToggleContext } from "../App";
import { useGotoHomepage } from "../utilites/hooks";
import {
  BadgesContext,
  CollapseItem,
  HiddenKeysContext,
  LinkItem,
} from "./items";
import { RadarrDisabledKey, SidebarList, SonarrDisabledKey } from "./list";
import "./style.scss";
import { BadgeProvider } from "./types";

interface Props {
  open?: boolean;
}

const Sidebar: FunctionComponent<Props> = ({ open }) => {
  const toggle = useContext(SidebarToggleContext);

  const { movies, episodes, providers } = useReduxStore((s) => s.site.badges);

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
    [movies, episodes, providers]
  );

  const sonarrEnabled = useIsSonarrEnabled();
  const radarrEnabled = useIsRadarrEnabled();

  const hiddenKeys = useMemo<string[]>(() => {
    const list = [];
    if (!sonarrEnabled) {
      list.push(SonarrDisabledKey);
    }
    if (!radarrEnabled) {
      list.push(RadarrDisabledKey);
    }
    return list;
  }, [sonarrEnabled, radarrEnabled]);

  const cls = ["sidebar-container"];
  const overlay = ["sidebar-overlay"];

  if (open === true) {
    cls.push("open");
    overlay.push("open");
  }

  const sidebarItems = useMemo(
    () =>
      SidebarList.map((v) => {
        if (hiddenKeys.includes(v.hiddenKey ?? "")) {
          return null;
        }
        if ("children" in v) {
          return <CollapseItem key={v.name} {...v}></CollapseItem>;
        } else {
          return <LinkItem key={v.link} {...v}></LinkItem>;
        }
      }),
    [hiddenKeys]
  );

  const goHome = useGotoHomepage();

  return (
    <React.Fragment>
      <aside className={cls.join(" ")}>
        <Container className="sidebar-title d-flex align-items-center d-md-none">
          <Image
            alt="brand"
            src={logo}
            width="32"
            height="32"
            onClick={goHome}
            className="cursor-pointer"
          ></Image>
        </Container>
        <HiddenKeysContext.Provider value={hiddenKeys}>
          <BadgesContext.Provider value={badges}>
            <ListGroup variant="flush">{sidebarItems}</ListGroup>
          </BadgesContext.Provider>
        </HiddenKeysContext.Provider>
      </aside>
      <div className={overlay.join(" ")} onClick={toggle}></div>
    </React.Fragment>
  );
};

export default Sidebar;
