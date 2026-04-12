import axios from 'axios'
import { getApiBaseUrl } from './config'

const axiosClient = axios.create({
	baseURL: getApiBaseUrl(),
	headers: {
		'Content-Type': 'application/json'
	}
})

axiosClient.interceptors.response.use(
	(response: any) => response,
	(error: { response?: { data?: any }; message: any }) => {
		console.error('API Error:', error.response?.data || error.message)
		return Promise.reject(error)
	}
)

export default axiosClient