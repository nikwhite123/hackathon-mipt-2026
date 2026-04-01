import { useState, useEffect } from "react";

export const useFetch = (mockData) => {
  const [data, setData] = useState([]);

  useEffect(() => {
    // имитация API
    setTimeout(() => {
      setData(mockData);
    }, 500);
  }, []);

  return data;
};