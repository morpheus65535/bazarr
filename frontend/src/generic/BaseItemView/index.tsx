import { faCheck, faList, faUndo } from "@fortawesome/free-solid-svg-icons";
import { AsyncThunk } from "@reduxjs/toolkit";
import { uniqBy } from "lodash";
import React, { useCallback, useMemo, useState } from "react";
import { Container, Dropdown, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { useLanguageProfiles } from "../../@redux/hooks";
import { useReduxAction } from "../../@redux/hooks/base";
import { ContentHeader } from "../../components";
import { GetItemId, isNonNullable } from "../../utilites";
import Table from "./table";

export interface SharedProps<T extends Item.Base> {
  name: string;
  loader: (params: Parameter.Range) => void;
  columns: Column<T>[];
  modify: (form: FormType.ModifyItem) => Promise<void>;
  state: AsyncOrderState<T>;
}

interface Props<T extends Item.Base = Item.Base> extends SharedProps<T> {
  updateAction: AsyncThunk<AsyncDataWrapper<T>, number[] | undefined, any>;
}

function BaseItemView<T extends Item.Base>({
  updateAction,
  ...shared
}: Props<T>) {
  const state = shared.state;

  const [pendingEditMode, setPendingEdit] = useState(false);
  const [editMode, setEdit] = useState(false);

  const onUpdated = useCallback(() => {
    setPendingEdit((edit) => {
      // Hack to remove all dependencies
      setEdit(edit);
      return edit;
    });
    setDirty([]);
  }, []);

  // const update = useReduxActionWith(updateAction, onUpdated);
  const update = useReduxAction(updateAction);

  const [selections, setSelections] = useState<T[]>([]);
  const [dirtyItems, setDirty] = useState<T[]>([]);

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
      const newDirty = uniqBy([...newItems, ...dirtyItems], GetItemId);
      setDirty(newDirty);
    },
    [selections, dirtyItems]
  );

  const startEdit = useCallback(() => {
    if (shared.state.data.order.every(isNonNullable)) {
      setEdit(true);
    } else {
      update();
    }
    setPendingEdit(true);
  }, [shared.state.data.order, update]);

  const endEdit = useCallback(() => {
    setEdit(false);
    setDirty([]);
    setPendingEdit(false);
    setSelections([]);
  }, []);

  const saveItems = useCallback(() => {
    const form: FormType.ModifyItem = {
      id: [],
      profileid: [],
    };
    dirtyItems.forEach((v) => {
      const id = GetItemId(v);
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
              <ContentHeader.Button icon={faUndo} onClick={endEdit}>
                Cancel
              </ContentHeader.Button>
              <ContentHeader.AsyncButton
                icon={faCheck}
                disabled={dirtyItems.length === 0}
                promise={saveItems}
                onSuccess={endEdit}
              >
                Save
              </ContentHeader.AsyncButton>
            </ContentHeader.Group>
          </React.Fragment>
        ) : (
          <ContentHeader.Button
            updating={pendingEditMode !== editMode}
            disabled={
              state.data.order.length === 0 && state.state === "loading"
            }
            icon={faList}
            onClick={startEdit}
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
}

export default BaseItemView;
