import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi, vitest } from "vitest";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import { customRender, screen } from "@/tests";
import ItemView from "./ItemView";

vi.mock("@/apis/hooks", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/apis/hooks")>()),
  useLanguageProfiles: () => ({ data: [] }),
  useLanguages: () => ({ data: [] }),
}));

const item = {
  title: "My Show",
  sonarrSeriesId: 1,
  tags: [],
} as unknown as Item.Series;

const columns: ColumnDef<Item.Series>[] = [
  { header: "Name", accessorKey: "title" },
];

const filterConfig = {
  sortFields: [{ value: "title", label: "Name" }],
  filters: {
    monitored: true,
    missing: true,
    profile: true,
    tags: true,
  },
};

const queryKey = ["test-item-view"];

const buildQueryFn = (total = 1): RangeQuery<Item.Series> => {
  return vitest.fn(() => Promise.resolve({ data: [item], total }));
};

const renderPoster = (item: Item.Series) => {
  return (
    <div key={item.sonarrSeriesId} data-testid="poster-card">
      {item.title}
    </div>
  );
};

describe("ItemView", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.history.pushState({}, "", "/");
  });

  it("renders the table view by default", async () => {
    customRender(
      <ItemView
        queryKey={queryKey}
        queryFn={buildQueryFn()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
        filterConfig={filterConfig}
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
        filterConfig={filterConfig}
      ></ItemView>,
    );

    await userEvent.click(
      await screen.findByRole("button", { name: "View: table" }),
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
        filterConfig={filterConfig}
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
        filterConfig={filterConfig}
      ></ItemView>,
    );

    await userEvent.click(
      await screen.findByRole("button", { name: "View: poster" }),
    );
    await userEvent.click(await screen.findByText("Table view"));

    expect(
      await screen.findByRole("columnheader", { name: "Name" }),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("poster-card")).not.toBeInTheDocument();
  });

  it("sorts by clicking the column header", async () => {
    customRender(
      <ItemView
        queryKey={queryKey}
        queryFn={buildQueryFn()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
        filterConfig={filterConfig}
      ></ItemView>,
    );

    const header = await screen.findByRole("columnheader", { name: "Name" });

    await userEvent.click(header);
    expect(window.location.search).toContain("sort_by=title");
    expect(window.location.search).toContain("sort_order=asc");

    await userEvent.click(header);
    expect(window.location.search).toContain("sort_order=desc");
  });

  it("resets the page param when a filter changes", async () => {
    window.history.pushState({}, "", "/?page=2");

    customRender(
      <ItemView
        queryKey={queryKey}
        queryFn={buildQueryFn()}
        columns={columns}
        viewModeKey="test-view-mode"
        renderPoster={renderPoster}
        filterConfig={filterConfig}
      ></ItemView>,
    );

    await screen.findByRole("columnheader", { name: "Name" });
    await userEvent.click(screen.getByText("Monitored"));

    expect(window.location.search).toContain("monitored=true");
    expect(window.location.search).not.toContain("page=");
  });

  it("does not show the toggle without poster support", async () => {
    customRender(
      <ItemView
        queryKey={queryKey}
        queryFn={buildQueryFn()}
        columns={columns}
        filterConfig={filterConfig}
      ></ItemView>,
    );

    expect(screen.queryByText("Poster view")).not.toBeInTheDocument();
    expect(
      await screen.findByRole("columnheader", { name: "Name" }),
    ).toBeInTheDocument();
  });
});
