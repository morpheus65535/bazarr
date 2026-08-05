import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { customRender, screen } from "@/tests";
import QueryPageTable from "./QueryPageTable";

interface Row {
  id: number;
  name: string;
}

type QueryShape = {
  data: { data: Row[]; total: number };
  paginationStatus: {
    page: number;
    pageCount: number;
    totalCount: number;
    pageSize: number;
    isPageLoading: boolean;
  };
  controls: { gotoPage: (page: number) => void };
};

const createQuery = (overrides?: Partial<QueryShape>) => {
  const gotoPage = vitest.fn();

  const baseQuery: QueryShape = {
    data: { data: [{ id: 1, name: "A" }], total: 1 },
    paginationStatus: {
      page: 0,
      pageCount: 2,
      totalCount: 2,
      pageSize: 1,
      isPageLoading: false,
    },
    controls: { gotoPage },
  };

  return {
    query: {
      ...baseQuery,
      ...overrides,
    } as unknown as UsePaginationQueryResult<Row>,
    gotoPage,
  };
};

const columns = [{ header: "Name", accessorKey: "name" }];

describe("QueryPageTable", () => {
  it("renders the data and pagination controls", () => {
    const { query } = createQuery();

    customRender(<QueryPageTable query={query} columns={columns} />);

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("Show 1 to 1 of 2 entries")).toBeInTheDocument();
  });

  it("navigates to the next page", async () => {
    const { query, gotoPage } = createQuery();

    customRender(<QueryPageTable query={query} columns={columns} />);

    await userEvent.click(screen.getByText("2"));

    expect(gotoPage).toHaveBeenCalledWith(1);
  });

  it("hides pagination when only one page is available", () => {
    const { query } = createQuery({
      paginationStatus: {
        page: 0,
        pageCount: 1,
        totalCount: 1,
        pageSize: 1,
        isPageLoading: false,
      },
    });

    customRender(<QueryPageTable query={query} columns={columns} />);

    expect(
      screen.queryByRole("button", { name: "Next page" }),
    ).not.toBeInTheDocument();
  });
});
