import { AxiosResponse } from 'axios';
import apis from '.';

interface Series {
    missing_episodes: number;
}

interface Movies {
    missing_movies: number;
}

interface Providers {
    throttled_providers: number;
}

export default class BadgesApi {
    get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
        return apis.axios.get(`/${path}`, {params});
    }

    async series() {
        return new Promise<number>((resolve, reject) => {
            this.get<Series>('badges_series')
            .then((result) => {
                resolve(result.data.missing_episodes);
            })
            .catch((reason) => {
                reject(reason);
            })
        })
    }

    async movies() {
        return new Promise<number>((resolve, reject) => {
            this.get<Movies>('badges_movies')
            .then((result) => {
                resolve(result.data.missing_movies);
            })
            .catch((reason) => {
                reject(reason);
            })
        });
    }

    async providers() {
        return new Promise<number>((resolve, reject) => {
            this.get<Providers>('badges_providers')
            .then((result) => {
                resolve(result.data.throttled_providers);
            })
            .catch((reason) => {
                reject(reason);
            })
        });
    }
}