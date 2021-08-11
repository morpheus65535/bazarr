import {
  configureStore,
  createAction,
  createAsyncThunk,
  createReducer,
} from "@reduxjs/toolkit";
import {} from "jest";
import { intersectionWith } from "lodash";
import { defaultList, defaultState, TestType } from "../tests/helper";
import { createAsyncListReducer } from "../utils/factory";

const allResolved = createAsyncThunk("all/resolved", () => {
  return new Promise<TestType[]>((resolve) => {
    resolve(defaultList);
  });
});
const allRejected = createAsyncThunk("all/rejected", () => {
  return new Promise<TestType[]>((resolve, rejected) => {
    rejected("Error");
  });
});
const idsResolved = createAsyncThunk("ids/resolved", (param: number[]) => {
  return new Promise<TestType[]>((resolve) => {
    resolve(intersectionWith(defaultList, param, (l, r) => l.id === r));
  });
});
const idsRejected = createAsyncThunk("ids/rejected", (param: number[]) => {
  return new Promise<TestType[]>((resolve, rejected) => {
    rejected("Error");
  });
});
const removeIds = createAction<number[]>("remove/id");
const dirty = createAction<number[]>("dirty/id");

const reducer = createReducer(defaultState, (builder) => {
  createAsyncListReducer(builder, (s) => s.list, "id", {
    all: allResolved,
    ids: idsResolved,
    removeIds,
    dirty,
  });
  createAsyncListReducer(builder, (s) => s.list, "id", {
    all: allRejected,
    ids: idsRejected,
  });
});

function testList(
  store: ReturnType<typeof createStore>,
  callback: (list: Async.List<TestType>) => void
) {
  const list = store.getState().list;
  callback(list);
}

function createStore() {
  const store = configureStore({
    reducer,
  });
  expect(store.getState()).toEqual(defaultState);
  return store;
}

it("list update all", async () => {
  const store = createStore();

  await store.dispatch(allResolved());
  testList(store, (list) => {
    expect(list.content).toEqual(defaultList);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("succeeded");
  });

  await store.dispatch(allRejected());
  testList(store, (list) => {
    expect(list.content).toEqual(defaultList);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).not.toBeNull();
    expect(list.state).toEqual("failed");
  });
});

it("list mark dirty", async () => {
  const store = createStore();
  await store.dispatch(allResolved());

  store.dispatch(dirty([1, 2, 3]));
  testList(store, (list) => {
    expect(list.content).toEqual(defaultList);
    expect(list.dirtyEntities).toHaveLength(3);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("dirty");
  });
});

it("list update by ids", async () => {
  const store = createStore();

  // update by range should be succeeded
  await store.dispatch(idsResolved([1, 2]));
  testList(store, (list) => {
    expect(list.content).toHaveLength(2);
    expect(list.content[0].id).toEqual(2);
    expect(list.content[1].id).toEqual(1);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("succeeded");
  });

  // re-update by range shouldn't change anything
  await store.dispatch(idsResolved([1, 2]));
  testList(store, (list) => {
    expect(list.content).toHaveLength(2);
    expect(list.content[0].id).toEqual(2);
    expect(list.content[1].id).toEqual(1);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("succeeded");
  });

  // add and update by range shouldn't add duplicative data
  await store.dispatch(idsResolved([2, 3]));
  testList(store, (list) => {
    expect(list.content).toHaveLength(3);
    expect(list.content[0].id).toEqual(3);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("succeeded");
  });

  await store.dispatch(idsResolved([5, 6]));
  testList(store, (list) => {
    expect(list.content).toHaveLength(5);
    expect(list.content[0].id).toEqual(6);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("succeeded");
  });

  await store.dispatch(idsResolved([7, 8]));
  testList(store, (list) => {
    expect(list.content).toHaveLength(6);
    expect(list.content[0].id).toEqual(7);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("succeeded");
  });

  await store.dispatch(idsResolved([999]));
  testList(store, (list) => {
    expect(list.content).toHaveLength(6);
    expect(list.content[0].id).toEqual(7);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("succeeded");
  });

  store.dispatch(dirty([1, 2, 3]));
  testList(store, (list) => {
    expect(list.dirtyEntities).toHaveLength(3);
    expect(list.state).toEqual("dirty");
  });

  await store.dispatch(idsRejected([1, 2]));
  testList(store, (list) => {
    expect(list.dirtyEntities).toHaveLength(3);
    expect(list.state).toEqual("failed");
  });

  // Partially update shouldn't change state to succeeded
  await store.dispatch(idsResolved([1, 2]));
  testList(store, (list) => {
    expect(list.dirtyEntities).toHaveLength(1);
    expect(list.state).toEqual("dirty");
  });

  // When all dirty entities are resolved, change state to succeeded
  await store.dispatch(idsResolved([3]));
  testList(store, (list) => {
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.state).toEqual("succeeded");
  });

  store.dispatch(dirty([999]));
  await store.dispatch(idsResolved([999]));
  testList(store, (list) => {
    expect(list.content.find((v) => v.id === 999)).toBeUndefined();
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.state).toBe("succeeded");
  });
});

it("list remove by ids", async () => {
  const store = createStore();

  await store.dispatch(allResolved());
  const totalSize = store.getState().list.content.length;

  // Remove by id should work
  store.dispatch(removeIds([1, 2, 3]));
  testList(store, (list) => {
    expect(list.content).toHaveLength(totalSize - 3);
    expect(list.state).toEqual("succeeded");
  });

  // Remove non-exist id shouldn't change anything
  store.dispatch(removeIds([1, 2, 3]));
  testList(store, (list) => {
    expect(list.content).toHaveLength(totalSize - 3);
    expect(list.state).toEqual("succeeded");
  });

  // Partically remove id should work
  store.dispatch(removeIds([2, 3, 4]));
  testList(store, (list) => {
    expect(list.content).toHaveLength(totalSize - 4);
    expect(list.state).toEqual("succeeded");
  });

  store.dispatch(dirty([5, 6, 7]));
  testList(store, (list) => {
    expect(list.dirtyEntities).toHaveLength(3);
    expect(list.state).toEqual("dirty");
  });

  // Partically remove id should remove dirty entities
  store.dispatch(removeIds([6, 7]));
  testList(store, (list) => {
    expect(list.dirtyEntities).toHaveLength(1);
    expect(list.state).toEqual("dirty");
  });

  store.dispatch(removeIds([5]));
  testList(store, (list) => {
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.state).toEqual("succeeded");
  });
});
