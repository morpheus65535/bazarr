import React, { FunctionComponent, useMemo } from "react";
import { Col, Container, Pagination, Row } from "react-bootstrap";

interface Props {
  count: number;
  index: number;
  size: number;
  total: number;
  canPrevious: boolean;
  previous: () => void;
  canNext: boolean;
  next: () => void;
  goto: (idx: number) => void;
}

const PageControl: FunctionComponent<Props> = ({
  count,
  index,
  size,
  total,
  canPrevious,
  previous,
  canNext,
  next,
  goto,
}) => {
  const empty = total === 0;
  const start = empty ? 0 : size * index + 1;
  const end = Math.min(size * (index + 1), total);

  const pageButtons = useMemo(
    () =>
      [...Array(count).keys()]
        .map((idx) => {
          if (Math.abs(idx - index) >= 4 && idx !== 0 && idx !== count - 1) {
            return null;
          } else {
            return (
              <Pagination.Item
                key={idx}
                active={index === idx}
                onClick={() => goto(idx)}
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
    [count, index, goto]
  );

  return (
    <Container fluid className="mb-3">
      <Row>
        <Col className="d-flex align-items-center justify-content-start">
          <span>
            Show {start} to {end} of {total} entries
          </span>
        </Col>
        <Col className="d-flex justify-content-end">
          <Pagination className="m-0" hidden={count <= 1}>
            <Pagination.Prev
              onClick={previous}
              disabled={!canPrevious}
            ></Pagination.Prev>
            {pageButtons}
            <Pagination.Next
              onClick={next}
              disabled={!canNext}
            ></Pagination.Next>
          </Pagination>
        </Col>
      </Row>
    </Container>
  );
};

export default PageControl;
