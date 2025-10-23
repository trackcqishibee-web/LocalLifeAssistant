# 🚀 Local Life Assistant - 部署指南

完整的生产级部署解决方案，支持传统部署和 Docker 部署两种方式。

## 📋 快速开始

### 🎯 一键部署（推荐）

```bash
# 在服务器上运行
wget https://raw.githubusercontent.com/wjshku/LocalLifeAssistant/main/deploy/auto-deploy.sh
chmod +x auto-deploy.sh
./auto-deploy.sh
```

### 🐳 Docker 部署

```bash
# Docker 一键部署
wget https://raw.githubusercontent.com/wjshku/LocalLifeAssistant/main/deploy/docker/docker-deploy.sh
chmod +x docker/docker-deploy.sh
./docker/docker-deploy.sh
```

## 📁 部署脚本说明

### 🔢 传统部署脚本（按顺序执行）

| 脚本 | 功能 | 说明 |
|------|------|------|
| `01-server-setup.sh` | 服务器基础配置 | 安装依赖、配置防火墙、创建用户 |
| `02-app-deploy.sh` | 应用部署 | 克隆代码、安装依赖、构建前端 |
| `03-nginx-setup.sh` | Nginx 配置 | 配置反向代理、域名路由 |
| `04-ssl-setup.sh` | SSL 证书配置 | Let's Encrypt 证书、HTTPS |

### 🐳 Docker 部署脚本

| 脚本 | 功能 | 说明 |
|------|------|------|
| `docker/docker-deploy.sh` | Docker 环境部署 | 安装 Docker、配置容器 |
| `docker/docker-manage.sh` | Docker 服务管理 | 启动/停止/监控容器 |

### 🤖 自动化脚本

| 脚本 | 功能 | 说明 |
|------|------|------|
| `auto-deploy.sh` | 一键部署 | 自动执行所有传统部署步骤 |

## 🛠️ 部署方式选择

### 方式一：传统部署（生产推荐）

**适用场景：** 生产环境、需要精细控制、资源优化

```bash
# 1. 服务器初始化
./01-server-setup.sh

# 2. 应用部署
./02-app-deploy.sh

# 3. Web 服务器配置
./03-nginx-setup.sh

# 4. SSL 证书配置
./04-ssl-setup.sh
```

**优势：**
- ✅ 资源占用少
- ✅ 性能最优
- ✅ 易于调试
- ✅ 生产级稳定性

### 方式二：Docker 部署（开发推荐）

**适用场景：** 开发环境、快速部署、容器化需求

```bash
# 1. Docker 环境部署
./docker/docker-deploy.sh

# 2. 启动服务
cd docker && docker-compose up -d

# 3. 管理服务
./docker/docker-manage.sh start
```

**优势：**
- ✅ 环境隔离
- ✅ 快速部署
- ✅ 易于扩展
- ✅ 开发友好

## 🔧 配置文件

### 环境变量模板

| 文件 | 用途 | 说明 |
|------|------|------|
| `.env.production.example` | 生产环境配置 | 传统部署使用 |
| `.env.docker.example` | Docker 环境配置 | Docker 部署使用 |

### Nginx 配置

| 文件 | 用途 | 说明 |
|------|------|------|
| `nginx.conf` | 主配置文件 | 反向代理、SSL、安全头 |
| `docker/nginx-frontend.conf` | 前端配置 | 静态文件服务（Docker）|

### Docker 配置

| 文件 | 用途 | 说明 |
|------|------|------|
| `docker/docker-compose.yml` | 容器编排 | 服务定义、网络、卷 |
| `docker/Dockerfile.backend` | 后端镜像 | Python FastAPI 服务 |
| `docker/Dockerfile.frontend` | 前端镜像 | React + Nginx |

## 🚀 GitHub Actions 自动部署

### 配置 Secrets

在 GitHub 仓库设置中添加：

```
OPENAI_API_KEY=your_openai_api_key
SSH_PRIVATE_KEY=your_server_ssh_private_key
SERVER_IP=your_server_ip_address
```

### 触发部署

```bash
# 推送到 main 分支自动部署
git push origin main

# 或手动触发 GitHub Actions
```

## 📊 部署架构

### 传统部署架构

```
Internet → Cloudflare → Nginx → FastAPI Backend
                    ↓
                React Frontend
```

### Docker 部署架构

```
Internet → Cloudflare → Nginx → Docker Containers
                    ↓
            [Backend] [Frontend]
```

## 🔍 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   sudo netstat -tlnp | grep :80
   sudo netstat -tlnp | grep :8000
   ```

2. **权限问题**
   ```bash
   sudo chown -R appuser:appuser /opt/locallifeassistant
   ```

3. **SSL 证书问题**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

### 日志查看

```bash
# 应用日志
sudo journalctl -u locallifeassistant-backend -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Docker 日志
docker-compose logs -f
```

## 📞 支持

- 📧 问题反馈：GitHub Issues
- 📖 详细文档：各脚本内注释
- 🔧 技术支持：查看日志和错误信息

---

**🎉 部署完成后，你的应用将在 `https://your-domain.com` 上运行！**