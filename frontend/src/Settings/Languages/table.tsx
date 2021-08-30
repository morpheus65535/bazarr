import { faTrash, faWrench } from "@fortawesome/free-solid-svg-icons";
import { cloneDeep } from "lodash";
import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Badge, Button, ButtonGroup } from "react-bootstrap";
import { Column, TableUpdater } from "react-table";
import { useEnabledLanguagesContext, useProfilesContext } from ".";
import { ActionButton, SimpleTable, useShowModal } from "../../components";
import { useSingleUpdate } from "../components";
import { languageProfileKey } from "../keys";
import Modal from "./modal";
import { anyCutoff } from "./options";

const Table: FunctionComponent = () => {
  const originalProfiles = useProfilesContext();

  const languages = useEnabledLanguagesContext();

  const [profiles, setProfiles] = useState(() => cloneDeep(originalProfiles));

  const nextProfileId = useMemo(
    () =>
      1 +
      profiles.reduce<number>((val, prof) => Math.max(prof.profileId, val), 0),
    [profiles]
  );

  const update = useSingleUpdate();

  const showModal = useShowModal();

  const submitProfiles = useCallback(
    (list: Language.Profile[]) => {
      update(list, languageProfileKey);
      setProfiles(list);
    },
    [update]
  );

  const updateProfile = useCallback(
    (profile: Language.Profile) => {
      const list = [...profiles];
      const idx = list.findIndex((v) => v.profileId === profile.profileId);

      if (idx !== -1) {
        list[idx] = profile;
      } else {
        list.push(profile);
      }
      submitProfiles(list);
    },
    [profiles, submitProfiles]
  );

  const updateRow = useCallback<TableUpdater<Language.Profile>>(
    (row, item?: Language.Profile) => {
      if (item) {
        showModal("profile", cloneDeep(item));
      } else {
        const list = [...profiles];
        list.splice(row.index, 1);
        submitProfiles(list);
      }
    },
    [submitProfiles, showModal, profiles]
  );

  const columns = useMemo<Column<Language.Profile>[]>(
    () => [
      {
        Header: "Name",
        accessor: "name",
      },
      {
        Header: "Languages",
        accessor: "items",
        Cell: (row) => {
          const items = row.value;
          const cutoff = row.row.original.cutoff;
          return items.map((v) => {
            const isCutoff = v.id === cutoff || cutoff === anyCutoff;
            return (
              <ItemBadge
                key={v.id}
                cutoff={isCutoff}
                className="mx-1"
                item={v}
              ></ItemBadge>
            );
          });
        },
      },
      {
        accessor: "profileId",
        Cell: ({ row, update }) => {
          const profile = row.original;

          return (
            <ButtonGroup>
              <ActionButton
                icon={faWrench}
                onClick={() => {
                  update && update(row, profile);
                }}
              ></ActionButton>
              <ActionButton
                icon={faTrash}
                onClick={() => update && update(row)}
              ></ActionButton>
            </ButtonGroup>
          );
        },
      },
    ],
    []
  );

  const canAdd = languages.length !== 0;

  return (
    <React.Fragment>
      <SimpleTable
        columns={columns}
        data={profiles}
        update={updateRow}
      ></SimpleTable>
      <Button
        block
        disabled={!canAdd}
        variant="light"
        onClick={() => {
          const profile = {
            profileId: nextProfileId,
            name: "",
            items: [],
            cutoff: null,
          };
          showModal("profile", profile);
        }}
      >
        {canAdd ? "Add New Profile" : "No Enabled Languages"}
      </Button>
      <Modal update={updateProfile} modalKey="profile"></Modal>
    </React.Fragment>
  );
};

interface ItemProps {
  className?: string;
  item: Language.ProfileItem;
  cutoff: boolean;
}

const ItemBadge: FunctionComponent<ItemProps> = ({
  cutoff,
  item,
  className,
}) => {
  const text = useMemo(() => {
    let result = item.language;
    if (item.hi === "True") {
      result += ":HI";
    } else if (item.forced === "True") {
      result += ":Forced";
    }
    return result;
  }, [item.hi, item.forced, item.language]);
  return (
    <Badge
      className={className}
      title={cutoff ? "Ignore others if this one is available" : undefined}
      variant={cutoff ? "primary" : "secondary"}
    >
      {text}
    </Badge>
  );
};

export default Table;
