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
  MediaQuery,
  Stack,
  Text,
} from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import Language from "./bazarr/Language";

interface Props {
  item: Item.Base | null;
  details?: { icon: IconDefinition; text: string }[];
}

const ItemOverview: FunctionComponent<Props> = (props) => {
  const { item, details } = props;

  const detailBadges = useMemo(() => {
    const badges: (JSX.Element | null)[] = [];

    if (item) {
      badges.push(
        <IconBadge key="file-path" icon={faFolder} desc="File Path">
          {item.path}
        </IconBadge>
      );

      badges.push(
        ...(details?.map((val, idx) => (
          <IconBadge key={BuildKey(idx, "detail", val.text)} icon={val.icon}>
            {val.text}
          </IconBadge>
        )) ?? [])
      );

      if (item.tags.length > 0) {
        badges.push(
          <IconBadge key="tags" icon={faTags} desc="Tags">
            {item.tags.join("|")}
          </IconBadge>
        );
      }
    }

    return badges;
  }, [details, item]);

  const audioBadges = useMemo(
    () =>
      item?.audio_language.map((v, idx) => (
        <IconBadge
          key={BuildKey(idx, "audio", v.code2)}
          icon={faMusic}
          desc="Audio Language"
        >
          {v.name}
        </IconBadge>
      )) ?? [],
    [item?.audio_language]
  );

  const profile = useLanguageProfileBy(item?.profileId);
  const profileItems = useProfileItemsToLanguages(profile);

  const languageBadges = useMemo(() => {
    const badges: (JSX.Element | null)[] = [];

    if (profile) {
      badges.push(
        <IconBadge
          key="language-profile"
          icon={faStream}
          desc="Languages Profile"
        >
          {profile.name}
        </IconBadge>
      );

      badges.push(
        ...profileItems.map((v, idx) => (
          <IconBadge
            key={BuildKey(idx, "lang", v.code2)}
            icon={faLanguage}
            desc="Language"
          >
            <Language.Text long value={v}></Language.Text>
          </IconBadge>
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
    <BackgroundImage src={item?.fanart ?? ""}>
      <Grid align="flex-start" grow gutter="xs" m={24}>
        <MediaQuery smallerThan="sm" styles={{ display: "none" }}>
          <Grid.Col span={2}>
            <Image src={item?.poster} withPlaceholder></Image>
          </Grid.Col>
        </MediaQuery>
        <Grid.Col span={8}>
          <Stack align="flex-start" spacing="xs" mx={6}>
            <Group>
              <Text size="xl" weight="bold" color="white">
                <Box component="span" mr={6}>
                  {item && isMovie(item) ? (
                    <FontAwesomeIcon
                      title={item.monitored ? "monitored" : "unmonitored"}
                      icon={item.monitored ? faBookmark : farBookmark}
                    ></FontAwesomeIcon>
                  ) : null}
                </Box>
                {item?.title}
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
              {item?.overview}
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

const IconBadge: FunctionComponent<ItemBadgeProps> = ({
  icon,
  desc,
  children,
}) => (
  <Badge radius="sm" title={desc} color="dark" size="md">
    <Text inherit color="white">
      <Box component="span" mr={8}>
        <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
      </Box>
      {children}
    </Text>
  </Badge>
);

export default ItemOverview;
