import React, { FunctionComponent, useMemo } from "react";
import { connect } from "react-redux";
import { Column } from "react-table";

import { BasicTable } from "../../components";

interface Props {
  providers: SystemProvider[];
}

function mapStateToProps({ system }: StoreState) {
  const { providers } = system;
  return {
    providers: providers.items,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const columns: Column<SystemProvider>[] = useMemo<Column<SystemProvider>[]>(
    () => [
      {
        Header: "Name",
        accessor: "name",
      },
      {
        Header: "Status",
        accessor: "status",
      },
      {
        Header: "Next Retry",
        accessor: "retry",
      },
    ],
    []
  );

  return <BasicTable columns={columns} data={props.providers}></BasicTable>;
};

export default connect(mapStateToProps)(Table);
