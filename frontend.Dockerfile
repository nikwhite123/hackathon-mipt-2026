FROM node:20-slim

WORKDIR /app


COPY ./frontend-vite/package*.json ./
RUN npm install


COPY ./frontend-vite ./
RUN npx vite build


RUN npm install -g serve
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]