import BaseApi from "./base";

class HistoryApi extends BaseApi {
  constructor() {
    super("/history");
  }

  async movies(): Promise<Array<MovieHistory>> {
    return new Promise<Array<MovieHistory>>((resolve, reject) => {
      this.get<DataWrapper<Array<MovieHistory>>>("/movies")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async series(): Promise<Array<SeriesHistory>> {
    return new Promise<Array<SeriesHistory>>((resolve, reject) => {
      this.get<DataWrapper<Array<SeriesHistory>>>("/series")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}

export default new HistoryApi();
