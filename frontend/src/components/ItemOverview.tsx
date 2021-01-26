import React, { FunctionComponent, useMemo } from "react";
import { Image, Container, Row, Col, Badge } from "react-bootstrap";
import { connect } from "react-redux";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import {
  faMusic,
  faLanguage,
  IconDefinition,
  faTags,
  faStream,
} from "@fortawesome/free-solid-svg-icons";
import { faFolder } from "@fortawesome/free-regular-svg-icons";

interface Props {
  item: ExtendItem;
  details?: { icon: IconDefinition; text: string }[];
  profiles: LanguagesProfile[];
}

function mapStateToProps({ system }: StoreState) {
  return {
    profiles: system.languagesProfiles.items,
  };
}

const createBadge = (icon: IconDefinition, text: string, desc?: string) => {
  if (text.length === 0) {
    return null;
  }

  return (
    <Badge
      title={`${desc ?? ""}${text}`}
      variant="secondary"
      className="mr-2 my-1 text-overflow-ellipsis"
      key={text}
    >
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
      <span className="ml-1">{text}</span>
    </Badge>
  );
};

const ItemOverview: FunctionComponent<Props> = (props) => {
  const { item, details, profiles } = props;

  const detailBadges = useMemo(() => {
    const badges: (JSX.Element | null)[] = [];

    badges.push(createBadge(faFolder, item.path, "File Path: "));

    badges.push(
      ...(details?.map((val) => createBadge(val.icon, val.text)) ?? [])
    );

    badges.push(createBadge(faTags, item.tags.join("|"), "Tags: "));

    return badges;
  }, [details, item.path, item.tags]);

  const audioBadges = useMemo(
    () =>
      item.audio_language.map((v) =>
        createBadge(faMusic, v.name, "Audio Language: ")
      ),
    [item.audio_language]
  );

  const languageBadges = useMemo(() => {
    const badges: (JSX.Element | null)[] = [];

    if (item.profileId) {
      const profile = profiles.find((v) => v.profileId === item.profileId);
      if (profile) {
        badges.push(createBadge(faStream, profile.name, "Languages Profile: "));
      }
    }

    badges.push(
      ...item.languages.map((val) => {
        return createBadge(faLanguage, val.name, "Language: ");
      })
    );
    return badges;
  }, [item.languages, profiles, item.profileId]);

  return (
    <Container
      fluid
      style={{
        backgroundRepeat: "no-repeat",
        backgroundSize: "cover",
        backgroundPosition: "top center",
        backgroundImage: `url('${item.fanart}')`,
      }}
    >
      <Row
        className="p-4 pb-5"
        style={{
          backgroundColor: "rgba(0,0,0,0.7)",
        }}
      >
        <Col sm="auto">
          <Image
            className="d-none d-sm-block"
            style={{
              maxHeight: 250,
            }}
            src={item.poster}
          ></Image>
        </Col>
        <Col>
          <Container fluid>
            <Row className="text-white">
              <h1>{item.title}</h1>
              {/* TODO: Tooltip */}
            </Row>
            <Row className="text-white">{detailBadges}</Row>
            <Row className="text-white">{audioBadges}</Row>
            <Row className="text-white">{languageBadges}</Row>
            <Row className="text-white"></Row>
            <Row className="text-white">
              <span>{item.overview}</span>
            </Row>
          </Container>
        </Col>
      </Row>
    </Container>
  );
};

export default connect(mapStateToProps)(ItemOverview);
