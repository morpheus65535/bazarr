import {
  faClone as fasClone,
  faFolder,
} from "@fortawesome/free-regular-svg-icons";
import {
  faLanguage,
  faMusic,
  faStream,
  faTags,
  IconDefinition,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import {
  Badge,
  Col,
  Container,
  Image,
  OverlayTrigger,
  Popover,
  Row,
} from "react-bootstrap";
import { connect } from "react-redux";

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

    badges.push(createBadge(faFolder, item.mapped_path, "File Path: "));

    badges.push(
      ...(details?.map((val) => createBadge(val.icon, val.text)) ?? [])
    );

    badges.push(createBadge(faTags, item.tags.join("|"), "Tags: "));

    return badges;
  }, [details, item.mapped_path, item.tags]);

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

  const alternativePopover = useMemo(
    () => (
      <Popover id="item-overview-alternative">
        <Popover.Title>Alternate Titles</Popover.Title>
        <Popover.Content>
          {item.alternativeTitles.map((v, idx) => (
            <li key={idx}>{v}</li>
          ))}
        </Popover.Content>
      </Popover>
    ),
    [item.alternativeTitles]
  );

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
              <span hidden={item.alternativeTitles.length === 0}>
                <OverlayTrigger placement="left" overlay={alternativePopover}>
                  <FontAwesomeIcon
                    className="mx-2"
                    icon={fasClone}
                  ></FontAwesomeIcon>
                </OverlayTrigger>
              </span>
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
