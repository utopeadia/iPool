# 构建阶段
FROM node:16-alpine as build-stage

WORKDIR /app

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装项目依赖
RUN npm install

# 复制项目文件并构建应用
COPY . .
RUN npm run build

# 生产阶段
FROM nginx:stable-alpine as production-stage

# 复制构建好的文件到nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制nginx配置文件
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露80端口
EXPOSE 80

# 启动nginx并保持在前台
CMD ["nginx", "-g", "daemon off;"]
