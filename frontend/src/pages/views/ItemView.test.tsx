import { ColumnDef } from "@tanstack/react-table";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import ItemView from "./ItemView";

const item = { title: "My Show", sonarrSeriesId: 1 } as Item.Series;

const columns: ColumnDef<Item.Series>[] = [
  { header: "Name", accessorKey: "title" },
];

const queryKey = ["test-item-view"];

const buildQueryFn = (total = 1): RangeQuery<Item.Series> => {
  return vitest.fn(() => Promise.resolve({ data: [item], total }));
};

const renderPoster = (item: Item.Series) => {
  return <div data-testid="poster-card">{item.title}</div>;
};

describe("ItemView", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders the table view by default", async () => {
    customRender(
      <ItemView
        queryKey={queryKey}
        queryFn={buildQueryFn()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
      ></ItemView>,
    );

    expect(
      await screen.findByRole("columnheader", { name: "Name" }),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("poster-card")).not.toBeInTheDocument();
  });

  it("switches to the poster view and persists the selection", async () => {
    customRender(
      <ItemView
        queryKey={queryKey}
        queryFn={buildQueryFn()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
      ></ItemView>,
    );

    await userEvent.click(await screen.findByText("Poster view"));

    expect(await screen.findByTestId("poster-card")).toBeInTheDocument();
    expect(screen.queryByRole("columnheader")).not.toBeInTheDocument();
    expect(window.localStorage.getItem("test-view-mode")).toBe(
      JSON.stringify("poster"),
    );
  });

  it("restores the persisted poster view on mount", async () => {
    window.localStorage.setItem("test-view-mode", JSON.stringify("poster"));

    customRender(
      <ItemView
        queryKey={queryKey}
        queryFn={buildQueryFn()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
      ></ItemView>,
    );

    expect(await screen.findByTestId("poster-card")).toBeInTheDocument();
  });

  it("switches back to the table view", async () => {
    window.localStorage.setItem("test-view-mode", JSON.stringify("poster"));

    customRender(
      <ItemView
        queryKey={queryKey}
        queryFn={buildQueryFn()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
      ></ItemView>,
    );

    await userEvent.click(await screen.findByText("Table view"));

    expect(
      await screen.findByRole("columnheader", { name: "Name" }),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("poster-card")).not.toBeInTheDocument();
  });

  it("does not show the toggle without poster support", async () => {
    customRender(
      <ItemView
        queryKey={queryKey}
        queryFn={buildQueryFn()}
        columns={columns}
      ></ItemView>,
    );

    expect(screen.queryByText("Poster view")).not.toBeInTheDocument();
    expect(
      await screen.findByRole("columnheader", { name: "Name" }),
    ).toBeInTheDocument();
  });
});
