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
  createAsyncItemReducer(builder, { all: allResolved, dirty }, (s) => s.item);
  createAsyncItemReducer(builder, { all: allRejected }, (s) => s.item);
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

  await store.dispatch(allResolved());
  testItem(store, (item) => {
    expect(store.getState().item.error).toBeNull();
    expect(store.getState().item.content).toEqual(defaultItem);
    expect(store.getState().item.state).toEqual("succeeded");
  });

  await store.dispatch(allRejected());
  testItem(store, (item) => {
    expect(store.getState().item.error).toEqual("Error");
    expect(store.getState().item.content).toEqual(defaultItem);
    expect(store.getState().item.state).toEqual("failed");
  });

  await store.dispatch(allResolved());
  testItem(store, (item) => {
    expect(store.getState().item.error).toBeNull();
    expect(store.getState().item.content).toEqual(defaultItem);
    expect(store.getState().item.state).toEqual("succeeded");
  });
});

it("item mark dirty", async () => {
  const store = createStore();

  store.dispatch(dirty());
  testItem(store, (item) => {
    expect(store.getState().item.content).toBeNull();
    expect(store.getState().item.state).toEqual("uninitialized");
  });

  await store.dispatch(allResolved());
  store.dispatch(dirty());
  testItem(store, (item) => {
    expect(store.getState().item.content).toEqual(defaultItem);
    expect(store.getState().item.state).toEqual("dirty");
  });
});
