import React, { useMemo } from "react";
import { Col, Container, Pagination, Row } from "react-bootstrap";
import { useSelector } from "react-redux";
import { TableOptions, usePagination, useTable } from "react-table";
import BaseTable, {
  ExtractStyleAndOptions,
  TableStyleProps,
} from "./BaseTable";

type Props<T extends object> = TableOptions<T> & TableStyleProps & {};

export default function PageTable<T extends object>(props: Props<T>) {
  const { ...remain } = props;
  const { style, options } = ExtractStyleAndOptions(remain);

  // Default Settings
  const site = useSelector<ReduxStore, ReduxStore.Site>((s) => s.site);

  if (options.initialState === undefined) {
    options.initialState = {};
  }

  if (options.autoResetPage === undefined) {
    options.autoResetPage = false;
  }

  if (options.initialState.pageSize === undefined) {
    options.initialState.pageSize = site.pageSize;
  }

  const instance = useTable(options, usePagination);

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

  const empty = rows.length === 0;

  const pageButtons = useMemo(
    () =>
      [...Array(pageCount).keys()]
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
                <Pagination.Ellipsis key={idx} disabled></Pagination.Ellipsis>
              );
            }
          } else {
            return [item];
          }
        }),
    [pageCount, pageIndex, gotoPage]
  );

  const pageControl = useMemo(() => {
    const start = empty ? 0 : pageSize * pageIndex + 1;
    const end = Math.min(pageSize * (pageIndex + 1), rows.length);

    return (
      <Container fluid className="mb-3">
        <Row>
          <Col className="d-flex align-items-center justify-content-start">
            <span>
              Show {start} to {end} of {rows.length} entries
            </span>
          </Col>
          <Col className="d-flex justify-content-end">
            <Pagination className="m-0" hidden={pageCount <= 1}>
              <Pagination.Prev
                onClick={previousPage}
                disabled={!canPreviousPage}
              ></Pagination.Prev>
              {pageButtons}
              <Pagination.Next
                onClick={nextPage}
                disabled={!canNextPage}
              ></Pagination.Next>
            </Pagination>
          </Col>
        </Row>
      </Container>
    );
  }, [
    empty,
    pageIndex,
    pageSize,
    previousPage,
    canPreviousPage,
    canNextPage,
    nextPage,
    pageButtons,
    pageCount,
    rows.length,
  ]);

  return (
    <React.Fragment>
      <BaseTable
        {...style}
        headers={headerGroups}
        rows={page}
        prepareRow={prepareRow}
        tableProps={getTableProps()}
        tableBodyProps={getTableBodyProps()}
      ></BaseTable>
      {pageControl}
    </React.Fragment>
  );
}
