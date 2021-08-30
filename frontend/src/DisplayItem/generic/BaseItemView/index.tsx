import { faCheck, faList, faUndo } from "@fortawesome/free-solid-svg-icons";
import { AsyncThunk } from "@reduxjs/toolkit";
import { uniqBy } from "lodash";
import React, { useCallback, useMemo, useState } from "react";
import { Container, Dropdown, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { useIsAnyTaskRunning } from "../../../@modules/task/hooks";
import { useLanguageProfiles } from "../../../@redux/hooks";
import { useAppDispatch } from "../../../@redux/hooks/base";
import { ContentHeader } from "../../../components";
import { GetItemId, isNonNullable } from "../../../utilities";
import Table from "./table";

export interface SharedProps<T extends Item.Base> {
  name: string;
  loader: (params: Parameter.Range) => void;
  columns: Column<T>[];
  modify: (form: FormType.ModifyItem) => Promise<void>;
  state: Async.Entity<T>;
}

interface Props<T extends Item.Base = Item.Base> extends SharedProps<T> {
  updateAction: AsyncThunk<AsyncDataWrapper<T>, void, {}>;
}

function BaseItemView<T extends Item.Base>({
  updateAction,
  ...shared
}: Props<T>) {
  const state = shared.state;

  const [pendingEditMode, setPendingEdit] = useState(false);
  const [editMode, setEdit] = useState(false);

  const dispatch = useAppDispatch();
  const update = useCallback(() => {
    dispatch(updateAction()).then(() => {
      setPendingEdit((edit) => {
        // Hack to remove all dependencies
        setEdit(edit);
        return edit;
      });
      setDirty([]);
    });
  }, [dispatch, updateAction]);

  const [selections, setSelections] = useState<T[]>([]);
  const [dirtyItems, setDirty] = useState<T[]>([]);

  const profiles = useLanguageProfiles();

  const profileOptions = useMemo<JSX.Element[]>(() => {
    const items: JSX.Element[] = [];
    if (profiles) {
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
    }

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
      setDirty((dirty) => {
        return uniqBy([...newItems, ...dirty], GetItemId);
      });
    },
    [selections]
  );

  const startEdit = useCallback(() => {
    if (shared.state.content.ids.every(isNonNullable)) {
      setEdit(true);
    } else {
      update();
    }
    setPendingEdit(true);
  }, [shared.state.content.ids, update]);

  const endEdit = useCallback(() => {
    setEdit(false);
    setDirty([]);
    setPendingEdit(false);
    setSelections([]);
  }, []);

  const save = useCallback(() => {
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

  const hasTask = useIsAnyTaskRunning();

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
                disabled={dirtyItems.length === 0 || hasTask}
                promise={save}
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
              (state.content.ids.length === 0 && state.state === "loading") ||
              hasTask
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
