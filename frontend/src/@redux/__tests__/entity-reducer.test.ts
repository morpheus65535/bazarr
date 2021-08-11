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
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
    defaultList.forEach((v, index) => {
      const id = v.id.toString();
      expect(entities.content.ids[index]).toEqual(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
  });

  await store.dispatch(allRejected());
  testEntities(store, (entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.error).not.toBeNull();
    expect(entities.state).toBe("failed");
    defaultList.forEach((v, index) => {
      const id = v.id.toString();
      expect(entities.content.ids[index]).toEqual(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
  });
});

it("entity mark dirty", async () => {
  const store = createStore();
  await store.dispatch(allResolved());

  store.dispatch(dirty([1, 2, 3]));
  testEntities(store, (entities) => {
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
  const store = createStore();
  await store.dispatch(allResolved());

  const idsToRemove = [0, 1, 3, 5];
  const expectResults = differenceWith(
    defaultList,
    idsToRemove,
    (l, r) => l.id === r
  );

  store.dispatch(removeIds(idsToRemove));
  testEntities(store, (entities) => {
    expect(entities.state).toBe("succeeded");
    expectResults.forEach((v, index) => {
      const id = v.id.toString();
      expect(entities.content.ids[index]).toEqual(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
  });
});

it("entity update by range", async () => {
  const store = createStore();

  await store.dispatch(rangeResolved({ start: 0, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(2);
    defaultList.slice(0, 0 + 2).forEach((v) => {
      const id = v.id.toString();
      expect(entities.content.ids).toContain(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  // re-update by range shouldn't change anything
  await store.dispatch(rangeResolved({ start: 0, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(2);
    defaultList.slice(0, 0 + 2).forEach((v) => {
      const id = v.id.toString();
      expect(entities.content.ids).toContain(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  // add and update by range shouldn't add duplicative data
  await store.dispatch(rangeResolved({ start: 1, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(3);
    defaultList.slice(1, 1 + 2).forEach((v) => {
      const id = v.id.toString();
      expect(entities.content.ids).toContain(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  await store.dispatch(rangeResolved({ start: 4, length: 2 }));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(5);
    defaultList.slice(4, 4 + 2).forEach((v) => {
      const id = v.id.toString();
      expect(entities.content.ids).toContain(id);
      expect(entities.content.entities[id]).toEqual(v);
    });
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

  const testIds = async (idsToAdd: number[]) => {
    const expectResults = intersectionWith(
      defaultList,
      idsToAdd,
      (l, r) => l.id === r
    );

    await store.dispatch(idsResolved(idsToAdd));
    testEntities(store, (entities) => {
      expect(entities.content.ids).toHaveLength(defaultList.length);
      expectResults.forEach((v) => {
        const id = v.id.toString();
        expect(entities.content.ids).toContain(id);
        expect(entities.content.entities[id]).toEqual(v);
      });
      expect(entities.error).toBeNull();
      expect(entities.state).toBe("succeeded");
    });
  };

  await testIds([0, 1, 3, 5]);
  await testIds([4, 6]);

  await store.dispatch(idsResolved([999]));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(6);
    expect(entities.content.entities).not.toHaveProperty("999");
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  store.dispatch(dirty([0, 1, 2]));
  testEntities(store, (entities) => {
    expect(entities.content.ids).toHaveLength(defaultList.length);
    expect(entities.content.ids.filter(isString)).toHaveLength(6);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("dirty");
  });

  await store.dispatch(idsResolved([1, 2]));
  testEntities(store, (entities) => {
    expect(entities.dirtyEntities).toHaveLength(1);
    expect(entities.content.ids.filter(isString)).toHaveLength(7);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("dirty");
  });

  await store.dispatch(idsResolved([0]));
  testEntities(store, (entities) => {
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.content.ids.filter(isString)).toHaveLength(7);
    expect(entities.error).toBeNull();
    expect(entities.state).toBe("succeeded");
  });

  // non-exist entity update should remove ids from dirty list
  store.dispatch(dirty([999]));
  await store.dispatch(idsResolved([999]));
  testEntities(store, (entities) => {
    expect(entities.content.ids).not.toContain("999");
    expect(entities.content.entities).not.toHaveProperty("999");
    expect(entities.dirtyEntities).toHaveLength(0);
    expect(entities.state).toBe("succeeded");
  });
});

it("entity update by variant range", async () => {
  const store = createStore();
  await store.dispatch(allResolved());

  await store.dispatch(rangeResolvedLonger({ start: 0, length: 2 }));
  testEntities(store, (entities) => {
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
  testEntities(store, (entities) => {
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
  const store = createStore();
  await store.dispatch(allResolved());

  await store.dispatch(idsResolvedLonger([2, 3, 4]));
  testEntities(store, (entities) => {
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
  testEntities(store, (entities) => {
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
