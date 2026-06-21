FROM node:20-alpine
WORKDIR /app
COPY package.json ./
# Adicionada a flag para ignorar o conflito de versões do React 19 com pacotes antigos
RUN npm install --legacy-peer-deps
COPY . .
CMD ["npm", "run", "dev"]
