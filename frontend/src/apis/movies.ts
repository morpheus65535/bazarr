import { AxiosResponse } from "axios";
import apis from ".";

class MovieApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/movies${path}`, { params });
  }

  postForm<T>(
    path: string,
    formdata?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    return apis.post(`/movies${path}`, formdata, params);
  }

  patch<T>(path: string, form?: any, params?: any): Promise<AxiosResponse<T>> {
    return apis.patch(`/movies${path}`, form, params);
  }

  delete<T>(path: string, form?: any, params?: any): Promise<AxiosResponse<T>> {
    return apis.delete(`/movies${path}`, form, params);
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
      this.postForm<void>("", { ...form }, { radarrid: id })
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
      this.postForm("/subtitles", form, { radarrid: id })
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
