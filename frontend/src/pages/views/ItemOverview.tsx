import { Language } from "@/components/bazarr";
import { BuildKey } from "@/utilities";
import {
  useLanguageProfileBy,
  useProfileItemsToLanguages,
} from "@/utilities/languages";
import {
  faFolder,
  faBookmark as farBookmark,
} from "@fortawesome/free-regular-svg-icons";
import {
  IconDefinition,
  faBookmark,
  faClone,
  faLanguage,
  faMusic,
  faStream,
  faTags,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  BackgroundImage,
  Badge,
  BadgeProps,
  Box,
  Grid,
  Group,
  HoverCard,
  Image,
  List,
  MediaQuery,
  Stack,
  Text,
  Title,
  createStyles,
} from "@mantine/core";
import { FunctionComponent, useMemo } from "react";

interface Props {
  item: Item.Base | null;
  details?: { icon: IconDefinition; text: string }[];
}

const useStyles = createStyles((theme) => {
  return {
    poster: {
      maxWidth: "250px",
    },
    col: {
      maxWidth: "100%",
    },
    group: {
      maxWidth: "100%",
    },
  };
});

const ItemOverview: FunctionComponent<Props> = (props) => {
  const { item, details } = props;

  const { classes } = useStyles();

  const detailBadges = useMemo(() => {
    const badges: (JSX.Element | null)[] = [];

    if (item) {
      badges.push(
        <ItemBadge key="file-path" icon={faFolder} title="File Path">
          {item.path}
        </ItemBadge>
      );

      badges.push(
        ...(details?.map((val, idx) => (
          <ItemBadge key={BuildKey(idx, "detail", val.text)} icon={val.icon}>
            {val.text}
          </ItemBadge>
        )) ?? [])
      );

      if (item.tags.length > 0) {
        badges.push(
          <ItemBadge key="tags" icon={faTags} title="Tags">
            {item.tags.join("|")}
          </ItemBadge>
        );
      }
    }

    return badges;
  }, [details, item]);

  const audioBadges = useMemo(
    () =>
      item?.audio_language.map((v, idx) => (
        <ItemBadge
          key={BuildKey(idx, "audio", v.code2)}
          icon={faMusic}
          title="Audio Language"
        >
          {v.name}
        </ItemBadge>
      )) ?? [],
    [item?.audio_language]
  );

  const profile = useLanguageProfileBy(item?.profileId);
  const profileItems = useProfileItemsToLanguages(profile);

  const languageBadges = useMemo(() => {
    const badges: (JSX.Element | null)[] = [];

    if (profile) {
      badges.push(
        <ItemBadge
          key="language-profile"
          icon={faStream}
          title="Languages Profile"
        >
          {profile.name}
        </ItemBadge>
      );

      badges.push(
        ...profileItems.map((v, idx) => (
          <ItemBadge
            key={BuildKey(idx, "lang", v.code2)}
            icon={faLanguage}
            title="Language"
          >
            <Language.Text long value={v}></Language.Text>
          </ItemBadge>
        ))
      );
    }

    return badges;
  }, [profile, profileItems]);

  return (
    <BackgroundImage src={item?.fanart ?? ""}>
      <Grid
        align="flex-start"
        grow
        gutter="xs"
        p={24}
        m={0}
        style={{
          backgroundColor: "rgba(0,0,0,0.7)",
          flexWrap: "nowrap",
        }}
      >
        <MediaQuery smallerThan="sm" styles={{ display: "none" }}>
          <Grid.Col span={3}>
            <Image
              src={item?.poster}
              mx="auto"
              className={classes.poster}
              withPlaceholder
            ></Image>
          </Grid.Col>
        </MediaQuery>
        <Grid.Col span={8} className={classes.col}>
          <Stack align="flex-start" spacing="xs" mx={6}>
            <Group align="flex-start" noWrap className={classes.group}>
              <Title my={0}>
                <Text inherit color="white">
                  <Box component="span" mr={12}>
                    <FontAwesomeIcon
                      title={item?.monitored ? "monitored" : "unmonitored"}
                      icon={item?.monitored ? faBookmark : farBookmark}
                    ></FontAwesomeIcon>
                  </Box>
                  {item?.title}
                </Text>
              </Title>
              <HoverCard position="bottom" withArrow>
                <HoverCard.Target>
                  <Text
                    hidden={item?.alternativeTitles.length === 0}
                    color="white"
                  >
                    <FontAwesomeIcon icon={faClone} />
                  </Text>
                </HoverCard.Target>
                <HoverCard.Dropdown>
                  <List>
                    {item?.alternativeTitles.map((v, idx) => (
                      <List.Item key={BuildKey(idx, v)}>{v}</List.Item>
                    ))}
                  </List>
                </HoverCard.Dropdown>
              </HoverCard>
            </Group>
            <Group spacing="xs" className={classes.group}>
              {detailBadges}
            </Group>
            <Group spacing="xs" className={classes.group}>
              {audioBadges}
            </Group>
            <Group spacing="xs" className={classes.group}>
              {languageBadges}
            </Group>
            <Text size="sm" color="white">
              {item?.overview}
            </Text>
          </Stack>
        </Grid.Col>
      </Grid>
    </BackgroundImage>
  );
};

type ItemBadgeProps = Omit<BadgeProps, "leftSection"> & {
  icon: IconDefinition;
  title?: string;
};

const ItemBadge: FunctionComponent<ItemBadgeProps> = ({
  icon,
  title,
  ...props
}) => (
  <Badge
    leftSection={<FontAwesomeIcon icon={icon}></FontAwesomeIcon>}
    radius="sm"
    color="dark"
    size="sm"
    style={{ textTransform: "none" }}
    aria-label={title}
    {...props}
  ></Badge>
);

export default ItemOverview;
