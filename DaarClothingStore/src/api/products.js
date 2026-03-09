import axios from 'axios';
import { API_URL } from './config';

export async function getProducts() {
  const response = await axios.get(`${API_URL}/api/products/`);
  return response.data;
}
