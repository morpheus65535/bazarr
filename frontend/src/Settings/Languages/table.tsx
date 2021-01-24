import { faWrench, faTrash } from "@fortawesome/free-solid-svg-icons";
import React, {
  FunctionComponent,
  useMemo,
  useState,
  useCallback,
} from "react";
import { Badge, Button } from "react-bootstrap";
import { Column } from "react-table";
import { ActionIcon, BasicTable } from "../../components";

import Modal from "./modal";

interface Props {
  languages: Language[];
  profiles: LanguagesProfile[];
  setProfiles: (profiles: LanguagesProfile[]) => void;
}

const Table: FunctionComponent<Props> = ({
  languages,
  profiles,
  setProfiles,
}) => {
  const [modal, setModal] = useState(false);

  const [active, setActive] = useState<LanguagesProfile>({
    profileId: -1,
    name: "",
    items: [],
    cutoff: null,
  });

  const showModal = useCallback(
    (profile: LanguagesProfile | undefined = undefined) => {
      if (profile === undefined) {
        const id =
          1 +
          profiles.reduce<number>(
            (val, prof) => Math.max(prof.profileId, val),
            0
          );
        profile = {
          profileId: id,
          name: "",
          items: [],
          cutoff: null,
        };
      }

      setActive(profile);
      setModal(true);
    },
    [profiles]
  );

  const hideModal = useCallback(() => {
    setModal(false);
  }, []);

  const updateProfile = useCallback(
    (profile: LanguagesProfile) => {
      const list = [...profiles];
      const idx = list.findIndex((v) => v.profileId === profile.profileId);

      if (idx !== -1) {
        list[idx] = profile;
      } else {
        list.push(profile);
      }
      setProfiles(list);
    },
    [profiles, setProfiles]
  );

  const removeProfile = useCallback(
    (id: number) => {
      const list = [...profiles];
      const idx = list.findIndex((v) => v.profileId === id);

      if (idx !== -1) {
        list.splice(idx, 1);
        setProfiles(list);
      }
    },
    [profiles, setProfiles]
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
                  showModal(profile);
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
      <Button block variant="light" onClick={() => showModal()}>
        Add New Profile
      </Button>
      <Modal
        key={active?.profileId ?? 0}
        languages={languages}
        profile={active}
        update={updateProfile}
        show={modal}
        onClose={hideModal}
      ></Modal>
    </React.Fragment>
  );
};

export default Table;
