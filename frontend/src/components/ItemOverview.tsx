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
import {
  BackgroundImage,
  Badge,
  Box,
  Grid,
  Group,
  Image,
  Stack,
  Text,
} from "@mantine/core";
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
    <BackgroundImage src={item.fanart}>
      <Grid align="flex-start" grow gutter="xs" m={24}>
        <Grid.Col span={2}>
          <Image src={item.poster} withPlaceholder></Image>
        </Grid.Col>
        <Grid.Col span={8}>
          <Stack align="flex-start" spacing="xs" mx={6}>
            <Group>
              <Text size="xl" weight="bold" color="white">
                <Box component="span" mr={6}>
                  {isMovie(item) ? (
                    <FontAwesomeIcon
                      title={item.monitored ? "monitored" : "unmonitored"}
                      icon={item.monitored ? faBookmark : farBookmark}
                    ></FontAwesomeIcon>
                  ) : null}
                </Box>
                {item.title}
              </Text>
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
            <Group spacing="xs">{detailBadges}</Group>
            <Group spacing="xs">{audioBadges}</Group>
            <Group spacing="xs">{languageBadges}</Group>
            <Text size="sm" color="white">
              {item.overview}
            </Text>
          </Stack>
        </Grid.Col>
      </Grid>
    </BackgroundImage>
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
  <Badge radius="sm" title={desc} color="dark" size="xs">
    <Text inherit color="white">
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
      {children}
    </Text>
  </Badge>
);

export default ItemOverview;
