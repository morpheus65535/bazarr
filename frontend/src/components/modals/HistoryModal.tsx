import React, { FunctionComponent, useMemo } from "react";
import BasicModal, { ModalProps } from "./BasicModal";
import { Column } from "react-table";
import { BasicTable, HistoryIcon, AsyncStateOverlay } from "..";

interface MovieHistoryProps {
  history: AsyncState<MovieHistory[]>;
}

export const MovieHistoryModal: FunctionComponent<
  ModalProps & MovieHistoryProps
> = (props) => {
  const { history } = props;

  const columns = useMemo<Column<MovieHistory>[]>(
    () => [
      {
        accessor: "action",
        Cell: (row) => {
          return <HistoryIcon action={row.value}></HistoryIcon>;
        },
      },
      {
        Header: "Language",
        accessor: (d) => d.language.name,
      },
      {
        Header: "Provider",
        accessor: "provider",
      },
      {
        Header: "Score",
        accessor: "score",
      },
      {
        Header: "Date",
        accessor: "timestamp",
      },
      {
        // Actions
        accessor: "radarrId",
        Cell: (row) => {
          return null;
        },
      },
    ],
    []
  );

  return (
    <BasicModal {...props}>
      <AsyncStateOverlay state={history}>
        <BasicTable
          emptyText="No History Found"
          options={{ columns, data: history.items }}
        ></BasicTable>
      </AsyncStateOverlay>
    </BasicModal>
  );
};

interface EpisodeHistoryProps {
  history: AsyncState<EpisodeHistory[]>;
}

export const EpisodeHistoryModal: FunctionComponent<
  ModalProps & EpisodeHistoryProps
> = (props) => {
  const { history } = props;

  const columns = useMemo<Column<EpisodeHistory>[]>(
    () => [
      {
        accessor: "action",
        Cell: (row) => {
          return <HistoryIcon action={row.value}></HistoryIcon>;
        },
      },
      {
        Header: "Language",
        accessor: (d) => d.language.name,
      },
      {
        Header: "Provider",
        accessor: "provider",
      },
      {
        Header: "Score",
        accessor: "score",
      },
      {
        Header: "Date",
        accessor: "timestamp",
      },
      {
        // Actions
        accessor: "sonarrEpisodeId",
        Cell: (row) => {
          return null;
        },
      },
    ],
    []
  );

  return (
    <BasicModal {...props}>
      <AsyncStateOverlay state={history}>
        <BasicTable options={{ columns, data: history.items }}></BasicTable>
      </AsyncStateOverlay>
    </BasicModal>
  );
};
