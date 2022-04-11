import { Language } from "@/components/bazarr";
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
  faClone,
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
  List,
  MediaQuery,
  Popover,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useHover } from "@mantine/hooks";
import { FunctionComponent, useMemo } from "react";

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

  const { ref, hovered } = useHover();

  return (
    <BackgroundImage src={item?.fanart ?? ""}>
      <Grid
        align="flex-start"
        grow
        gutter="xs"
        p={24}
        m={0}
        style={{ backgroundColor: "rgba(0,0,0,0.7)", flexWrap: "nowrap" }}
      >
        <MediaQuery smallerThan="sm" styles={{ display: "none" }}>
          <Grid.Col span={3}>
            <Image src={item?.poster} withPlaceholder></Image>
          </Grid.Col>
        </MediaQuery>
        <Grid.Col span={8}>
          <Stack align="flex-start" spacing="xs" mx={6}>
            <Group align="flex-start" noWrap>
              <Title my={0}>
                <Text inherit color="white">
                  {item && isMovie(item) ? (
                    <Box component="span" mr={12}>
                      <FontAwesomeIcon
                        title={item.monitored ? "monitored" : "unmonitored"}
                        icon={item.monitored ? faBookmark : farBookmark}
                      ></FontAwesomeIcon>
                    </Box>
                  ) : null}
                  {item?.title}
                </Text>
              </Title>
              <Popover
                opened={hovered}
                position="bottom"
                withArrow
                target={
                  <Text
                    hidden={item?.alternativeTitles.length === 0}
                    color="white"
                    ref={ref}
                  >
                    <FontAwesomeIcon icon={faClone} />
                  </Text>
                }
              >
                <List>
                  {item?.alternativeTitles.map((v, idx) => (
                    <List.Item key={BuildKey(idx, v)}>{v}</List.Item>
                  ))}
                </List>
              </Popover>
            </Group>
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
  <Text size="xs" color="white">
    <Badge
      leftSection={<FontAwesomeIcon icon={icon}></FontAwesomeIcon>}
      radius="sm"
      title={desc}
      color="dark"
      size="sm"
      style={{ textTransform: "none" }}
    >
      {children}
    </Badge>
  </Text>
);

export default ItemOverview;
