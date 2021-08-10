import {
  configureStore,
  createAction,
  createAsyncThunk,
  createReducer,
} from "@reduxjs/toolkit";
import {} from "jest";
import { AsyncUtility } from "../utils/async";
import {
  createAsyncItemReducer,
  createAsyncListReducer,
} from "../utils/factory";

interface TestType {
  id: string;
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

const defaultItem: TestType = { id: "123", name: "test" };

const reset = createAction("reducer/reset");

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

const reducer = createReducer(defaultState, (builder) => {
  createAsyncItemReducer(
    builder,
    { all: itemResolvedAction, dirty: itemDirtyAction },
    (s) => s.item
  );
  createAsyncItemReducer(builder, { all: itemRejectedAction }, (s) => s.item);

  createAsyncListReducer<Reducer, Async.IdType, TestType, "id">(
    builder,
    (s) => s.list,
    "id",
    {}
  );

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

  store.dispatch(itemDirtyAction());
  expect(store.getState().item.content).toBeNull();
  expect(store.getState().item.state).toEqual("uninitialized");

  await store.dispatch(itemResolvedAction());

  expect(store.getState().item.error).toBeNull();
  expect(store.getState().item.content).toEqual(defaultItem);
  expect(store.getState().item.state).toEqual("succeeded");

  store.dispatch(itemDirtyAction());
  expect(store.getState().item.content).toEqual(defaultItem);
  expect(store.getState().item.state).toEqual("dirty");

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

it("list update", () => {
  const store = createNewStore();
});
