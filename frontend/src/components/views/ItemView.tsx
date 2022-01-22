import { faCheck, faList, faUndo } from "@fortawesome/free-solid-svg-icons";
import { uniqBy } from "lodash";
import React, { useCallback, useMemo, useState } from "react";
import { Container, Dropdown, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column, TableOptions, TableUpdater } from "react-table";
import { PaginationQuery } from "src/apis/queries/hooks";
import { TableStyleProps } from "src/components/tables/BaseTable";
import {
  ContentHeader,
  ItemEditorModal,
  QueryPageTable,
  useShowModal,
} from "..";
import {
  useIsAnyMutationRunning,
  useLanguageProfiles,
} from "../../apis/queries/client";
import { GetItemId } from "../../utilities";

interface Props<T extends Item.Base = Item.Base> {
  name: string;
  query: PaginationQuery<T>;
  columns: Column<T>[];
  modify: (form: FormType.ModifyItem) => Promise<void>;
}

function ItemView<T extends Item.Base>({
  name,
  query,
  columns,
  modify,
}: Props<T>) {
  const [pendingEditMode, setPendingEdit] = useState(false);
  const [editMode, setEdit] = useState(false);

  const update = useCallback(() => {
    // dispatch(updateAction()).then(() => {
    //   setPendingEdit((edit) => {
    //     // Hack to remove all dependencies
    //     setEdit(edit);
    //     return edit;
    //   });
    //   setDirty([]);
    // });
  }, []);

  const [selections, setSelections] = useState<T[]>([]);
  const [dirtyItems, setDirty] = useState<T[]>([]);

  const { data: profiles } = useLanguageProfiles();

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
    if (query.paginationStatus.totalCount > 0) {
      setEdit(true);
    } else {
      update();
    }
    setPendingEdit(true);
  }, [query.paginationStatus.totalCount, update]);

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
      if (id) {
        form.id.push(id);
        form.profileid.push(v.profileId);
      }
    });
    return modify(form);
  }, [dirtyItems, modify]);

  const hasTask = useIsAnyMutationRunning();

  const showModal = useShowModal();

  const updateRow = useCallback<TableUpdater<T>>(
    (row, modalKey: string) => {
      showModal(modalKey, row.original);
    },
    [showModal]
  );

  const options: Partial<TableOptions<T> & TableStyleProps<T>> = {
    emptyText: `No ${name} Found`,
    update: updateRow,
  };

  return (
    <Container fluid>
      <Helmet>
        <title>{name} - Bazarr</title>
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
              // (state.content.ids.length === 0 && state.state === "loading") ||
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
        <QueryPageTable
          {...options}
          columns={columns}
          query={query}
          data={[]}
        ></QueryPageTable>
        <ItemEditorModal modalKey="edit" submit={modify}></ItemEditorModal>
      </Row>
    </Container>
  );
}

export default ItemView;
