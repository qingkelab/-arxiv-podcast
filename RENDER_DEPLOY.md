# 部署到 Render

## 一键部署

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/qingkelab/-arxiv-podcast)

## 手动部署步骤

1. **Fork 或导入仓库到 GitHub**
   - 确保仓库是公开的

2. **在 Render 创建 Web Service**
   - 登录 https://dashboard.render.com
   - New → Web Service
   - 选择 GitHub 仓库

3. **配置**
   - Name: `arxiv-podcast`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python web_server.py`
   - Plan: Standard ($7/月) 或 Free (有限制)

4. **环境变量**
   - `OPENAI_API_KEY`: 你的 API Key
   - `PORT`: 8080

5. **磁盘（可选）**
   - 用于存储生成的视频
   - Mount Path: `/opt/render/project/output`
   - Size: 5GB

## 限制

**Free 计划：**
- 15 分钟超时（可能不够生成视频）
- 512MB 内存
- 无持久化存储

**Standard 计划 ($7/月)：**
- 无超时限制
- 2GB 内存
- 支持磁盘持久化

## 建议

对于视频生成功能，建议使用 **Standard 计划** 或部署到自己的 VPS。

如果只是测试 API 和脚本生成，Free 计划够用。
