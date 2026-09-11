FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install --no-audit

COPY . .

EXPOSE 3001

CMD ["npm", "run", "dev", "--", "-p", "3001"]
