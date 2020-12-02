import React from "react";
import {
  Pagination,
  Row,
  Col,
  Table,
} from "react-bootstrap";
import { TableOptions, usePagination, useTable } from "react-table";

interface Props<T extends object = {}> {
  options: TableOptions<T>;
}

export default function BasicTable<T extends object = {}>(props: Props<T>) {
  const instance = useTable(props.options, usePagination);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,

    // page
    page,
    canNextPage,
    canPreviousPage,
    pageCount,
    gotoPage,
    nextPage,
    previousPage,
    state: { pageIndex, pageSize },
  } = instance;

  const header = (
    <thead>
      {headerGroups.map((headerGroup) => (
        <tr {...headerGroup.getHeaderGroupProps()}>
          {headerGroup.headers.map((col) => (
            <th {...col.getHeaderProps()}>{col.render("Header")}</th>
          ))}
        </tr>
      ))}
    </thead>
  );

  const body = (
    <tbody {...getTableBodyProps()}>
      {page.map(
        (row): JSX.Element => {
          prepareRow(row);
          return (
            <tr {...row.getRowProps()}>
              {row.cells.map((cell) => (
                <td {...cell.getCellProps()}>{cell.render("Cell")}</td>
              ))}
            </tr>
          );
        }
      )}
    </tbody>
  );

  const start = pageSize * pageIndex + 1;
  const end = Math.min(pageSize * (pageIndex + 1), rows.length);

  const buttonClass = "";
  const pageButtons = React.useMemo(() => {
    return [...Array(pageCount).keys()].map((idx) => (
      <Pagination.Item
        key={idx}
        className={buttonClass}
        active={pageIndex === idx}
        onClick={() => gotoPage(idx)}
      >
        {idx + 1}
      </Pagination.Item>
    ));
  }, [pageCount, pageIndex, gotoPage]);

  const pageControl = (
    <div>
      <Row>
        <Col className="d-flex align-items-center justify-content-start">
          <span>
            Show {start} to {end} of {rows.length} entries
          </span>
        </Col>
        <Col className="d-flex justify-content-end">
          <Pagination>
            <Pagination.Prev
              className={buttonClass}
              onClick={previousPage}
              disabled={!canPreviousPage}
            >
            </Pagination.Prev>
            {pageButtons}
            <Pagination.Next
              className={buttonClass}
              onClick={nextPage}
              disabled={!canNextPage}
            >
            </Pagination.Next>
          </Pagination>
        </Col>
      </Row>
    </div>
  );

  return (
    <React.Fragment>
      <Table striped borderless {...getTableProps()}>
        {header}
        {body}
      </Table>
      {pageControl}
    </React.Fragment>
  );
}
