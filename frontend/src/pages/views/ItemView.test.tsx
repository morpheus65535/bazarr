import { ColumnDef } from "@tanstack/react-table";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vitest } from "vitest";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { customRender, screen } from "@/tests";
import ItemView from "./ItemView";

const item = { title: "My Show", sonarrSeriesId: 1 } as Item.Series;

const columns: ColumnDef<Item.Series>[] = [
  { header: "Name", accessorKey: "title" },
];

function buildQuery(): UsePaginationQueryResult<Item.Series> {
  return {
    data: { data: [item], total: 1 },
    paginationStatus: {
      isPageLoading: false,
      totalCount: 1,
      pageSize: 50,
      pageCount: 1,
      page: 0,
    },
    controls: { gotoPage: vitest.fn() },
  } as unknown as UsePaginationQueryResult<Item.Series>;
}

function renderPoster(item: Item.Series) {
  return <div data-testid="poster-card">{item.title}</div>;
}

describe("ItemView", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders the table view by default", () => {
    customRender(
      <ItemView
        query={buildQuery()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
      ></ItemView>,
    );

    expect(
      screen.getByRole("columnheader", { name: "Name" }),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("poster-card")).not.toBeInTheDocument();
  });

  it("switches to the poster view and persists the selection", async () => {
    customRender(
      <ItemView
        query={buildQuery()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
      ></ItemView>,
    );

    await userEvent.click(screen.getByText("Poster view"));

    expect(screen.getByTestId("poster-card")).toBeInTheDocument();
    expect(screen.queryByRole("columnheader")).not.toBeInTheDocument();
    expect(window.localStorage.getItem("test-view-mode")).toBe(
      JSON.stringify("poster"),
    );
  });

  it("restores the persisted poster view on mount", () => {
    window.localStorage.setItem("test-view-mode", JSON.stringify("poster"));

    customRender(
      <ItemView
        query={buildQuery()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
      ></ItemView>,
    );

    expect(screen.getByTestId("poster-card")).toBeInTheDocument();
  });

  it("switches back to the table view", async () => {
    window.localStorage.setItem("test-view-mode", JSON.stringify("poster"));

    customRender(
      <ItemView
        query={buildQuery()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
      ></ItemView>,
    );

    await userEvent.click(screen.getByText("Table view"));

    expect(
      screen.getByRole("columnheader", { name: "Name" }),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("poster-card")).not.toBeInTheDocument();
  });

  it("does not show the toggle without poster support", () => {
    customRender(<ItemView query={buildQuery()} columns={columns}></ItemView>);

    expect(screen.queryByText("Poster view")).not.toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: "Name" }),
    ).toBeInTheDocument();
  });
});
