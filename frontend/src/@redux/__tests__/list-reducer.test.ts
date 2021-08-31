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
  createAsyncListReducer(builder, (s) => s.list, {
    all: allResolved,
    ids: idsResolved,
    removeIds,
    dirty,
  });
  createAsyncListReducer(builder, (s) => s.list, {
    all: allRejected,
    ids: idsRejected,
  });
});

function createStore() {
  const store = configureStore({
    reducer,
  });
  expect(store.getState()).toEqual(defaultState);
  return store;
}

let store = createStore();

function use(callback: (list: Async.List<TestType>) => void) {
  const list = store.getState().list;
  callback(list);
}

beforeEach(() => {
  store = createStore();
});

it("list all uninitialized -> succeeded", async () => {
  await store.dispatch(allResolved());
  use((list) => {
    expect(list.content).toEqual(defaultList);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.didLoaded).toHaveLength(defaultList.length);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("succeeded");
  });
});

it("list all uninitialized -> failed", async () => {
  await store.dispatch(allRejected());
  use((list) => {
    expect(list.content).toHaveLength(0);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).not.toBeNull();
    expect(list.state).toEqual("failed");
  });
});

it("list uninitialized -> dirty", () => {
  store.dispatch(dirty([0, 1]));
  use((list) => {
    expect(list.content).toHaveLength(0);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("uninitialized");
  });
});

it("list succeeded -> dirty", async () => {
  await store.dispatch(allResolved());
  store.dispatch(dirty([1, 2, 3]));
  use((list) => {
    expect(list.content).toEqual(defaultList);
    expect(list.dirtyEntities).toHaveLength(3);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("dirty");
  });
});

it("list ids uninitialized -> succeeded", async () => {
  await store.dispatch(idsResolved([0, 1, 2]));
  use((list) => {
    expect(list.content).toHaveLength(3);
    expect(list.didLoaded).toHaveLength(3);
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.error).toBeNull();
    expect(list.state).toEqual("succeeded");
  });
});

it("list ids succeeded -> dirty", async () => {
  await store.dispatch(idsResolved([0, 1]));
  store.dispatch(dirty([2, 3]));
  use((list) => {
    expect(list.dirtyEntities).toHaveLength(2);
    expect(list.state).toEqual("dirty");
  });
});

it("list ids succeeded -> dirty", async () => {
  await store.dispatch(idsResolved([0, 1, 2]));
  store.dispatch(dirty([2, 3]));
  use((list) => {
    expect(list.dirtyEntities).toHaveLength(2);
    expect(list.state).toEqual("dirty");
  });
});

it("list ids update data", async () => {
  await store.dispatch(idsResolved([0, 1]));
  await store.dispatch(idsResolved([3, 4]));
  use((list) => {
    expect(list.content).toHaveLength(4);
    expect(list.state).toEqual("succeeded");
  });
});

it("list ids update duplicative data", async () => {
  await store.dispatch(idsResolved([0, 1, 2]));
  await store.dispatch(idsResolved([2, 3]));
  use((list) => {
    expect(list.content).toHaveLength(4);
    expect(list.didLoaded).toHaveLength(4);
    expect(list.state).toEqual("succeeded");
  });
});

it("list ids update new data", async () => {
  await store.dispatch(idsResolved([0, 1]));
  await store.dispatch(idsResolved([2, 3]));
  use((list) => {
    expect(list.content).toHaveLength(4);
    expect(list.didLoaded).toHaveLength(4);
    expect(list.content[1].id).toBe(2);
    expect(list.content[0].id).toBe(3);
    expect(list.state).toEqual("succeeded");
  });
});

it("list ids empty data", async () => {
  await store.dispatch(idsResolved([0, 1, 2]));
  await store.dispatch(idsResolved([999]));
  use((list) => {
    expect(list.content).toHaveLength(3);
    expect(list.state).toEqual("succeeded");
  });
});

it("list ids duplicative dirty", async () => {
  await store.dispatch(idsResolved([0]));
  store.dispatch(dirty([2, 2]));
  use((list) => {
    expect(list.dirtyEntities).toHaveLength(1);
    expect(list.dirtyEntities).toContain("2");
    expect(list.state).toEqual("dirty");
  });
});

it("list ids resolved dirty", async () => {
  await store.dispatch(idsResolved([0, 1, 2]));
  store.dispatch(dirty([2, 3]));
  use((list) => {
    expect(list.content).toHaveLength(3);
    expect(list.dirtyEntities).toContain("2");
    expect(list.dirtyEntities).toContain("3");
    expect(list.state).toBe("dirty");
  });
});

it("list ids resolved dirty", async () => {
  await store.dispatch(idsResolved([0, 1, 2]));
  store.dispatch(dirty([1, 2, 3, 999]));
  await store.dispatch(idsResolved([1, 2]));
  use((list) => {
    expect(list.content).toHaveLength(3);
    expect(list.dirtyEntities).not.toContain("1");
    expect(list.dirtyEntities).not.toContain("2");
    expect(list.state).toBe("dirty");
  });

  await store.dispatch(idsResolved([3]));
  use((list) => {
    expect(list.content).toHaveLength(4);
    expect(list.dirtyEntities).not.toContain("3");
    expect(list.state).toBe("dirty");
  });

  await store.dispatch(idsResolved([999]));
  use((list) => {
    expect(list.content).toHaveLength(4);
    expect(list.dirtyEntities).not.toContain("999");
    expect(list.state).toBe("succeeded");
  });
});

it("list remove ids", async () => {
  await store.dispatch(allResolved());
  const totalSize = store.getState().list.content.length;

  store.dispatch(removeIds([1, 2]));
  use((list) => {
    expect(list.content).toHaveLength(totalSize - 2);
    expect(list.content.map((v) => v.id)).not.toContain(1);
    expect(list.content.map((v) => v.id)).not.toContain(2);
    expect(list.state).toEqual("succeeded");
  });
});

it("list remove dirty ids", async () => {
  await store.dispatch(allResolved());
  store.dispatch(dirty([1, 2, 3]));
  store.dispatch(removeIds([1, 2]));
  use((list) => {
    expect(list.dirtyEntities).not.toContain("1");
    expect(list.dirtyEntities).not.toContain("2");
    expect(list.state).toEqual("dirty");
  });
  store.dispatch(removeIds([3]));
  use((list) => {
    expect(list.dirtyEntities).toHaveLength(0);
    expect(list.state).toEqual("succeeded");
  });
});
