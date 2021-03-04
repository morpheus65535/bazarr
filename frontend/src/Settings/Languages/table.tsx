import { faTrash, faWrench } from "@fortawesome/free-solid-svg-icons";
import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Badge, Button, ButtonGroup } from "react-bootstrap";
import { Column, TableUpdater } from "react-table";
import { useProfiles } from ".";
import { ActionIcon, SimpleTable, useShowModal } from "../../components";
import { useLocalUpdater } from "../components";
import { languageProfileKey } from "../keys";
import Modal from "./modal";
import { anyCutoff } from "./options";

const Table: FunctionComponent = () => {
  const originalProfiles = useProfiles();

  const [profiles, setProfiles] = useState([...originalProfiles]);

  const nextProfileId = useMemo(
    () =>
      1 +
      profiles.reduce<number>((val, prof) => Math.max(prof.profileId, val), 0),
    [profiles]
  );

  const update = useLocalUpdater();

  const showModal = useShowModal();

  const submitProfiles = useCallback(
    (list: Profile.Languages[]) => {
      update(list, languageProfileKey);
      setProfiles(list);
    },
    [update]
  );

  const updateProfile = useCallback(
    (profile: Profile.Languages) => {
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

  const updateRow = useCallback<TableUpdater<Profile.Languages>>(
    (row, item?: Profile.Languages) => {
      if (item) {
        showModal("profile", item);
      } else {
        const list = [...profiles];
        list.splice(row.index, 1);
        submitProfiles(list);
      }
    },
    [submitProfiles, showModal, profiles]
  );

  const columns = useMemo<Column<Profile.Languages>[]>(
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
              <ActionIcon
                icon={faWrench}
                onClick={() => {
                  update && update(row, profile);
                }}
              ></ActionIcon>
              <ActionIcon
                icon={faTrash}
                onClick={() => update && update(row)}
              ></ActionIcon>
            </ButtonGroup>
          );
        },
      },
    ],
    []
  );

  return (
    <React.Fragment>
      <SimpleTable
        columns={columns}
        data={profiles}
        update={updateRow}
      ></SimpleTable>
      <Button
        block
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
        Add New Profile
      </Button>
      <Modal update={updateProfile} modalKey="profile"></Modal>
    </React.Fragment>
  );
};

interface ItemProps {
  className?: string;
  item: Profile.Item;
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
      title={cutoff ? "Ignore others if this one is avaliable" : undefined}
      variant={cutoff ? "primary" : "secondary"}
    >
      {text}
    </Badge>
  );
};

export default Table;
