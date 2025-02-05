import axios from "axios";
import { Message } from "./types";

const apiClient = axios.create({});


if (process.env.NODE_ENV === "development") {
    apiClient.defaults.baseURL = "http://localhost:6006/api";
} else {
    apiClient.defaults.baseURL = "/api";
}

export const api = {
    chat: {
        send: async (message: string) => {
            const { data, status } = await apiClient.post("/chat", { message });
            if (status !== 200) {
                throw new Error(data.content)
            }
            return data as Message;
        },
    },
    getFile: async (file_name: string) => {
        const { data, status } = await apiClient.get(`/files`, {
            params: {
                file_name,
            },
            responseType: "arraybuffer",
        });

        if (status !== 200) {
            throw new Error(`HTTP error! status: ${status}`);
        }
        const binary = new Uint8Array(data);
        return binary;
    }
};