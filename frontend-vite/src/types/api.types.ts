
export interface User {
    id: number;
    name: string;
}

export interface ApiResponse<T> {
    data: T;
    error?: string;
}

export {};