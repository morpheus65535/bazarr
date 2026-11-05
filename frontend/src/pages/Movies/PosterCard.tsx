import { FunctionComponent } from "react";
import { Badge, Group, Stack, Tooltip } from "@mantine/core";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { uniqueId } from "lodash";
import { Action } from "@/components";
import Language from "@/components/bazarr/Language";
import { PosterCard, PosterCardSelection } from "@/components/cards";
import { BuildKey } from "@/utilities";

const MAX_VISIBLE_BADGES = 2;

interface Props {
  item: Item.Movie;
  onEdit: () => void;
  selection?: PosterCardSelection;
}

const MoviePosterCard: FunctionComponent<Props> = ({
  item,
  onEdit,
  selection,
}) => {
  const { title, year, poster, monitored, missingSubtitles, radarrId } = item;

  const visible = missingSubtitles.slice(0, MAX_VISIBLE_BADGES);
  const hidden = missingSubtitles.slice(MAX_VISIBLE_BADGES);

  return (
    <PosterCard
      title={title}
      year={year}
      poster={poster}
      to={`/movies/${radarrId}`}
      header={
        <Tooltip
          label={monitored ? "Monitored in Radarr" : "Unmonitored in Radarr"}
        >
          <FontAwesomeIcon
            icon={monitored ? faBookmark : farBookmark}
          ></FontAwesomeIcon>
        </Tooltip>
      }
      actions={
        selection ? undefined : (
          <Action
            label="Edit Movie"
            icon={faWrench}
            size="sm"
            variant="filled"
            onClick={onEdit}
          ></Action>
        )
      }
      selection={selection}
    >
      {missingSubtitles.length > 0 && (
        <Group gap={4} mt={4} wrap="nowrap">
          {visible.map((v) => (
            <Badge
              size="xs"
              color="warning"
              key={uniqueId(`${BuildKey(v.code2, v.hi, v.forced)}_`)}
            >
              <Language.Text value={v}></Language.Text>
            </Badge>
          ))}
          {hidden.length > 0 && (
            <Tooltip
              label={
                <Stack gap={2}>
                  {hidden.map((v) => (
                    <Language.Text
                      key={uniqueId(`${BuildKey(v.code2, v.hi, v.forced)}_`)}
                      value={v}
                    ></Language.Text>
                  ))}
                </Stack>
              }
            >
              <Badge size="xs" color="warning">
                +{hidden.length}
              </Badge>
            </Tooltip>
          )}
        </Group>
      )}
    </PosterCard>
  );
};

export default MoviePosterCard;
