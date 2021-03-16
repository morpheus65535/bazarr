import { faCheck, faList, faUndo } from "@fortawesome/free-solid-svg-icons";
import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Container, Dropdown, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { useLanguageProfiles } from "../../@redux/hooks";
import { ContentHeader } from "../../components";
import { getExtendItemId, mergeArray } from "../../utilites";
import Table from "./table";

export interface SharedProps {
  name: string;
  update: (id?: number[]) => void;
  loader: (start: number, length: number) => void;
  columns: Column<Item.Base>[];
  modify: (form: FormType.ModifyItem) => Promise<void>;
  state: AsyncState<OrderIdState<Item.Base>>;
}

export function ExtendItemComparer(lhs: Item.Base, rhs: Item.Base): boolean {
  return getExtendItemId(lhs) === getExtendItemId(rhs);
}

interface Props extends SharedProps {}

const BaseItemView: FunctionComponent<Props> = (shared) => {
  const state = shared.state;
  const [editMode, setEdit] = useState(false);

  const [selections, setSelections] = useState<Item.Base[]>([]);
  const [dirtyItems, setDirty] = useState<Item.Base[]>([]);

  const [profiles] = useLanguageProfiles();

  const profileOptions = useMemo<JSX.Element[]>(() => {
    const items: JSX.Element[] = [];
    items.push(
      <Dropdown.Item key="clear-profile">Clear Profile</Dropdown.Item>
    );
    items.push(<Dropdown.Divider key="dropdown-divider"></Dropdown.Divider>);
    items.push(
      ...profiles.map((v) => (
        <Dropdown.Item key={v.profileId} eventKey={v.profileId.toString()}>
          {v.name}
        </Dropdown.Item>
      ))
    );
    return items;
  }, [profiles]);

  const changeProfiles = useCallback(
    (key: Nullable<string>) => {
      const id = key ? parseInt(key) : null;
      const newItems = selections.map((v) => {
        const item = { ...v };
        item.profileId = id;
        return item;
      });
      const newDirty = mergeArray(dirtyItems, newItems, ExtendItemComparer);
      setDirty(newDirty);
    },
    [selections, dirtyItems]
  );

  const toggleMode = useCallback(() => {
    if (dirtyItems.length > 0) {
      const ids = dirtyItems.map(getExtendItemId);
      shared.update(ids);
    }
    setEdit((edit) => !edit);
    setDirty([]);
    setSelections([]);
  }, [dirtyItems, shared]);

  const saveItems = useCallback(() => {
    const form: FormType.ModifyItem = {
      id: [],
      profileid: [],
    };
    dirtyItems.forEach((v) => {
      const id = getExtendItemId(v);
      form.id.push(id);
      form.profileid.push(v.profileId);
    });
    return shared.modify(form);
  }, [dirtyItems, shared]);

  return (
    <Container fluid>
      <Helmet>
        <title>{shared.name} - Bazarr</title>
      </Helmet>
      <ContentHeader scroll={false}>
        {editMode ? (
          <React.Fragment>
            <ContentHeader.Group pos="start">
              <Dropdown onSelect={changeProfiles}>
                <Dropdown.Toggle
                  disabled={selections.length === 0}
                  variant="light"
                >
                  Change Profile
                </Dropdown.Toggle>
                <Dropdown.Menu>{profileOptions}</Dropdown.Menu>
              </Dropdown>
            </ContentHeader.Group>
            <ContentHeader.Group pos="end">
              <ContentHeader.Button icon={faUndo} onClick={toggleMode}>
                Cancel
              </ContentHeader.Button>
              <ContentHeader.AsyncButton
                icon={faCheck}
                disabled={dirtyItems.length === 0}
                promise={saveItems}
                onSuccess={toggleMode}
              >
                Save
              </ContentHeader.AsyncButton>
            </ContentHeader.Group>
          </React.Fragment>
        ) : (
          <ContentHeader.Button
            disabled={state.data.order.length === 0 && state.updating}
            icon={faList}
            onClick={toggleMode}
          >
            Mass Edit
          </ContentHeader.Button>
        )}
      </ContentHeader>
      <Row>
        <Table
          {...shared}
          dirtyItems={dirtyItems}
          editMode={editMode}
          select={setSelections}
        ></Table>
      </Row>
    </Container>
  );
};

export default BaseItemView;
