import axios from 'axios';

const axiosClient = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

axiosClient.interceptors.response.use(
    (response: any) => response,
    (error: { response: { data: any; }; message: any; }) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

export default axiosClient;