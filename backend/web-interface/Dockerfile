FROM node:18-alpine

WORKDIR /app

    # Copy package files
    COPY package.json ./

# Install dependencies
RUN npm install --only=production

# Copy the rest of the source code
COPY . .

EXPOSE 3000

CMD ["npm", "start"]
