import { FunctionComponent } from "react";
import { Group, Progress, Tooltip } from "@mantine/core";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faPlay,
  faStop,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Action } from "@/components";
import { PosterCard } from "@/components/cards";

interface Props {
  item: Item.Series;
  onEdit: () => void;
}

const SeriesPosterCard: FunctionComponent<Props> = ({ item, onEdit }) => {
  const {
    title,
    year,
    poster,
    monitored,
    ended,
    profileId,
    episodeFileCount,
    episodeMissingCount,
    sonarrSeriesId,
  } = item;

  const label = `${episodeFileCount - episodeMissingCount}/${episodeFileCount}`;

  const value =
    episodeFileCount === 0 || !profileId
      ? 0
      : (1.0 - episodeMissingCount / episodeFileCount) * 100.0;

  return (
    <PosterCard
      title={title}
      year={year}
      poster={poster}
      to={`/series/${sonarrSeriesId}`}
      header={
        <Group gap="xs" wrap="nowrap">
          <FontAwesomeIcon
            title={monitored ? "monitored" : "unmonitored"}
            icon={monitored ? faBookmark : farBookmark}
          ></FontAwesomeIcon>
          <FontAwesomeIcon
            title={ended ? "Ended" : "Continuing"}
            icon={ended ? faStop : faPlay}
          ></FontAwesomeIcon>
        </Group>
      }
      actions={
        <Action
          label="Edit Series"
          icon={faWrench}
          size="sm"
          variant="filled"
          onClick={onEdit}
        ></Action>
      }
    >
      <Tooltip label={`Episodes with subtitles: ${label}`}>
        <Progress.Root size="sm" mt={4}>
          <Progress.Section
            value={value}
            color={episodeMissingCount === 0 ? "brand" : "warning"}
          ></Progress.Section>
        </Progress.Root>
      </Tooltip>
    </PosterCard>
  );
};

export default SeriesPosterCard;
