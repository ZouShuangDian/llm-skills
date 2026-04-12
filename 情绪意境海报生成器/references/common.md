# 通用配置说明

## 获取 API Key

1. 注册并登录 [阿里云](https://www.aliyun.com/)，完成实名认证
2. 访问 [百炼控制台](https://bailian.console.aliyun.com/)，开通百炼服务
3. 进入 **API-KEY 管理**，创建新的 API Key

## 配置环境变量

```bash
export DASHSCOPE_API_KEY="your-api-key"
```

或在项目根目录创建 `.env` 文件：

```
DASHSCOPE_API_KEY=your-api-key
```

## 费用参考

| 模型 | 价格 |
|---|---|
| wan2.7-image-pro | 0.5 元/张 |
| wan2.7-image | 0.2 元/张 |

> 本 Skill 使用 `wan2.7-image-pro`，推荐购买阿里云优惠套餐包降低成本。

## 依赖安装

```bash
pip install requests python-dotenv
```
