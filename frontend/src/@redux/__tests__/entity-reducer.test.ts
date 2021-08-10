import {
  configureStore,
  createAction,
  createAsyncThunk,
  createReducer,
} from "@reduxjs/toolkit";
import {} from "jest";
import { intersectionWith, isString } from "lodash";
import { defaultList, defaultState, TestType } from "../tests/helper";
import { createAsyncEntityReducer } from "../utils/factory";

const allResolved = createAsyncThunk("all/resolved", () => {
  return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
    resolve({ total: defaultList.length, data: defaultList });
  });
});
const allRejected = createAsyncThunk("all/rejected", () => {
  return new Promise<AsyncDataWrapper<TestType>>((resolve, rejected) => {
    rejected("Error");
  });
});
const idsResolved = createAsyncThunk("ids/resolved", (param: number[]) => {
  return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
    resolve({
      total: defaultList.length,
      data: intersectionWith(defaultList, param, (l, r) => l.id === r),
    });
  });
});
const idsRejected = createAsyncThunk("ids/rejected", (param: number[]) => {
  return new Promise<AsyncDataWrapper<TestType>>((resolve, rejected) => {
    rejected("Error");
  });
});
const rangeResolved = createAsyncThunk(
  "range/resolved",
  (param: Parameter.Range) => {
    return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
      resolve({
        total: defaultList.length,
        data: defaultList.slice(param.start, param.start + param.length),
      });
    });
  }
);
const rangeRejected = createAsyncThunk(
  "range/rejected",
  (param: Parameter.Range) => {
    return new Promise<AsyncDataWrapper<TestType>>((resolve, rejected) => {
      rejected("Error");
    });
  }
);
const removeIds = createAction<number[]>("remove/id");
const dirty = createAction<number[]>("dirty/id");

const reducer = createReducer(defaultState, (builder) => {
  createAsyncEntityReducer(builder, (s) => s.entities, {
    all: allResolved,
    range: rangeResolved,
    ids: idsResolved,
    dirty,
    removeIds,
  });
  createAsyncEntityReducer(builder, (s) => s.entities, {
    all: allRejected,
    range: rangeRejected,
    ids: idsRejected,
  });
});

function testEntities(
  store: ReturnType<typeof createStore>,
  callback: (entities: Async.Entity<TestType>) => void
) {
  const entities = store.getState().entities;
  callback(entities);
}

function createStore() {
  const store = configureStore({
    reducer,
  });
  expect(store.getState()).toEqual(defaultState);
  return store;
}

it("entity update all", async () => {
  const store = createStore();

  await store.dispatch(allResolved());
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(
      Object.keys(store.getState().entities.content.entities)
    ).toHaveLength(defaultList.length);
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  await store.dispatch(allRejected());
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(Object.keys(entities.content.entities)).toHaveLength(
      defaultList.length
    );
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.error).not.toBeNull();
    expect(entities.state).toBe("failed");
  });
});

it("entity mark dirty", async () => {
  const store = createStore();
  await store.dispatch(allResolved());

  store.dispatch(dirty([1, 2, 3]));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(Object.keys(entities.content.entities)).toHaveLength(
      defaultList.length
    );
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("dirty");
  });
});

it("entity update by range", async () => {
  const store = createStore();

  await store.dispatch(rangeResolved({ start: 0, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(2);
    expect(entities.content.ids).toContain("0");
    expect(entities.content.ids).toContain("1");
    expect(entities.content.entities["0"]).toEqual(defaultList[0]);
    expect(entities.content.entities["1"]).toEqual(defaultList[1]);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  // re-update by range shouldn't change anything
  await store.dispatch(rangeResolved({ start: 0, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(2);
    expect(entities.content.ids).toContain("0");
    expect(entities.content.ids).toContain("1");
    expect(entities.content.entities["0"]).toEqual(defaultList[0]);
    expect(entities.content.entities["1"]).toEqual(defaultList[1]);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  // add and update by range shouldn't add duplicative data
  await store.dispatch(rangeResolved({ start: 1, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(3);
    expect(entities.content.ids).toContain("2");
    expect(entities.content.entities["2"]).toEqual(defaultList[2]);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  await store.dispatch(rangeResolved({ start: 4, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(5);
    expect(entities.content.ids).toContain("5");
    expect(entities.content.entities["5"]).toEqual(defaultList[5]);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  store.dispatch(dirty([0, 1, 2]));
  testEntities(store, (entities) => {
    expect(entities.dirtyEntities).toHaveLength(3);
    expect(entities.state).toBe("dirty");
  });

  await store.dispatch(rangeResolved({ start: 0, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.dirtyEntities).toHaveLength(1);
    expect(entities.state).toBe("dirty");
  });

  await store.dispatch(rangeResolved({ start: 1, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.state).toBe("succeeded");
  });
});

it("entity update by ids", async () => {
  const store = createStore();
  await store.dispatch(idsResolved([0, 1]));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(2);
    expect(entities.content.entities).toHaveProperty("0");
    expect(entities.content.entities).toHaveProperty("1");
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  await store.dispatch(idsResolved([1, 2]));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(3);
    expect(entities.content.entities).toHaveProperty("2");
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  await store.dispatch(idsResolved([5, 6]));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(5);
    expect(entities.content.entities).toHaveProperty("5");
    expect(entities.content.entities).toHaveProperty("6");
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  await store.dispatch(idsResolved([999]));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(5);
    expect(entities.content.entities).not.toHaveProperty("999");
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  store.dispatch(dirty([0, 1, 2]));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(5);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("dirty");
  });

  await store.dispatch(idsResolved([1, 2]));
  testEntities(store, (entities) => {
    expect(entities.dirtyEntities).toHaveLength(1);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("dirty");
  });

  await store.dispatch(idsResolved([0]));
  testEntities(store, (entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });
});

it("entity update by variant range", () => {});
it("entity update by variant ids", () => {});
