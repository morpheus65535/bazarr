import { describe, expect, it } from "vitest";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import { customRender, screen } from "@/tests";
import GroupTable from "./GroupTable";

interface Item {
  name: string;
  value: number;
}

const columns: ColumnDef<Item, unknown>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "value", header: "Value" },
];

const data: Item[] = [
  { name: "Group A", value: 1 },
  { name: "Group A", value: 2 },
  { name: "Group B", value: 3 },
];

describe("GroupTable", () => {
  it("renders rows grouped by the configured column", () => {
    customRender(
      <GroupTable
        data={data}
        columns={columns}
        state={{ grouping: ["name"] }}
      />,
    );

    expect(screen.getByText("Group A")).toBeInTheDocument();
    expect(screen.getByText("Group B")).toBeInTheDocument();
  });
});
