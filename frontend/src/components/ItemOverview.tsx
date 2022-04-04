import { BuildKey, isMovie } from "@/utilities";
import {
  useLanguageProfileBy,
  useProfileItemsToLanguages,
} from "@/utilities/languages";
import {
  faBookmark as farBookmark,
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
import { Badge, Grid, Group, Image, Stack, Title } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import Language from "./bazarr/Language";

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
            <Language.Text long value={v}></Language.Text>
          </DetailBadge>
        ))
      );
    }

    return badges;
  }, [profile, profileItems]);

  // const alternativePopover = useMemo(
  //   () => (
  //     <Popover id="item-overview-alternative">
  //       <Popover.Title>Alternate Titles</Popover.Title>
  //       <Popover.Content>
  //         {item.alternativeTitles.map((v, idx) => (
  //           <li key={idx}>{v}</li>
  //         ))}
  //       </Popover.Content>
  //     </Popover>
  //   ),
  //   [item.alternativeTitles]
  // );

  return (
    <Grid
      style={{
        backgroundRepeat: "no-repeat",
        backgroundSize: "cover",
        backgroundPosition: "top center",
        backgroundImage: `url('${item.fanart}')`,
      }}
    >
      <Grid.Col>
        <Image
          className="d-none d-sm-block my-2"
          style={{
            maxHeight: 250,
          }}
          src={item.poster}
        ></Image>
      </Grid.Col>
      <Grid.Col>
        <Stack>
          <Group>
            {isMovie(item) ? (
              <FontAwesomeIcon
                className="mx-2 mt-2"
                title={item.monitored ? "monitored" : "unmonitored"}
                icon={item.monitored ? faBookmark : farBookmark}
                size="2x"
              ></FontAwesomeIcon>
            ) : null}
            <Title>{item.title}</Title>
          </Group>
          {/* <Row>
            <h1>{item.title}</h1>
            <span hidden={item.alternativeTitles.length === 0}>
              <OverlayTrigger overlay={alternativePopover}>
                <FontAwesomeIcon
                  className="mx-2"
                  icon={fasClone}
                ></FontAwesomeIcon>
              </OverlayTrigger>
            </span>
          </Row> */}
          {detailBadges}
          {audioBadges}
          {languageBadges}
          <Title>{item.overview}</Title>
        </Stack>
      </Grid.Col>
    </Grid>
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
  <Badge title={desc} color="secondary" className="mr-2 my-1 text-truncate">
    <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    <span className="ml-1">{children}</span>
  </Badge>
);

export default ItemOverview;
