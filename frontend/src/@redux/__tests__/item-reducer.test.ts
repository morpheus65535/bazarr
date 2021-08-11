import {
  configureStore,
  createAction,
  createAsyncThunk,
  createReducer,
} from "@reduxjs/toolkit";
import {} from "jest";
import { defaultState, TestType } from "../tests/helper";
import { createAsyncItemReducer } from "../utils/factory";

// Item
const defaultItem: TestType = { id: 0, name: "test" };
const allResolved = createAsyncThunk("all/resolved", () => {
  return new Promise<TestType>((resolve) => {
    resolve(defaultItem);
  });
});
const allRejected = createAsyncThunk("all/rejected", () => {
  return new Promise<TestType>((resolve, rejected) => {
    rejected("Error");
  });
});
const dirty = createAction("dirty/ids");

const reducer = createReducer(defaultState, (builder) => {
  createAsyncItemReducer(builder, (s) => s.item, { all: allResolved, dirty });
  createAsyncItemReducer(builder, (s) => s.item, { all: allRejected });
});

function testItem(
  store: ReturnType<typeof createStore>,
  callback: (entities: Async.Item<TestType>) => void
) {
  const item = store.getState().item;
  callback(item);
}

function createStore() {
  const store = configureStore({
    reducer,
  });
  expect(store.getState()).toEqual(defaultState);
  return store;
}

// Begin Test Section

it("item update", async () => {
  const store = createStore();

  store.dispatch(dirty());
  testItem(store, (item) => {
    expect(item.error).toBeNull();
    expect(item.content).toBeNull();
  });

  await store.dispatch(allResolved());
  testItem(store, (item) => {
    expect(item.error).toBeNull();
    expect(item.content).toEqual(defaultItem);
  });

  await store.dispatch(allRejected());
  testItem(store, (item) => {
    expect(item.content).toEqual(defaultItem);
  });

  await store.dispatch(allResolved());
  testItem(store, (item) => {
    expect(item.content).toEqual(defaultItem);
  });
});

it("item state transfer", async () => {
  const store = createStore();

  store.dispatch(dirty());
  testItem(store, (item) => {
    expect(item.state).toEqual("uninitialized");
  });

  await store.dispatch(allResolved());
  testItem(store, (item) => {
    expect(item.state).toEqual("succeeded");
  });

  store.dispatch(dirty());
  testItem(store, (item) => {
    expect(item.state).toEqual("dirty");
  });

  await store.dispatch(allRejected());
  testItem(store, (item) => {
    expect(item.error).toEqual("Error");
    expect(item.state).toEqual("failed");
  });

  store.dispatch(dirty());
  testItem(store, (item) => {
    expect(item.state).toEqual("dirty");
  });

  await store.dispatch(allResolved());
  testItem(store, (item) => {
    expect(item.error).toBeNull();
    expect(item.state).toEqual("succeeded");
  });
});
