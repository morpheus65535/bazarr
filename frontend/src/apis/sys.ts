import {} from 'axios';
import apis from '.';

export default class SystemApi {
    get<T>(path: string, params?: any): Promise<T> {
        return apis.axios.get(`/${path}`, {params});
    }

    async shutdown() {
        return this.get<never>('shutdown');
    }

    async restart() {
        return this.get<never>('restart');
    }
}