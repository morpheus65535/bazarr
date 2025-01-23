import { useNavigate } from "react-router";
import { faList } from "@fortawesome/free-solid-svg-icons";
import { ColumnDef } from "@tanstack/react-table";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { QueryPageTable, Toolbox } from "@/components";

interface Props<T extends Item.Base = Item.Base> {
  query: UsePaginationQueryResult<T>;
  columns: ColumnDef<T>[];
}

function ItemView<T extends Item.Base>({ query, columns }: Props<T>) {
  const navigate = useNavigate();

  return (
    <>
      <Toolbox>
        <Toolbox.Button
          disabled={query.paginationStatus.totalCount === 0}
          icon={faList}
          onClick={() => navigate("edit")}
        >
          Mass Edit
        </Toolbox.Button>
      </Toolbox>
      <QueryPageTable
        columns={columns}
        query={query}
        tableStyles={{ emptyText: "No items found" }}
      ></QueryPageTable>
    </>
  );
}

export default ItemView;
