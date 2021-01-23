import React from "react";
import { Pagination, Row, Col, Container, Table } from "react-bootstrap";
import { TableOptions, usePagination, useTable } from "react-table";

interface Props<T extends object = {}> {
  options: TableOptions<T>;
  emptyText?: string;
  pageControl?: boolean;
  responsive?: boolean;
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

  const colCount = React.useMemo<number>(() => {
    return headerGroups.reduce(
      (prev, curr) => (curr.headers.length > prev ? curr.headers.length : prev),
      0
    );
  }, [headerGroups]);

  const empty = rows.length === 0;

  const body = (
    <tbody {...getTableBodyProps()}>
      {props.emptyText && empty ? (
        <tr>
          <td colSpan={colCount} className="text-center">
            {props.emptyText}
          </td>
        </tr>
      ) : (
        page.map(
          (row): JSX.Element => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()}>
                {row.cells.map((cell) => (
                  <td
                    className={cell.column.className}
                    {...cell.getCellProps()}
                  >
                    {cell.render("Cell")}
                  </td>
                ))}
              </tr>
            );
          }
        )
      )}
    </tbody>
  );

  const start = empty ? 0 : pageSize * pageIndex + 1;
  const end = Math.min(pageSize * (pageIndex + 1), rows.length);

  const buttonClass = "";

  const pageButtons = React.useMemo(() => {
    return [...Array(pageCount).keys()]
      .map((idx) => {
        if (
          Math.abs(idx - pageIndex) >= 4 &&
          idx !== 0 &&
          idx !== pageCount - 1
        ) {
          return null;
        } else {
          return (
            <Pagination.Item
              key={idx}
              className={buttonClass}
              active={pageIndex === idx}
              onClick={() => gotoPage(idx)}
            >
              {idx + 1}
            </Pagination.Item>
          );
        }
      })
      .flatMap((item, idx, arr) => {
        if (item === null) {
          if (arr[idx + 1] === null) {
            return [];
          } else {
            return (
              <Pagination.Ellipsis
                key={idx}
                className={buttonClass}
                disabled
              ></Pagination.Ellipsis>
            );
          }
        } else {
          return [item];
        }
      });
  }, [pageCount, pageIndex, gotoPage]);

  const pageControlEnabled = props.pageControl ?? true;

  const pageControl = (
    <Container fluid hidden={!pageControlEnabled}>
      <Row>
        <Col className="d-flex align-items-center justify-content-start">
          <span>
            Show {start} to {end} of {rows.length} entries
          </span>
        </Col>
        <Col className="d-flex justify-content-end">
          <Pagination className="m-0" hidden={pageCount <= 1}>
            <Pagination.Prev
              className={buttonClass}
              onClick={previousPage}
              disabled={!canPreviousPage}
            ></Pagination.Prev>
            {pageButtons}
            <Pagination.Next
              className={buttonClass}
              onClick={nextPage}
              disabled={!canNextPage}
            ></Pagination.Next>
          </Pagination>
        </Col>
      </Row>
    </Container>
  );

  return (
    <React.Fragment>
      <Table
        striped
        borderless
        responsive={props.responsive ?? true}
        {...getTableProps()}
      >
        {header}
        {body}
      </Table>
      {pageControl}
    </React.Fragment>
  );
}
