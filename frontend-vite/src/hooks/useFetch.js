import { useState, useEffect } from "react";

export const useFetch = (mockData) => {
  const [data, setData] = useState([]);

  useEffect(() => {
    // имитация API
    setTimeout(() => {
      setData(mockData); //заменить потом нужно на реальный api
    }, 500);
  }, []);

  return data;
};