import { useIsAnyMutationRunning, useLanguageProfiles } from "@/apis/hooks";
import { GetItemId } from "@/utilities";
import { faCheck, faUndo } from "@fortawesome/free-solid-svg-icons";
import { Container, Select } from "@mantine/core";
import { uniqBy } from "lodash";
import { useCallback, useMemo, useState } from "react";
import { UseMutationResult } from "react-query";
import { useNavigate } from "react-router-dom";
import { Column, useRowSelect } from "react-table";
import { ContentHeader, SimpleTable } from ".";
import { useCustomSelection } from "./tables/plugins";

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
    [dirties, raw]
  );

  // const profileOptions = useMemo(() => {
  //   const items: JSX.Element[] = [];
  //   if (profiles) {
  //     items.push(
  //       <Dropdown.Item key="clear-profile">Clear Profile</Dropdown.Item>
  //     );
  //     items.push(<Dropdown.Divider key="dropdown-divider"></Dropdown.Divider>);
  //     items.push(
  //       ...profiles.map((v) => (
  //         <Dropdown.Item key={v.profileId} eventKey={v.profileId.toString()}>
  //           {v.name}
  //         </Dropdown.Item>
  //       ))
  //     );
  //   }

  //   return items;
  // }, [profiles]);

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
    (key: Nullable<string>) => {
      const id = key ? parseInt(key) : null;

      const newItems = selections.map((v) => ({ ...v, profileId: id }));

      setDirties((dirty) => {
        return uniqBy([...newItems, ...dirty], GetItemId);
      });
    },
    [selections]
  );
  return (
    <Container fluid px={0}>
      <ContentHeader>
        <div>
          <Select
            placeholder="Change Profile"
            disabled={selections.length === 0}
            data={[]}
          ></Select>
          {/* <Dropdown onSelect={setProfiles}>
            <Dropdown.Toggle disabled={selections.length === 0} color="light">
              Change Profile
            </Dropdown.Toggle>
            <Dropdown.Menu>{profileOptions}</Dropdown.Menu>
          </Dropdown> */}
        </div>
        <div>
          <ContentHeader.Button icon={faUndo} onClick={onEnded}>
            Cancel
          </ContentHeader.Button>
          <ContentHeader.AsyncButton
            icon={faCheck}
            disabled={dirties.length === 0 || hasTask}
            promise={save}
            onSuccess={onEnded}
          >
            Save
          </ContentHeader.AsyncButton>
        </div>
      </ContentHeader>
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
