# oneshare_base

上海文享信息科技有限公司-Odoo基础模块

### RESTful API

> 客户端header中增加 X-Org-Name: oneshare, Content-Type: application/json

> 需认证的接口需要先调用/api/v1/login接口获取session_id,
> 并在后续接口调用中header中增加: X-Openerp-Session-Id: ${session_id}

### 环境变量

```shell
ENV_ENABLE_SSO: false # 是否启用SSO功能
ENV_ONESHARE_SIGNUP_PUBLIC_USER: false # 是否signup创建公用用户(可登陆系统)
ENV_ONESHARE_SQL_REC_LIMT: 15 # SQL 查询记录限制
ONESHARE_DEFAULT_SPC_MIN_LIMIT: 50 # SPC 查询最小数量
ONESHARE_DEFAULT_SPC_MAX_LIMIT: 1000 # SPC 查询最大数量
ENV_SESSION_REDIS_HOST: localhost # session保存redis, 使用host

```

