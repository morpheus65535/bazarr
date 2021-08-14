import BaseApi from "./base";

class MovieApi extends BaseApi {
  constructor() {
    super("/movies");
  }

  async blacklist(): Promise<Blacklist.Movie[]> {
    return new Promise<Blacklist.Movie[]>((resolve, reject) => {
      this.get<DataWrapper<Blacklist.Movie[]>>("/blacklist")
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

  async movies(radarrid?: number[]) {
    return new Promise<AsyncDataWrapper<Item.Movie>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Item.Movie>>("", { radarrid })
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async moviesBy(params: Parameter.Range) {
    return new Promise<AsyncDataWrapper<Item.Movie>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Item.Movie>>("", params)
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

  async wanted(params: Parameter.Range) {
    return new Promise<AsyncDataWrapper<Wanted.Movie>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Wanted.Movie>>("/wanted", params)
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async wantedBy(radarrid: number[]) {
    return new Promise<AsyncDataWrapper<Wanted.Movie>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Wanted.Movie>>("/wanted", { radarrid })
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async history(id?: number): Promise<History.Movie[]> {
    return new Promise<History.Movie[]>((resolve, reject) => {
      this.get<DataWrapper<History.Movie[]>>("/history", {
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
