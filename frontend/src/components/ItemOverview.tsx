import {
  faBookmark as farBookmark,
  faClone as fasClone,
  faFolder,
} from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
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
import { BuildKey, isMovie } from "utilities";
import {
  useLanguageProfileBy,
  useProfileItemsToLanguages,
} from "utilities/languages";
import { LanguageText } from ".";

interface Props {
  item: Item.Base;
  details?: { icon: IconDefinition; text: string }[];
}

const ItemOverview: FunctionComponent<Props> = (props) => {
  const { item, details } = props;

  const detailBadges = useMemo(() => {
    const badges: (JSX.Element | null)[] = [];
    badges.push(
      <DetailBadge key="file-path" icon={faFolder} desc="File Path">
        {item.path}
      </DetailBadge>
    );

    badges.push(
      ...(details?.map((val, idx) => (
        <DetailBadge key={BuildKey(idx, "detail", val.text)} icon={val.icon}>
          {val.text}
        </DetailBadge>
      )) ?? [])
    );

    if (item.tags.length > 0) {
      badges.push(
        <DetailBadge key="tags" icon={faTags} desc="Tags">
          {item.tags.join("|")}
        </DetailBadge>
      );
    }

    return badges;
  }, [details, item.path, item.tags]);

  const audioBadges = useMemo(
    () =>
      item.audio_language.map((v, idx) => (
        <DetailBadge
          key={BuildKey(idx, "audio", v.code2)}
          icon={faMusic}
          desc="Audio Language"
        >
          {v.name}
        </DetailBadge>
      )),
    [item.audio_language]
  );

  const profile = useLanguageProfileBy(item.profileId);
  const profileItems = useProfileItemsToLanguages(profile);

  const languageBadges = useMemo(() => {
    const badges: (JSX.Element | null)[] = [];

    if (profile) {
      badges.push(
        <DetailBadge
          key="language-profile"
          icon={faStream}
          desc="Languages Profile"
        >
          {profile.name}
        </DetailBadge>
      );

      badges.push(
        ...profileItems.map((v, idx) => (
          <DetailBadge
            key={BuildKey(idx, "lang", v.code2)}
            icon={faLanguage}
            desc="Language"
          >
            <LanguageText long text={v}></LanguageText>
          </DetailBadge>
        ))
      );
    }

    return badges;
  }, [profile, profileItems]);

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
        className="p-4 pb-4"
        style={{
          backgroundColor: "rgba(0,0,0,0.7)",
        }}
      >
        <Col sm="auto">
          <Image
            className="d-none d-sm-block my-2"
            style={{
              maxHeight: 250,
            }}
            src={item.poster}
          ></Image>
        </Col>
        <Col>
          <Container fluid className="text-white">
            <Row>
              {isMovie(item) ? (
                <FontAwesomeIcon
                  className="mx-2 mt-2"
                  title={item.monitored ? "monitored" : "unmonitored"}
                  icon={item.monitored ? faBookmark : farBookmark}
                  size="2x"
                ></FontAwesomeIcon>
              ) : null}
              <h1>{item.title}</h1>
              <span hidden={item.alternativeTitles.length === 0}>
                <OverlayTrigger overlay={alternativePopover}>
                  <FontAwesomeIcon
                    className="mx-2"
                    icon={fasClone}
                  ></FontAwesomeIcon>
                </OverlayTrigger>
              </span>
            </Row>
            <Row>{detailBadges}</Row>
            <Row>{audioBadges}</Row>
            <Row>{languageBadges}</Row>
            <Row>
              <span>{item.overview}</span>
            </Row>
          </Container>
        </Col>
      </Row>
    </Container>
  );
};

interface ItemBadgeProps {
  icon: IconDefinition;
  children: string | JSX.Element;
  desc?: string;
}

const DetailBadge: FunctionComponent<ItemBadgeProps> = ({
  icon,
  desc,
  children,
}) => (
  <Badge title={desc} variant="secondary" className="mr-2 my-1 text-truncate">
    <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    <span className="ml-1">{children}</span>
  </Badge>
);

export default ItemOverview;
