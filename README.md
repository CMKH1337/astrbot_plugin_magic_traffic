# AstrBot VPN 流量查询插件

一个用于查询 Clash/V2Ray 订阅剩余流量的 AstrBot 插件。

<p align="center">
  <img src="https://count.getloli.com/get/@astrbot_plugin_magic_traffic?theme=gelbooru-h" alt="访问计数" />
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

### 命令前缀 (command_prefix)

触发流量查询的命令，默认为 `流量`

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

## 输出示例

```
📊 我的VPN 流量信息
==============================
⬆️  上传: 5.23 GB
⬇️  下载: 45.67 GB
📈 已用: 50.90 GB
📦 总量: 100.00 GB
💾 剩余: 49.10 GB
📊 使用率: 50.90%
[██████████░░░░░░░░░░]
⏰ 到期时间: 2026-08-01 23:59:59
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
