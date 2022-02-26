import { faCheck, faList, faUndo } from "@fortawesome/free-solid-svg-icons";
import { useIsAnyMutationRunning, useLanguageProfiles } from "apis/hooks";
import { UsePaginationQueryResult } from "apis/queries/hooks";
import { TableStyleProps } from "components/tables/BaseTable";
import { useCustomSelection } from "components/tables/plugins";
import { uniqBy } from "lodash";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Container, Dropdown, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { UseMutationResult, UseQueryResult } from "react-query";
import { Column, TableOptions, TableUpdater, useRowSelect } from "react-table";
import { GetItemId } from "utilities";
import {
  ContentHeader,
  ItemEditorModal,
  LoadingIndicator,
  QueryPageTable,
  SimpleTable,
  useShowModal,
} from "..";

interface Props<T extends Item.Base = Item.Base> {
  name: string;
  fullQuery: UseQueryResult<T[]>;
  query: UsePaginationQueryResult<T>;
  columns: Column<T>[];
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem>;
}

function ItemView<T extends Item.Base>({
  name,
  fullQuery,
  query,
  columns,
  mutation,
}: Props<T>) {
  const [editMode, setEditMode] = useState(false);

  const showModal = useShowModal();

  const updateRow = useCallback<TableUpdater<T>>(
    ({ original }, modalKey: string) => {
      showModal(modalKey, original);
    },
    [showModal]
  );

  const options: Partial<TableOptions<T> & TableStyleProps<T>> = {
    emptyText: `No ${name} Found`,
    update: updateRow,
  };

  const content = editMode ? (
    <ItemMassEditor
      query={fullQuery}
      columns={columns}
      mutation={mutation}
      onEnded={() => setEditMode(false)}
    ></ItemMassEditor>
  ) : (
    <>
      <ContentHeader scroll={false}>
        <ContentHeader.Button
          disabled={query.paginationStatus.totalCount === 0}
          icon={faList}
          onClick={() => setEditMode(true)}
        >
          Mass Edit
        </ContentHeader.Button>
      </ContentHeader>
      <Row>
        <QueryPageTable
          {...options}
          columns={columns}
          query={query}
          data={[]}
        ></QueryPageTable>
        <ItemEditorModal modalKey="edit" mutation={mutation}></ItemEditorModal>
      </Row>
    </>
  );

  return (
    <Container fluid>
      <Helmet>
        <title>{name} - Bazarr</title>
      </Helmet>
      {content}
    </Container>
  );
}

interface ItemMassEditorProps<T extends Item.Base> {
  columns: Column<T>[];
  query: UseQueryResult<T[]>;
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem>;
  onEnded: () => void;
}

function ItemMassEditor<T extends Item.Base = Item.Base>(
  props: ItemMassEditorProps<T>
) {
  const { columns, mutation, query, onEnded } = props;
  const [selections, setSelections] = useState<T[]>([]);
  const [dirties, setDirties] = useState<T[]>([]);
  const hasTask = useIsAnyMutationRunning();
  const { data: profiles } = useLanguageProfiles();

  const { refetch } = query;

  useEffect(() => {
    refetch();
  }, [refetch]);

  const data = useMemo(
    () => uniqBy([...dirties, ...(query?.data ?? [])], GetItemId),
    [dirties, query?.data]
  );

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
    <>
      <ContentHeader scroll={false}>
        <ContentHeader.Group pos="start">
          <Dropdown onSelect={setProfiles}>
            <Dropdown.Toggle disabled={selections.length === 0} variant="light">
              Change Profile
            </Dropdown.Toggle>
            <Dropdown.Menu>{profileOptions}</Dropdown.Menu>
          </Dropdown>
        </ContentHeader.Group>
        <ContentHeader.Group pos="end">
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
        </ContentHeader.Group>
      </ContentHeader>
      <Row>
        {query.data === undefined ? (
          <LoadingIndicator></LoadingIndicator>
        ) : (
          <SimpleTable
            columns={columns}
            data={data}
            onSelect={setSelections}
            isSelecting
            plugins={[useRowSelect, useCustomSelection]}
          ></SimpleTable>
        )}
      </Row>
    </>
  );
}

export default ItemView;
