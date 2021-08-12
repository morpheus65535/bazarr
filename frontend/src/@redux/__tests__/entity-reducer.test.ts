import {
  configureStore,
  createAction,
  createAsyncThunk,
  createReducer,
} from "@reduxjs/toolkit";
import {} from "jest";
import { differenceWith, intersectionWith, isString } from "lodash";
import { defaultList, defaultState, TestType } from "../tests/helper";
import { createAsyncEntityReducer } from "../utils/factory";

const newItem: TestType = {
  id: 123,
  name: "extended",
};

const longerList: TestType[] = [...defaultList, newItem];
const shorterList: TestType[] = defaultList.slice(0, defaultList.length - 1);

const allResolved = createAsyncThunk("all/resolved", () => {
  return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
    resolve({ total: defaultList.length, data: defaultList });
  });
});

const allResolvedLonger = createAsyncThunk("all/longer/resolved", () => {
  return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
    resolve({ total: longerList.length, data: longerList });
  });
});

const allResolvedShorter = createAsyncThunk("all/shorter/resolved", () => {
  return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
    resolve({ total: shorterList.length, data: shorterList });
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

const idsResolvedLonger = createAsyncThunk(
  "ids/longer/resolved",
  (param: number[]) => {
    return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
      resolve({
        total: longerList.length,
        data: intersectionWith(longerList, param, (l, r) => l.id === r),
      });
    });
  }
);

const idsResolvedShorter = createAsyncThunk(
  "ids/shorter/resolved",
  (param: number[]) => {
    return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
      resolve({
        total: shorterList.length,
        data: intersectionWith(shorterList, param, (l, r) => l.id === r),
      });
    });
  }
);

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

const rangeResolvedLonger = createAsyncThunk(
  "range/longer/resolved",
  (param: Parameter.Range) => {
    return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
      resolve({
        total: longerList.length,
        data: longerList.slice(param.start, param.start + param.length),
      });
    });
  }
);

const rangeResolvedShorter = createAsyncThunk(
  "range/shorter/resolved",
  (param: Parameter.Range) => {
    return new Promise<AsyncDataWrapper<TestType>>((resolve) => {
      resolve({
        total: shorterList.length,
        data: shorterList.slice(param.start, param.start + param.length),
      });
    });
  }
);

