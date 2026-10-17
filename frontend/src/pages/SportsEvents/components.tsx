import { FunctionComponent, useMemo, useState } from "react";
import { Badge, MantineColor, Menu } from "@mantine/core";
import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useSportsSubtitleModification } from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import { useModals } from "@/modules/modals";

interface Props {
  leagueId: number;
  eventId: number;
  missing?: boolean;
  subtitle: Subtitle;
}

export const SportsSubtitle: FunctionComponent<Props> = ({
  leagueId,
  eventId,
  missing = false,
  subtitle,
}) => {
  const { remove, download } = useSportsSubtitleModification();

  const modals = useModals();

  const [opened, setOpen] = useState(false);

  const isEmbedded = subtitle.path === null;

  const variant: MantineColor | undefined = useMemo(() => {
    if (opened && !isEmbedded) {
      return "highlight";
    } else if (missing) {
      return "warning";
    } else if (isEmbedded) {
      return "disabled";
    }
  }, [isEmbedded, missing, opened]);

  // An embedded track lives inside the media file, so it can be neither
  // searched for nor deleted.
  const showSearch = missing;
  const showDelete = !missing && !isEmbedded;

  return (
    <Menu
      withArrow
      withinPortal
      position="left-end"
      trigger="hover"
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
    >
      <Menu.Target>
        <Badge variant={variant}>
          <Language.Text value={subtitle} long={false}></Language.Text>
        </Badge>
      </Menu.Target>
      <Menu.Dropdown>
        {(showSearch || showDelete) && <Menu.Label>Actions</Menu.Label>}
        {showSearch && (
          <Menu.Item
            leftSection={<FontAwesomeIcon icon={faSearch}></FontAwesomeIcon>}
            onClick={() => {
              void download.mutateAsync({
                leagueId,
                eventId,
                form: {
                  language: subtitle.code2,
                  hi: subtitle.hi,
                  forced: subtitle.forced,
                },
              });
            }}
          >
            Search
          </Menu.Item>
        )}
        {showDelete && (
          <Menu.Item
            color="danger"
            leftSection={<FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>}
            onClick={() => {
              modals.openConfirmModal({
                title: "The following subtitles will be deleted",
                children: subtitle.path,
                labels: { confirm: "Delete", cancel: "Cancel" },
                confirmProps: { color: "red" },
                onConfirm: () => {
                  if (subtitle.path) {
                    void remove.mutateAsync({
                      leagueId,
                      eventId,
                      form: {
                        language: subtitle.code2,
                        hi: subtitle.hi,
                        forced: subtitle.forced,
                        path: subtitle.path,
                      },
                    });
                  }
                },
              });
            }}
          >
            Delete
          </Menu.Item>
        )}
      </Menu.Dropdown>
    </Menu>
  );
};
