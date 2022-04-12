import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { QueryPageTable, Toolbox } from "@/components";
import { TableStyleProps } from "@/components/tables/BaseTable";
import { faList } from "@fortawesome/free-solid-svg-icons";
import { useNavigate } from "react-router-dom";
import { Column, TableOptions } from "react-table";

interface Props<T extends Item.Base = Item.Base> {
  query: UsePaginationQueryResult<T>;
  columns: Column<T>[];
}

function ItemView<T extends Item.Base>({ query, columns }: Props<T>) {
  const navigate = useNavigate();

  const options: Partial<TableOptions<T> & TableStyleProps<T>> = {
    emptyText: `No Items Found`,
  };

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
        {...options}
        columns={columns}
        query={query}
        data={[]}
      ></QueryPageTable>
    </>
  );
}

export default ItemView;
