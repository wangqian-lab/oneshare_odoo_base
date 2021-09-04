# oneshare_base
上海文享信息科技有限公司-Odoo基础模块


### RESTful API
> 客户端header中增加 X-Org-Name: oneshare, Content-Type: application/json

> 需认证的接口需要先调用/api/v1/login接口获取session_id,
> 并在后续接口调用中header中增加: X-Openerp-Session-Id: ${session_id} 

