import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { TableStyleProps } from "@/components/tables/BaseTable";
import { faList } from "@fortawesome/free-solid-svg-icons";
import React, { useCallback } from "react";
import { Row } from "react-bootstrap";
import { UseMutationResult } from "react-query";
import { useNavigate } from "react-router-dom";
import { Column, TableOptions, TableUpdater } from "react-table";
import {
  ContentHeader,
  ItemEditorModal,
  QueryPageTable,
  useShowModal,
} from "..";

interface Props<T extends Item.Base = Item.Base> {
  query: UsePaginationQueryResult<T>;
  columns: Column<T>[];
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem>;
}

function ItemView<T extends Item.Base>({ query, columns, mutation }: Props<T>) {
  const { mutateAsync } = mutation;

  const navigate = useNavigate();

  const showModal = useShowModal();

  const updateRow = useCallback<TableUpdater<T>>(
    ({ original }, modalKey: string) => {
      showModal(modalKey, original);
    },
    [showModal]
  );

  const options: Partial<TableOptions<T> & TableStyleProps<T>> = {
    emptyText: `No Items Found`,
    update: updateRow,
  };

  return (
    <>
      <ContentHeader scroll={false}>
        <ContentHeader.Button
          disabled={query.paginationStatus.totalCount === 0}
          icon={faList}
          onClick={() => navigate("edit")}
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
        <ItemEditorModal modalKey="edit" submit={mutateAsync}></ItemEditorModal>
      </Row>
    </>
  );
}

export default ItemView;
