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
import { PosterCard, PosterCardSelection } from "@/components/cards";

interface Props {
  item: Item.Series;
  onEdit: () => void;
  selection?: PosterCardSelection;
}

const SeriesPosterCard: FunctionComponent<Props> = ({
  item,
  onEdit,
  selection,
}) => {
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
          <Tooltip label={monitored ? "Monitored" : "Unmonitored"}>
            <FontAwesomeIcon
              icon={monitored ? faBookmark : farBookmark}
            ></FontAwesomeIcon>
          </Tooltip>
          <Tooltip label={ended ? "Ended" : "Continuing"}>
            <FontAwesomeIcon icon={ended ? faStop : faPlay}></FontAwesomeIcon>
          </Tooltip>
        </Group>
      }
      actions={
        selection ? undefined : (
          <Action
            label="Edit Series"
            icon={faWrench}
            size="sm"
            variant="filled"
            onClick={onEdit}
          ></Action>
        )
      }
      selection={selection}
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
