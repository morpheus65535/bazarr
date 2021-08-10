import {
  configureStore,
  createAction,
  createAsyncThunk,
  createReducer,
} from "@reduxjs/toolkit";
import {} from "jest";
import { intersectionWith } from "lodash";
import { AsyncUtility } from "../utils/async";
import {
  createAsyncItemReducer,
  createAsyncListReducer,
} from "../utils/factory";

interface TestType {
  id: number;
  name: string;
}

interface Reducer {
  item: Async.Item<TestType>;
  list: Async.List<TestType>;
  entities: Async.Entity<TestType>;
}

const defaultState: Reducer = {
  item: AsyncUtility.getDefaultItem(),
  list: AsyncUtility.getDefaultList(),
  entities: AsyncUtility.getDefaultEntity("id"),
};

const reset = createAction("reducer/reset");

// Item
const defaultItem: TestType = { id: 0, name: "test" };
const itemResolvedAction = createAsyncThunk("item/all/resolved", () => {
  return new Promise<TestType>((resolve) => {
    resolve(defaultItem);
  });
});
const itemRejectedAction = createAsyncThunk("item/all/rejected", () => {
  return new Promise<TestType>((resolve, rejected) => {
    rejected("Error");
  });
});
const itemDirtyAction = createAction("item/dirty");

// List
const defaultList: TestType[] = [
  { id: 1, name: "test_1" },
  { id: 2, name: "test_2" },
  { id: 3, name: "test_3" },
  { id: 4, name: "test_4" },
  { id: 5, name: "test_5" },
  { id: 6, name: "test_6" },
  { id: 7, name: "test_6" },
];
const listResolvedActionAll = createAsyncThunk("list/all/resolved", () => {
  return new Promise<TestType[]>((resolve) => {
    resolve(defaultList);
  });
});
const listRejectedActionAll = createAsyncThunk("list/all/rejected", () => {
  return new Promise<TestType[]>((resolve, rejected) => {
    rejected("Error");
  });
});
const listResolvedActionIds = createAsyncThunk(
  "list/ids/resolved",
  (param: number[]) => {
    return new Promise<TestType[]>((resolve) => {
      resolve(intersectionWith(defaultList, param, (l, r) => l.id === r));
    });
  }
);
const listRejectedActionIds = createAsyncThunk(
  "list/ids/rejected",
  (param: number[]) => {
    return new Promise<TestType[]>((resolve, rejected) => {
      rejected("Error");
    });
  }
);
const listDirtyAction = createAction<number[]>("list/dirty/id");

const reducer = createReducer(defaultState, (builder) => {
  createAsyncItemReducer(
    builder,
    { all: itemResolvedAction, dirty: itemDirtyAction },
    (s) => s.item
  );
  createAsyncItemReducer(builder, { all: itemRejectedAction }, (s) => s.item);

  createAsyncListReducer(builder, (s) => s.list, "id", {
    all: listResolvedActionAll,
    ids: listResolvedActionIds,
    dirty: listDirtyAction,
  });
  createAsyncListReducer(builder, (s) => s.list, "id", {
    all: listRejectedActionAll,
    ids: listRejectedActionIds,
  });

  builder.addCase(reset, (state) => {
    state = defaultState;
  });
});

// Begin Test Section

function createNewStore() {
  const store = configureStore({
    reducer,
  });
  expect(store.getState()).toEqual(defaultState);
  return store;
}

it("item update", async () => {
  const store = createNewStore();

  await store.dispatch(itemResolvedAction());
  expect(store.getState().item.error).toBeNull();
  expect(store.getState().item.content).toEqual(defaultItem);
  expect(store.getState().item.state).toEqual("succeeded");

  await store.dispatch(itemRejectedAction());
  expect(store.getState().item.error).toEqual("Error");
  expect(store.getState().item.content).toEqual(defaultItem);
  expect(store.getState().item.state).toEqual("failed");

  await store.dispatch(itemResolvedAction());
  expect(store.getState().item.error).toBeNull();
  expect(store.getState().item.content).toEqual(defaultItem);
  expect(store.getState().item.state).toEqual("succeeded");
});

