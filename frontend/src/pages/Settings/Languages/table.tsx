import { Fragment, FunctionComponent, useCallback, useMemo } from "react";
import { Badge, Button, Group, Text } from "@mantine/core";
import { faTrash, faWrench } from "@fortawesome/free-solid-svg-icons";
import { cloneDeep, includes, maxBy } from "lodash";
import { Action } from "@/components";
import { EnhancedProfileEditModal } from "@/components/forms/EnhancedProfileEditForm";
import {
  anyCutoff,
  ProfileEditModal,
} from "@/components/forms/ProfileEditForm";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import SimpleTable from "@/components/tables/SimpleTable";
import { useModals } from "@/modules/modals";
import { languageProfileKey } from "@/pages/Settings/keys";
import {
  HookType,
  useFormActions,
} from "@/pages/Settings/utilities/FormValues";
import { BuildKey, useArrayAction } from "@/utilities";
import { snakeCaseKeys } from "@/utilities/case";
import {
  useLatestEnabledLanguages,
  useLatestProfiles,
} from "./useLatestLanguages";

const Table: FunctionComponent = () => {
  const profiles = useLatestProfiles();

  const languages = useLatestEnabledLanguages();

  const nextProfileId = useMemo(
    () =>
      1 +
      profiles.reduce<number>((val, prof) => Math.max(prof.profileId, val), 0),
    [profiles],
  );

  const { setValue } = useFormActions();

  const modals = useModals();

  const submitProfiles = useCallback(
    (list: Language.Profile[]) => {
      setValue(list, languageProfileKey, ((value: Language.Profile[]) => {
        const raw: Language.RawProfileSubmission[] = value.map(
          ({ groups, ...profile }) => ({
            ...profile,
            // Enhanced profiles keep their groups. Their flat items are derived and must not be saved.
            items:
              profile.profileType === "enhanced" && groups
                ? {
                    groups: snakeCaseKeys(
                      groups,
                    ) as unknown as Language.RawEnhancedGroup[],
                  }
                : profile.items.map(
                    (item) =>
                      snakeCaseKeys(item) as unknown as Language.RawProfileItem,
                  ),
          }),
        );

        return JSON.stringify(raw);
      }) as HookType);
    },
    [setValue],
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
    [profiles, submitProfiles],
  );

  const action = useArrayAction<Language.Profile>((fn) => {
    const list = [...profiles];
    submitProfiles(fn(list));
  });

  const columns = useMemo<ColumnDef<Language.Profile>[]>(
    () => [
      {
        header: "Name",
        accessorKey: "name",
      },
      {
        header: "Tag",
        accessorKey: "tag",
      },
      {
        header: "Languages",
        accessorKey: "items",
        cell: ({
          row: {
            original: { items, cutoff, profileType, groups },
          },
        }) => {
          if (profileType === "enhanced" && groups) {
            return <GroupsExpression groups={groups} cutoff={cutoff} />;
          }

          return (
            <Group gap="xs" wrap="nowrap">
              {items.map((v, i) => {
                const isCutoff = v.id === cutoff || cutoff === anyCutoff;
                return (
                  <ItemBadge key={i} cutoff={isCutoff} item={v}></ItemBadge>
                );
              })}
            </Group>
          );
        },
      },
      {
        header: "Must contain",
        accessorKey: "mustContain",
        cell: ({
          row: {
            original: { mustContain },
          },
        }) => {
          if (!mustContain) {
            return null;
          }
          return (
            <>
              {mustContain.map((v, idx) => {
                return (
                  <Badge key={BuildKey(idx, v)} color="secondary">
                    {v}
                  </Badge>
                );
              })}
            </>
          );
        },
      },
      {
        header: "Must not contain",
        accessorKey: "mustNotContain",
        cell: ({
          row: {
            original: { mustNotContain },
          },
        }) => {
          if (!mustNotContain) {
            return null;
          }
          return (
            <>
              {mustNotContain.map((v, idx) => {
                return (
                  <Badge key={BuildKey(idx, v)} color="secondary">
                    {v}
                  </Badge>
                );
              })}
            </>
          );
        },
      },
      {
        id: "profileId",
        cell: ({ row }) => {
          const profile = row.original;
          return (
            <Group gap="xs" wrap="nowrap">
              <Action
                label="Edit Profile"
                icon={faWrench}
                c="secondary"
                onClick={() => {
                  if (profile.profileType === "enhanced") {
                    modals.openContextModal(EnhancedProfileEditModal, {
                      languages,
                      profile: cloneDeep(profile),
                      onComplete: updateProfile,
                    });
                    return;
                  }

                  const lastId = maxBy(profile.items, "id")?.id || 0;

                  // We once had an issue on the past where there were duplicated
                  // item ids that needs to become unique upon editing.
                  const sanitizedProfile = {
                    ...cloneDeep(profile),
                    items: profile.items.reduce(
                      (acc, value) => {
                        const { ids, duplicatedIds, items } = acc;

                        // We once had an issue on the past where there were duplicated
                        // item ids that needs to become unique upon editing.
                        if (includes(ids, value.id)) {
                          duplicatedIds.push(value.id);
                          items.push({
                            ...value,
                            id: lastId + duplicatedIds.length,
                          });

                          return acc;
                        }

                        ids.push(value.id);
                        items.push(value);

                        return acc;
                      },
                      {
                        ids: [] as number[],
                        duplicatedIds: [] as number[],
                        items: [] as typeof profile.items,
                      },
                    ).items,
                    tag: profile.tag || undefined,
                  };

                  modals.openContextModal(ProfileEditModal, {
                    languages,
                    profile: sanitizedProfile,
                    onComplete: updateProfile,
                  });
                }}
              ></Action>
              <Action
                label="Remove"
                icon={faTrash}
                c="danger"
                onClick={() => action.remove(row.index)}
              ></Action>
            </Group>
          );
        },
      },
    ],
    // TODO: Optimize this
    [action, languages, modals, updateProfile],
  );

  const canAdd = languages.length !== 0;

  return (
    <>
      <SimpleTable columns={columns} data={[...profiles]}></SimpleTable>
      <Button
        fullWidth
        disabled={!canAdd}
        onClick={() => {
          const profile = {
            profileId: nextProfileId,
            name: "",
            tag: undefined,
            items: [],
            cutoff: null,
            mustContain: [],
            mustNotContain: [],
            originalFormat: false,
          };
          modals.openContextModal(ProfileEditModal, {
            languages,
            profile,
            onComplete: updateProfile,
          });
        }}
      >
        {canAdd ? "Add New Profile" : "No Enabled Languages"}
      </Button>
      <Button
        fullWidth
        variant="light"
        disabled={!canAdd}
        onClick={() => {
          const profile: Language.Profile = {
            profileId: nextProfileId,
            name: "",
            tag: undefined,
            profileType: "enhanced",
            items: [],
            groups: [],
            cutoff: null,
            mustContain: [],
            mustNotContain: [],
            originalFormat: false,
          };
          modals.openContextModal(EnhancedProfileEditModal, {
            languages,
            profile,
            onComplete: updateProfile,
          });
        }}
      >
        {canAdd ? "Add New Enhanced Profile" : "No Enabled Languages"}
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
    const result =
      item.language +
      (item.hi === "True"
        ? ":HI"
        : item.forced === "True"
          ? ":Forced"
          : item.hi === "Excluded"
            ? ":Non-HI"
            : "");
    return result;
  }, [item.hi, item.forced, item.language]);
  return (
    <Badge
      title={cutoff ? "Ignore others if this one is available" : undefined}
      color={cutoff ? "brand" : "secondary"}
    >
      {text}
    </Badge>
  );
};

