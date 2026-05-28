import React, { FunctionComponent, useMemo } from "react";
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
  Stack,
  Text,
  Title,
  Tooltip,
} from "@mantine/core";
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
import { Language } from "@/components/bazarr";
import { BuildKey } from "@/utilities";
import {
  normalizeAudioLanguage,
  useLanguageProfileBy,
  useProfileItemsToLanguages,
} from "@/utilities/languages";

interface Props {
  item: Item.Base | null;
  details?: { icon: IconDefinition; text: string }[];
}

const ItemOverview: FunctionComponent<Props> = (props) => {
  const { item, details } = props;

  const detailBadges = useMemo(() => {
    const badges: (React.JSX.Element | null)[] = [];

    if (item) {
      badges.push(
        <ItemBadge
          key="file-path"
          icon={faFolder}
          title="File Path"
          styles={{
            root: { overflow: "unset" },
            label: { overflow: "hidden" },
          }}
        >
          <Tooltip
            label={item.path}
            multiline
            style={{ overflowWrap: "anywhere" }}
            events={{ hover: true, focus: false, touch: true }}
          >
            <span>{item.path}</span>
          </Tooltip>
        </ItemBadge>,
      );

      badges.push(
        ...(details?.map((val, idx) => (
          <ItemBadge key={BuildKey(idx, "detail", val.text)} icon={val.icon}>
            {val.text}
          </ItemBadge>
        )) ?? []),
      );

      if (item.tags.length > 0) {
        badges.push(
          <ItemBadge key="tags" icon={faTags} title="Tags">
            {item.tags.join("|")}
          </ItemBadge>,
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
          {normalizeAudioLanguage(v.name)}
        </ItemBadge>
      )) ?? [],
    [item?.audio_language],
  );

  const profile = useLanguageProfileBy(item?.profileId);
  const profileItems = useProfileItemsToLanguages(profile);

  const languageBadges = useMemo(() => {
    const badges: (React.JSX.Element | null)[] = [];

    if (profile) {
      badges.push(
        <ItemBadge
          key="language-profile"
          icon={faStream}
          title="Languages Profile"
        >
          {profile.name}
        </ItemBadge>,
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
        )),
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
        }}
        styles={{
          inner: { flexWrap: "nowrap" },
        }}
      >
        <Grid.Col span={1} visibleFrom="sm">
          <Image src={item?.poster} mx="auto" maw="250px"></Image>
        </Grid.Col>
        <Grid.Col span={8} maw="100%" style={{ overflow: "hidden" }}>
          <Stack align="flex-start" gap="xs" mx={6}>
            <Group align="flex-start" wrap="nowrap" maw="100%">
              <Title my={0}>
                <Text inherit c="white">
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
                  <Text hidden={item?.alternativeTitles.length === 0} c="white">
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
            <Group gap="xs" maw="100%">
              {detailBadges}
            </Group>
            <Group gap="xs" maw="100%">
              {audioBadges}
            </Group>
            <Group gap="xs" maw="100%">
              {languageBadges}
            </Group>
            <Text size="sm" c="white">
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
    variant="light"
    radius="sm"
    size="sm"
    style={{ textTransform: "none" }}
    aria-label={title}
    {...props}
  ></Badge>
);

export default ItemOverview;
