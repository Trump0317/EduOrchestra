# EduOrchestra

多智能体驱动的 K12 数学自主学习系统。

## 快速启动

### 后端

```bash
cd server
cp ../.env.example ../.env  # 编辑 .env 填入 API Key
uvicorn main:app --reload
```

### 前端

```bash
cd client
npm install
npm run dev
```
