import { Action, SimpleTable } from "@/components";
import { useModals } from "@/modules/modals";
import { LOG } from "@/utilities/console";
import { faTrash, faWrench } from "@fortawesome/free-solid-svg-icons";
import { Badge, Button, Group } from "@mantine/core";
import { cloneDeep } from "lodash";
import {
  createContext,
  FunctionComponent,
  useCallback,
  useContext,
  useMemo,
} from "react";
import { Column } from "react-table";
import { useLatestEnabledLanguages, useLatestProfiles } from ".";
import { useSingleUpdate } from "../components";
import { languageProfileKey } from "../keys";
import Modal from "./modal";
import { anyCutoff } from "./options";

type ModifyFn = (index: number, item?: Language.Profile) => void;

const RowContext = createContext<ModifyFn>(() => {
  LOG("error", "RowContext not initialized");
});

function useRowMutation() {
  return useContext(RowContext);
}

const Table: FunctionComponent = () => {
  const profiles = useLatestProfiles();

  const languages = useLatestEnabledLanguages();

  const nextProfileId = useMemo(
    () =>
      1 +
      profiles.reduce<number>((val, prof) => Math.max(prof.profileId, val), 0),
    [profiles]
  );

  const update = useSingleUpdate();

  const modals = useModals();

  const submitProfiles = useCallback(
    (list: Language.Profile[]) => {
      update(list, languageProfileKey);
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

  const mutateRow = useCallback<ModifyFn>(
    (index, item) => {
      if (item) {
        modals.openContextModal(Modal, {
          profile: cloneDeep(item),
          onComplete: updateProfile,
        });
      } else {
        const list = [...profiles];
        list.splice(index, 1);
        submitProfiles(list);
      }
    },
    [modals, updateProfile, profiles, submitProfiles]
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
              <ItemBadge key={v.id} cutoff={isCutoff} item={v}></ItemBadge>
            );
          });
        },
      },
      {
        Header: "Must contain",
        accessor: "mustContain",
        Cell: (row) => {
          const items = row.value;
          if (!items) {
            return false;
          }
          return items.map((v) => {
            return <Badge color="gray">{v}</Badge>;
          });
        },
      },
      {
        Header: "Must not contain",
        accessor: "mustNotContain",
        Cell: (row) => {
          const items = row.value;
          if (!items) {
            return false;
          }
          return items.map((v) => {
            return <Badge color="gray">{v}</Badge>;
          });
        },
      },
      {
        accessor: "profileId",
        Cell: ({ row }) => {
          const profile = row.original;
          const mutate = useRowMutation();

          return (
            <Group spacing="xs">
              <Action
                icon={faWrench}
                onClick={() => {
                  mutate(row.index, profile);
                }}
              ></Action>
              <Action icon={faTrash} onClick={() => mutate(row.index)}></Action>
            </Group>
          );
        },
      },
    ],
    []
  );

  const canAdd = languages.length !== 0;

  return (
    <>
      <RowContext.Provider value={mutateRow}>
        <SimpleTable columns={columns} data={profiles}></SimpleTable>
      </RowContext.Provider>
      <Button
        fullWidth
        disabled={!canAdd}
        color="light"
        onClick={() => {
          const profile = {
            profileId: nextProfileId,
            name: "",
            items: [],
            cutoff: null,
            mustContain: [],
            mustNotContain: [],
            originalFormat: false,
          };
          modals.openContextModal(Modal, {
            profile,
            onComplete: updateProfile,
          });
        }}
      >
        {canAdd ? "Add New Profile" : "No Enabled Languages"}
      </Button>
    </>
  );
};

interface ItemProps {
  item: Language.ProfileItem;
  cutoff: boolean;
}

const ItemBadge: FunctionComponent<ItemProps> = ({ cutoff, item }) => {
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
      title={cutoff ? "Ignore others if this one is available" : undefined}
      color={cutoff ? "primary" : "secondary"}
    >
      {text}
    </Badge>
  );
};

export default Table;
