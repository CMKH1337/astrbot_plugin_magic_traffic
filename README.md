# AstrBot VPN 流量查询插件

一个用于查询 Clash/V2Ray 订阅剩余流量的 AstrBot 插件。

<p align="center">
  <img src="https://count.getloli.com/get/@astrbot_plugin_magic_traffic?theme=gelbooru" alt="访问计数" />
</p>

## 功能特性

-  支持多个订阅链接管理
-  自动解析订阅流量信息（上传、下载、总量、剩余）
-  显示使用率和可视化进度条
-  显示订阅到期时间
-  自动转换流量单位（B/KB/MB/GB/TB）
-  支持单独查询或批量查询

## 安装方法

1. 将插件文件夹放入 AstrBot 的 `data/plugins/` 目录
2. 重启 AstrBot 或使用插件管理命令重载插件
3. 在 AstrBot WebUI 中配置插件参数

## 配置说明

在插件配置页面中需要配置以下参数：

### 订阅列表 (subscriptions)

在 AstrBot WebUI 的插件配置页中，点击 `添加订阅链接`，然后按表单填写：

- **name**: 订阅名称，方便识别
- **url**: Clash 订阅链接（必须支持流量查询）
- **user_agent**: 请求时使用的 User-Agent，默认为 "clash"

### 自动转换单位 (auto_convert_unit)

是否自动将流量转换为合适的单位（KB/MB/GB/TB），默认为 `true`

## 使用方法

### 查询所有订阅流量

```
/流量
```

### 查询指定订阅流量

```
/流量 我的VPN
```

### 添加订阅

```
/添加订阅 <名称> <订阅链接> [User-Agent]
```

### 显示帮助

```
/流量 help
```

## 输出示例

```
MY VPN
上传 477.23 MB  下载 7.32 GB
已用 7.78 GB / 100.00 GB
剩余 92.22 GB
到期 2027-02-02 15:48:24
```

## 支持的订阅格式

该插件支持在响应头中包含 `subscription-userinfo` 或 `Subscription-UserInfo` 字段的订阅链接。

响应头格式示例：
```
subscription-userinfo: upload=5617737728; download=49036984320; total=107374182400; expire=1722527999
```

## 注意事项

1. 确保订阅链接支持流量查询功能（部分机场不提供此功能）
2. 订阅链接请勿泄露给他人
3. 建议定期更换订阅链接以保证安全

## 兼容性

- AstrBot 版本：>= 4.16
- Python 版本：>= 3.8

## 依赖项

- aiohttp >= 3.8.0

- # astrbot_plugin_magic_traffic v1.2.2 更新日志

发布日期：2026-08-11

## 新增功能

### 支持通过指令添加订阅

用户现在可以直接在会话中添加属于自己的订阅：

```text
/添加订阅 <名称> <订阅链接> [User-Agent]
```

示例：

```text
/添加订阅 主订阅 https://example.com/sub clash
```

- 自动绑定当前用户 ID
- 自动保存至插件配置
- 用户只能查询自己添加的订阅
- 默认仅允许在私聊中添加
- 默认每个用户最多保存 10 个订阅
- 禁止同一用户添加重名订阅
- User-Agent 可省略，默认使用 `clash`

### 新增流量帮助指令

支持以下帮助指令：

```text
/流量 help
/流量 -h
/流量 --help
/流量 帮助
```

帮助内容：

```text
VPN 流量查询
/流量  查询自己的全部订阅
/流量 <订阅名称>  查询指定订阅
/添加订阅 <名称> <订阅链接> [User-Agent]
/流量 help  显示帮助
```

当前查询结果包含：

- 上传流量
- 下载流量
- 已用流量
- 总流量
- 剩余流量
- 到期时间

## 安全优化

- 仅接受 HTTP 或 HTTPS 订阅地址
- 拒绝明显指向本机、回环地址或内网 IP 的订阅链接
- 默认禁止在群聊中发送和保存订阅链接
- 查询结果及错误日志不会暴露完整订阅地址
- 限制订阅名称和 User-Agent 的最大长度
- 限制每个用户可保存的订阅数量

## 配置项

新增以下配置：

- `allow_group_add`：是否允许用户在群聊中添加订阅，默认关闭
- `max_user_subscriptions`：每个用户最多保存的订阅数量，默认值为 10
