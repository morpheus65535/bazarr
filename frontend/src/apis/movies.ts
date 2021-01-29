import BasicApi from "./basic";

class MovieApi extends BasicApi {
  constructor() {
    super("/movies");
  }

  async blacklist(): Promise<Array<MovieBlacklist>> {
    return new Promise<Array<MovieBlacklist>>((resolve, reject) => {
      this.get<DataWrapper<Array<MovieBlacklist>>>("/blacklist")
        .then((res) => {
          resolve(res.data.data);
        })
        .catch(reject);
    });
  }

  async addBlacklist(radarrid: number, form: BlacklistAddForm): Promise<void> {
    return new Promise((resolve, reject) => {
      this.post<void>("/blacklist", form, { radarrid })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async deleteBlacklist(
    all?: boolean,
    form?: BlacklistDeleteForm
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      this.delete<void>("/blacklist", form, { all })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async movies(id?: number): Promise<Array<Movie>> {
    return new Promise<Array<Movie>>((resolve, reject) => {
      this.get<DataWrapper<Array<Movie>>>("", { radarrid: id })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async modify(id: number, form: ItemModifyForm) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("", { ...form }, { radarrid: id })
        .then(() => resolve())
        .catch((err) => reject(err));
    });
  }

  async wanted(): Promise<Array<WantedMovie>> {
    return new Promise<Array<WantedMovie>>((resolve, reject) => {
      this.get<DataWrapper<Array<WantedMovie>>>("/wanted")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async searchAllWanted(): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/wanted")
        .then(() => resolve())
        .catch(reject);
    });
  }

  async history(id: number): Promise<Array<MovieHistory>> {
    return new Promise<Array<MovieHistory>>((resolve, reject) => {
      this.get<DataWrapper<Array<MovieHistory>>>("/history", {
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

  async scanDisk(id: number): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/disk", undefined, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async searchMissing(id: number): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/missing", undefined, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async downloadSubtitles(id: number, form: SubtitleForm): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/subtitles", form, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async uploadSubtitles(id: number, form: SubtitleUploadForm): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.post("/subtitles", form, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async deleteSubtitles(id: number, form: SubtitleDeleteForm): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.delete("/subtitles", form, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new MovieApi();
