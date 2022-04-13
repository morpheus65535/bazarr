import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { QueryPageTable, Toolbox } from "@/components";
import { faList } from "@fortawesome/free-solid-svg-icons";
import { useNavigate } from "react-router-dom";
import { Column } from "react-table";

interface Props<T extends Item.Base = Item.Base> {
  query: UsePaginationQueryResult<T>;
  columns: Column<T>[];
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