interface GroupsProps {
  groups: Language.EnhancedGroup[];
  cutoff: number | null;
}

// Renders an enhanced profile as an expression, for example (en AND fr) > de. The cutoff group is highlighted.
const GroupsExpression: FunctionComponent<GroupsProps> = ({
  groups,
  cutoff,
}) => {
  return (
    <Group gap="xs" wrap="nowrap">
      {groups.map((group, groupIndex) => {
        const isCutoff = group.id === cutoff || cutoff === anyCutoff;
        const parenthesized = group.items.length > 1;

        return (
          <Fragment key={group.id}>
            {groupIndex > 0 && (
              <Text span c="dimmed">
                &gt;
              </Text>
            )}
            {parenthesized && (
              <Text span c="dimmed">
                (
              </Text>
            )}
            {group.items.map((item, itemIndex) => (
              <Fragment key={item.id}>
                {itemIndex > 0 && (
                  <Text span size="sm" c="dimmed">
                    {group.operator}
                  </Text>
                )}
                <ItemBadge cutoff={isCutoff} item={item}></ItemBadge>
              </Fragment>
            ))}
            {parenthesized && (
              <Text span c="dimmed">
                )
              </Text>
            )}
          </Fragment>
        );
      })}
    </Group>
  );
};

export default Table;
