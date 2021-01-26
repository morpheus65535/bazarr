import { faWrench, faTrash } from "@fortawesome/free-solid-svg-icons";
import React, {
  FunctionComponent,
  useMemo,
  useState,
  useCallback,
} from "react";
import { Badge, Button } from "react-bootstrap";
import { Column } from "react-table";
import { ActionIcon, BasicTable, useShowModal } from "../../components";

import { useLanguagesProfile } from ".";

import Modal from "./modal";
import { useUpdate } from "../components";

import { languageProfileKey } from "../keys";

const Table: FunctionComponent = () => {
  const originalProfiles = useLanguagesProfile();

  const [profiles, setProfiles] = useState(originalProfiles);

  const nextProfileId = useMemo(
    () =>
      1 +
      profiles.reduce<number>((val, prof) => Math.max(prof.profileId, val), 0),
    [profiles]
  );

  const update = useUpdate();

  const showModal = useShowModal();

  const submitProfiles = useCallback(
    (list: LanguagesProfile[]) => {
      update(list, languageProfileKey);
      setProfiles(list);
    },
    [update]
  );

  const updateProfile = useCallback(
    (profile: LanguagesProfile) => {
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

  const removeProfile = useCallback(
    (id: number) => {
      const list = [...profiles];
      const idx = list.findIndex((v) => v.profileId === id);

      if (idx !== -1) {
        list.splice(idx, 1);
        submitProfiles(list);
      }
    },
    [profiles, submitProfiles]
  );

  const columns = useMemo<Column<LanguagesProfile>[]>(
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
          return items.map((v) => (
            <Badge key={v.id} className="mx-1" variant="secondary">
              {v.language}
            </Badge>
          ));
        },
      },
      {
        accessor: "profileId",
        Cell: (row) => {
          const profile = row.row.original;

          return (
            <React.Fragment>
              <ActionIcon
                icon={faWrench}
                onClick={() => {
                  showModal("profile", profile);
                }}
              ></ActionIcon>
              <ActionIcon
                icon={faTrash}
                onClick={() => removeProfile(profile.profileId)}
              ></ActionIcon>
            </React.Fragment>
          );
        },
      },
    ],
    [showModal, removeProfile]
  );

  return (
    <React.Fragment>
      <BasicTable
        showPageControl={false}
        columns={columns}
        data={profiles}
      ></BasicTable>
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

export default Table;