const allRejected = createAsyncThunk("all/rejected", () => {
  return new Promise<AsyncDataWrapper<TestType>>((resolve, rejected) => {
    rejected("Error");
  });
});
const idsRejected = createAsyncThunk("ids/rejected", (param: number[]) => {
  return new Promise<AsyncDataWrapper<TestType>>((resolve, rejected) => {
    rejected("Error");
  });
});
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

  createAsyncEntityReducer(builder, (s) => s.entities, {
    all: allResolvedLonger,
    range: rangeResolvedLonger,
    ids: idsResolvedLonger,
  });

  createAsyncEntityReducer(builder, (s) => s.entities, {
    all: allResolvedShorter,
    range: rangeResolvedShorter,
    ids: idsResolvedShorter,
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

function use(callback: (entities: Async.Entity<TestType>) => void) {
  const entities = store.getState().entities;
  callback(entities);
}

beforeEach(() => {
  store = createStore();
});

it("entity update all resolved", async () => {
  await store.dispatch(allResolved());
  use((entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
    defaultList.forEach((v, index) => {
      const id = v.id.toString();
      expect(entities.content.ids[index]).toEqual(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
  });
});

it("entity update all rejected", async () => {
  await store.dispatch(allRejected());
  use((entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.error).not.toBeNull();
    expect(entities.state).toBe("failed");
    expect(entities.content.ids).toHaveLength(0);
    expect(entities.content.entities).toEqual({});
  });
});

it("entity mark dirty", async () => {
  await store.dispatch(allResolved());

  store.dispatch(dirty([1, 2, 3]));
  use((entities) => {
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("dirty");
    defaultList.forEach((v, index) => {
      const id = v.id.toString();
      expect(entities.content.ids[index]).toEqual(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
  });
});

it("delete entity item", async () => {
  await store.dispatch(allResolved());

  const idsToRemove = [0, 1, 3, 5];
  const expectResults = differenceWith(
    defaultList,
    idsToRemove,
    (l, r) => l.id === r
  );

  store.dispatch(removeIds(idsToRemove));
  use((entities) => {
    expect(entities.state).toBe("succeeded");
    expectResults.forEach((v, index) => {
      const id = v.id.toString();
      expect(entities.content.ids[index]).toEqual(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
  });
});

it("entity update by range", async () => {
  await store.dispatch(rangeResolved({ start: 0, length: 2 }));
  await store.dispatch(rangeResolved({ start: 4, length: 2 }));
  use((entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(4);
    [0, 1, 4, 5].forEach((v) => {
      const id = v.toString();
      expect(entities.content.ids).toContain(id);
      expect(entities.content.entities[id].id).toEqual(v);
    });
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });
});

it("entity update by duplicative range", async () => {
  await store.dispatch(rangeResolved({ start: 0, length: 2 }));
  await store.dispatch(rangeResolved({ start: 1, length: 2 }));
  use((entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(3);
    defaultList.slice(0, 3).forEach((v) => {
      const id = v.id.toString();
      expect(entities.content.ids).toContain(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });
});

it("entity resolved by dirty", async () => {
  await store.dispatch(rangeResolved({ start: 0, length: 2 }));
  store.dispatch(dirty([1, 2, 3]));
  await store.dispatch(rangeResolved({ start: 1, length: 2 }));
  use((entities) => {
    expect(entities.dirtyEntities).not.toContain("1");
    expect(entities.dirtyEntities).not.toContain("2");
    expect(entities.dirtyEntities).toContain("3");
    expect(entities.state).toBe("dirty");
  });
  await store.dispatch(rangeResolved({ start: 1, length: 3 }));
  use((entities) => {
    expect(entities.dirtyEntities).not.toContain("1");
    expect(entities.dirtyEntities).not.toContain("2");
    expect(entities.dirtyEntities).not.toContain("3");
    expect(entities.state).toBe("succeeded");
  });
});

it("entity update by ids", async () => {
  await store.dispatch(idsResolved([999]));
  use((entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(0);
    expect(entities.content.entities).not.toHaveProperty("999");
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });
});

it("entity resolved dirty by ids", async () => {
  await store.dispatch(idsResolved([0, 1, 2, 3, 4]));
  store.dispatch(dirty([0, 1, 2, 3]));
  await store.dispatch(idsResolved([0, 1]));
  use((entities) => {
    expect(entities.dirtyEntities).toHaveLength(2);
    expect(entities.content.ids.filter(isString)).toHaveLength(5);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("dirty");
  });
});

it("entity resolved non-exist by ids", async () => {
  await store.dispatch(idsResolved([0, 1]));
  store.dispatch(dirty([999]));
  await store.dispatch(idsResolved([999]));
  use((entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.state).toBe("succeeded");
  });
});

it("entity update by variant range", async () => {
  await store.dispatch(allResolved());

  await store.dispatch(rangeResolvedLonger({ start: 0, length: 2 }));
  use((entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.state).toBe("succeeded");
    expect(entities.content.ids).toHaveLength(longerList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(2);
    longerList.slice(0, 2).forEach((v) => {
      const id = v.id.toString();
      expect(entities.content.ids).toContain(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
  });

  await store.dispatch(allResolved());
  await store.dispatch(rangeResolvedShorter({ start: 0, length: 2 }));
  use((entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.state).toBe("succeeded");
    expect(entities.content.ids).toHaveLength(shorterList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(2);
    shorterList.slice(0, 2).forEach((v) => {
      const id = v.id.toString();
      expect(entities.content.ids).toContain(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
  });
});

it("entity update by variant ids", async () => {
  await store.dispatch(allResolved());

  await store.dispatch(idsResolvedLonger([2, 3, 4]));
  use((entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.state).toBe("succeeded");
    expect(entities.content.ids).toHaveLength(longerList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(3);
    Array(3)
      .fill(undefined)
      .forEach((v) => {
        expect(entities.content.ids[v]).not.toBeNull();
      });
  });

  await store.dispatch(allResolved());
  await store.dispatch(idsResolvedShorter([2, 3, 4]));
  use((entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.state).toBe("succeeded");
    expect(entities.content.ids).toHaveLength(shorterList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(3);
    Array(3)
      .fill(undefined)
      .forEach((v) => {
        expect(entities.content.ids[v]).not.toBeNull();
      });
  });
});
