import BaseApi from "./base";

class MovieApi extends BaseApi {
  constructor() {
    super("/movies");
  }

  async blacklist(): Promise<Array<Blacklist.Movie>> {
    return new Promise<Array<Blacklist.Movie>>((resolve, reject) => {
      this.get<DataWrapper<Array<Blacklist.Movie>>>("/blacklist")
        .then((res) => {
          resolve(res.data.data);
        })
        .catch(reject);
    });
  }

  async addBlacklist(
    radarrid: number,
    form: FormType.AddBlacklist
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      this.post<void>("/blacklist", form, { radarrid })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async deleteBlacklist(
    all?: boolean,
    form?: FormType.DeleteBlacklist
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      this.delete<void>("/blacklist", form, { all })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async movies(id?: number) {
    return new Promise<AsyncDataWrapper<Item.Movie>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Item.Movie>>("", { radarrid: id })
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async moviesBy(start: number, length: number) {
    return new Promise<AsyncDataWrapper<Item.Movie>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Item.Movie>>("", { start, length })
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async modify(form: FormType.ModifyItem) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("", { radarrid: form.id, profileid: form.profileid })
        .then(() => resolve())
        .catch((err) => reject(err));
    });
  }

  async history(id?: number): Promise<Array<History.Movie>> {
    return new Promise<Array<History.Movie>>((resolve, reject) => {
      this.get<DataWrapper<Array<History.Movie>>>("/history", {
        radarrid: id,
      })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async action(action: FormType.MoviesAction) {
    return new Promise<void>((resolve, reject) => {
      this.patch("", action)
        .then(() => resolve())
        .catch(reject);
    });
  }

  async downloadSubtitles(id: number, form: FormType.Subtitle): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/subtitles", form, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async uploadSubtitles(
    id: number,
    form: FormType.UploadSubtitle
  ): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.post("/subtitles", form, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async deleteSubtitles(
    id: number,
    form: FormType.DeleteSubtitle
  ): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.delete("/subtitles", form, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new MovieApi();
