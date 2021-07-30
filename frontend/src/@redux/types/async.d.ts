import { EntityState } from "@reduxjs/toolkit";

namespace Async {
  type State = "loading" | "succeeded" | "failed" | "dirty" | "idle";

  type IdType = number | string;

  type BaseType = {
    state: State;
    error: Unknown | null;
  };

  type List<T> = BaseType & {
    dirtyEntities: IdType[];
    content: EntityState<T>;
  };

  type Item<T> = BaseType & {
    content: T | null;
  };

  type Pagination<T> = List<T> & {
    pageIndex: number;
  };
}