it("item mark dirty", async () => {
  const store = createNewStore();

  store.dispatch(itemDirtyAction());
  expect(store.getState().item.content).toBeNull();
  expect(store.getState().item.state).toEqual("uninitialized");

  await store.dispatch(itemResolvedAction());
  store.dispatch(itemDirtyAction());
  expect(store.getState().item.content).toEqual(defaultItem);
  expect(store.getState().item.state).toEqual("dirty");
});

it("list update", async () => {
  const store = createNewStore();

  await store.dispatch(listResolvedActionAll());
  expect(store.getState().list.content).toEqual(defaultList);
  expect(store.getState().list.dirtyEntities).toHaveLength(0);
  expect(store.getState().list.error).toBeNull();
  expect(store.getState().list.state).toEqual("succeeded");

  await store.dispatch(listRejectedActionAll());
  expect(store.getState().list.content).toEqual(defaultList);
  expect(store.getState().list.dirtyEntities).toHaveLength(0);
  expect(store.getState().list.error).not.toBeNull();
  expect(store.getState().list.state).toEqual("failed");

  store.dispatch(listDirtyAction([1, 2, 3]));
  expect(store.getState().list.content).toEqual(defaultList);
  expect(store.getState().list.dirtyEntities).toHaveLength(3);
  expect(store.getState().list.error).not.toBeNull();
  expect(store.getState().list.state).toEqual("dirty");
});

it("list update by range", async () => {
  const store = createNewStore();

  await store.dispatch(listResolvedActionIds([1, 2]));
  expect(store.getState().list.content).toHaveLength(2);
  expect(store.getState().list.content[0].id).toEqual(2);
  expect(store.getState().list.content[1].id).toEqual(1);
  expect(store.getState().list.dirtyEntities).toHaveLength(0);
  expect(store.getState().list.error).toBeNull();
  expect(store.getState().list.state).toEqual("succeeded");

  await store.dispatch(listResolvedActionIds([1, 2]));
  expect(store.getState().list.content).toHaveLength(2);
  expect(store.getState().list.content[0].id).toEqual(2);
  expect(store.getState().list.content[1].id).toEqual(1);
  expect(store.getState().list.dirtyEntities).toHaveLength(0);
  expect(store.getState().list.error).toBeNull();
  expect(store.getState().list.state).toEqual("succeeded");

  await store.dispatch(listResolvedActionIds([2, 3]));
  expect(store.getState().list.content).toHaveLength(3);
  expect(store.getState().list.content[0].id).toEqual(3);
  expect(store.getState().list.dirtyEntities).toHaveLength(0);
  expect(store.getState().list.error).toBeNull();
  expect(store.getState().list.state).toEqual("succeeded");

  await store.dispatch(listResolvedActionIds([5, 6]));
  expect(store.getState().list.content).toHaveLength(5);
  expect(store.getState().list.content[0].id).toEqual(6);
  expect(store.getState().list.dirtyEntities).toHaveLength(0);
  expect(store.getState().list.error).toBeNull();
  expect(store.getState().list.state).toEqual("succeeded");

  await store.dispatch(listResolvedActionIds([7, 8]));
  expect(store.getState().list.content).toHaveLength(6);
  expect(store.getState().list.content[0].id).toEqual(7);
  expect(store.getState().list.dirtyEntities).toHaveLength(0);
  expect(store.getState().list.error).toBeNull();
  expect(store.getState().list.state).toEqual("succeeded");

  store.dispatch(listDirtyAction([1, 2, 3]));
  expect(store.getState().list.dirtyEntities).toHaveLength(3);
  expect(store.getState().list.state).toEqual("dirty");

  await store.dispatch(listRejectedActionIds([1, 2]));
  expect(store.getState().list.dirtyEntities).toHaveLength(3);
  expect(store.getState().list.state).toEqual("failed");

  await store.dispatch(listResolvedActionIds([1, 2]));
  expect(store.getState().list.dirtyEntities).toHaveLength(1);
  expect(store.getState().list.state).toEqual("dirty");

  await store.dispatch(listResolvedActionIds([3]));
  expect(store.getState().list.dirtyEntities).toHaveLength(0);
  expect(store.getState().list.state).toEqual("succeeded");
});
