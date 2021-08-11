import { AsyncUtility } from "../utils/async";

export interface TestType {
  id: number;
  name: string;
}

export interface Reducer {
  item: Async.Item<TestType>;
  list: Async.List<TestType>;
  entities: Async.Entity<TestType>;
}

export const defaultState: Reducer = {
  item: AsyncUtility.getDefaultItem(),
  list: AsyncUtility.getDefaultList("id"),
  entities: AsyncUtility.getDefaultEntity("id"),
};

export const defaultItem: TestType = { id: 0, name: "test" };

export const defaultList: TestType[] = [
  { id: 0, name: "test" },
  { id: 1, name: "test_1" },
  { id: 2, name: "test_2" },
  { id: 3, name: "test_3" },
  { id: 4, name: "test_4" },
  { id: 5, name: "test_5" },
  { id: 6, name: "test_6" },
  { id: 7, name: "test_6" },
];
