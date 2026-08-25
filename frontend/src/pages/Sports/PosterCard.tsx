import { FunctionComponent } from "react";
import { Group, Progress, Tooltip } from "@mantine/core";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Action } from "@/components";
import { PosterCard } from "@/components/cards";

interface Props {
  item: Item.SportsLeague;
  onEdit: () => void;
}

const SportsLeaguePosterCard: FunctionComponent<Props> = ({ item, onEdit }) => {
  const {
    title,
    poster,
    monitored,
    sport,
    profileId,
    episodeFileCount,
    episodeMissingCount,
    sportarrLeagueId,
  } = item;

  const label = `${episodeFileCount - episodeMissingCount}/${episodeFileCount}`;

  const value =
    episodeFileCount === 0 || !profileId
      ? 0
      : (1.0 - episodeMissingCount / episodeFileCount) * 100.0;

  return (
    <PosterCard
      title={title}
      // A league runs on and has no release year, so the sport goes in the
      // slot a series year takes.
      year={sport}
      poster={poster}
      to={`/sports/${sportarrLeagueId}`}
      header={
        <Group gap="xs" wrap="nowrap">
          <FontAwesomeIcon
            title={monitored ? "monitored" : "unmonitored"}
            icon={monitored ? faBookmark : farBookmark}
          ></FontAwesomeIcon>
        </Group>
      }
      actions={
        <Action
          label="Edit League"
          icon={faWrench}
          size="sm"
          variant="filled"
          onClick={onEdit}
        ></Action>
      }
    >
      <Tooltip label={`Events with subtitles: ${label}`}>
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

export default SportsLeaguePosterCard;
