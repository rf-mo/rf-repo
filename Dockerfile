# Use the official Node.js image from Docker Hub
FROM node:14

# Create a directory for the app
WORKDIR /usr/src/app

# Copy the package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy the application code
COPY . .

# Expose port 3000
EXPOSE 3000

# Start the app
CMD [ "node", "index.js" ]

