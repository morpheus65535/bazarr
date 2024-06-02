import { useIsAnyMutationRunning, useLanguageProfiles } from "@/apis/hooks";
import { SimpleTable, Toolbox } from "@/components";
import { Selector, SelectorOption } from "@/components/inputs";
import { useCustomSelection } from "@/components/tables/plugins";
import { GetItemId, useSelectorOptions } from "@/utilities";
import { faCheck, faUndo } from "@fortawesome/free-solid-svg-icons";
import { Box, Container } from "@mantine/core";
import { uniqBy } from "lodash";
import { useCallback, useMemo, useState } from "react";
import { UseMutationResult } from "react-query";
import { useNavigate } from "react-router-dom";
import { Column, useRowSelect } from "react-table";

interface MassEditorProps<T extends Item.Base = Item.Base> {
  columns: Column<T>[];
  data: T[];
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem>;
}

function MassEditor<T extends Item.Base>(props: MassEditorProps<T>) {
  const { columns, data: raw, mutation } = props;

  const [selections, setSelections] = useState<T[]>([]);
  const [dirties, setDirties] = useState<T[]>([]);
  const hasTask = useIsAnyMutationRunning();
  const { data: profiles } = useLanguageProfiles();

  const navigate = useNavigate();

  const onEnded = useCallback(() => navigate(".."), [navigate]);

  const data = useMemo(
    () => uniqBy([...dirties, ...(raw ?? [])], GetItemId),
    [dirties, raw],
  );

  const profileOptions = useSelectorOptions(profiles ?? [], (v) => v.name);

  const profileOptionsWithAction = useMemo<
    SelectorOption<Language.Profile | null>[]
  >(
    () => [
      { label: "Clear", value: null, group: "Action" },
      ...profileOptions.options,
    ],
    [profileOptions.options],
  );

  const getKey = useCallback((value: Language.Profile | null) => {
    if (value) {
      return value.name;
    }

    return "Clear";
  }, []);

  const { mutateAsync } = mutation;

  const save = useCallback(() => {
    const form: FormType.ModifyItem = {
      id: [],
      profileid: [],
    };
    dirties.forEach((v) => {
      const id = GetItemId(v);
      if (id) {
        form.id.push(id);
        form.profileid.push(v.profileId);
      }
    });
    return mutateAsync(form);
  }, [dirties, mutateAsync]);

  const setProfiles = useCallback(
    (profile: Language.Profile | null) => {
      const id = profile?.profileId ?? null;
      const newItems = selections.map((v) => ({ ...v, profileId: id }));

      setDirties((dirty) => {
        return uniqBy([...newItems, ...dirty], GetItemId);
      });
    },
    [selections],
  );
  return (
    <Container fluid px={0}>
      <Toolbox>
        <Box>
          <Selector
            allowDeselect
            placeholder="Change Profile"
            options={profileOptionsWithAction}
            getkey={getKey}
            disabled={selections.length === 0}
            onChange={setProfiles}
          ></Selector>
        </Box>
        <Box>
          <Toolbox.Button icon={faUndo} onClick={onEnded}>
            Cancel
          </Toolbox.Button>
          <Toolbox.MutateButton
            icon={faCheck}
            disabled={dirties.length === 0 || hasTask}
            promise={save}
            onSuccess={onEnded}
          >
            Save
          </Toolbox.MutateButton>
        </Box>
      </Toolbox>
      <SimpleTable
        columns={columns}
        data={data}
        onSelect={setSelections}
        plugins={[useRowSelect, useCustomSelection]}
      ></SimpleTable>
    </Container>
  );
}

export default MassEditor;
