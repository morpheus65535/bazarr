import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import { customRender, screen } from "@/tests";
import SimpleTable from "./SimpleTable";

interface Item {
  name: string;
  value: number;
}

const columns: ColumnDef<Item, unknown>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "value", header: "Value" },
];

describe("SimpleTable", () => {
  it("renders a full server page without slicing it to the default page size", () => {
    const data: Item[] = Array.from({ length: 75 }, (_, i) => ({
      name: `Row ${i + 1}`,
      value: i,
    }));

    customRender(<SimpleTable data={data} columns={columns} />);

    expect(screen.getByText("Row 1")).toBeInTheDocument();
    expect(screen.getByText("Row 75")).toBeInTheDocument();
  });

  it("respects the consumer's initialState", () => {
    const data: Item[] = [
      { name: "Low", value: 1 },
      { name: "High", value: 2 },
    ];

    customRender(
      <SimpleTable
        data={data}
        columns={columns}
        initialState={{ sorting: [{ id: "value", desc: true }] }}
      />,
    );

    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("High");
    expect(rows[2]).toHaveTextContent("Low");
  });

  it("notifies row selection changes", async () => {
    const onRowSelectionChanged = vitest.fn();

    const data: Item[] = [
      { name: "Row 1", value: 1 },
      { name: "Row 2", value: 2 },
    ];

    customRender(
      <SimpleTable
        data={data}
        columns={[
          {
            id: "select",
            cell: ({ row }) => (
              <input
                aria-label="Select row"
                checked={row.getIsSelected()}
                onChange={row.getToggleSelectedHandler()}
                type="checkbox"
              />
            ),
          },
          ...columns,
        ]}
        enableRowSelection
        onRowSelectionChanged={onRowSelectionChanged}
      />,
    );

    await userEvent.click(screen.getAllByRole("checkbox")[1]);

    expect(onRowSelectionChanged).toHaveBeenLastCalledWith([
      expect.objectContaining({ original: data[1] }),
    ]);
  });

  it("renders the empty text when there is no data", () => {
    customRender(
      <SimpleTable
        data={[]}
        columns={columns}
        tableStyles={{ emptyText: "Nothing here" }}
      />,
    );

    expect(screen.getByText("Nothing here")).toBeInTheDocument();
  });
});
