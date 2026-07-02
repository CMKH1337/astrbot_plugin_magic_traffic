import json

import aiohttp
from datetime import datetime
from typing import Any, Dict, List, Optional

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register


@register(
    "astrbot_plugin_vpn_traffic",
    "tiger",
    "查询 Clash/V2Ray 订阅的剩余流量信息",
    "v1.0.0",
)
class VPNTrafficPlugin(Star):
    """查询 Clash/V2Ray 订阅剩余流量。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        
        # 调试：打印所有配置键和原始配置
        print("=" * 50)
        print("VPN流量插件配置调试信息")
        print("=" * 50)
        print(f"配置对象类型: {type(config)}")
        print(f"配置对象内容: {config}")
        
        raw_subscriptions = config.get("subscriptions", [])
        print(f"原始 subscriptions: {raw_subscriptions}")
        print(f"subscriptions 类型: {type(raw_subscriptions)}")
        print("=" * 50)
        
        logger.info(f"[VPN流量插件] 原始 subscriptions 配置: {raw_subscriptions}")
        logger.info(f"[VPN流量插件] subscriptions 类型: {type(raw_subscriptions)}")
        
        self.subscriptions = self.normalize_subscriptions(raw_subscriptions)
        self.auto_convert_unit = bool(config.get("auto_convert_unit", True))
        
        print(f"标准化后的订阅数量: {len(self.subscriptions)}")
        print(f"标准化后的订阅: {self.subscriptions}")
        print("=" * 50)
        
        logger.info(f"VPN流量查询插件已加载，已配置 {len(self.subscriptions)} 个订阅")
        logger.info(f"[VPN流量插件] 标准化后的订阅: {self.subscriptions}")

    @filter.command("流量")
    async def query_all_traffic(self, event: AstrMessageEvent, subscription_name: Optional[str] = None):
        """查询 VPN 订阅剩余流量。"""
        result = await self.query_traffic(subscription_name)
        yield event.plain_result(result)
    
    def normalize_subscriptions(self, subscriptions: Any) -> List[Dict[str, str]]:
        if isinstance(subscriptions, str):
            try:
                subscriptions = json.loads(subscriptions)
            except json.JSONDecodeError:
                logger.warning("subscriptions 配置不是有效的 JSON 字符串")
                return []

        if isinstance(subscriptions, dict):
            subscriptions = [subscriptions]

        if not isinstance(subscriptions, list):
            logger.warning(f"subscriptions 配置格式错误，期望 list，实际为 {type(subscriptions)}")
            return []

        normalized = []
        for subscription in subscriptions:
            if not isinstance(subscription, dict):
                logger.warning(f"忽略格式错误的订阅配置: {subscription}")
                continue
            url = str(subscription.get("url", "")).strip()
            if not url:
                continue
            normalized.append({
                "name": str(subscription.get("name", "未命名订阅")).strip() or "未命名订阅",
                "url": url,
                "user_agent": str(subscription.get("user_agent", "clash")).strip() or "clash",
            })
        return normalized

    async def query_traffic(self, subscription_name: Optional[str] = None) -> str:
        """查询流量信息"""
        if not self.subscriptions:
            return "未配置任何订阅链接，请先在插件配置中添加订阅。"

        if subscription_name:
            target_sub = None
            for sub in self.subscriptions:
                if sub.get("name") == subscription_name:
                    target_sub = sub
                    break

            if not target_sub:
                names = "、".join(sub.get("name", "未命名订阅") for sub in self.subscriptions)
                return f"未找到名为「{subscription_name}」的订阅。可用订阅：{names}"

            return await self.fetch_traffic_info(target_sub)

        results = []
        for sub in self.subscriptions:
            results.append(await self.fetch_traffic_info(sub))

        return "\n\n".join(results)

    async def fetch_traffic_info(self, subscription: Dict) -> str:
        """获取单个订阅的流量信息"""
        name = subscription.get("name", "未命名订阅")
        url = subscription.get("url", "")
        user_agent = subscription.get("user_agent", "clash")

        if not url:
            return f"{name}: 订阅链接为空"

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": user_agent}
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        return f"{name}: 请求失败 (HTTP {response.status})"

                    traffic_info = self.parse_traffic_headers(response.headers)

                    if not traffic_info:
                        return f"{name}: 订阅链接未返回流量信息"

                    return self.format_traffic_info(name, traffic_info)

        except aiohttp.ClientError as e:
            logger.error(f"请求订阅 {name} 失败: {e}")
            return f"{name}: 网络请求失败 - {str(e)}"
        except Exception as e:
            logger.error(f"查询订阅 {name} 时发生错误: {e}")
            return f"{name}: 查询失败 - {str(e)}"

    def parse_traffic_headers(self, headers) -> Optional[Dict[str, int]]:
        """
        解析响应头中的流量信息
        常见的流量信息头：
        - subscription-userinfo: upload=xxx; download=xxx; total=xxx; expire=xxx
        - Subscription-UserInfo: upload=xxx; download=xxx; total=xxx; expire=xxx
        """
        possible_headers = [
            "subscription-userinfo",
            "Subscription-UserInfo",
            "SUBSCRIPTION-USERINFO",
        ]

        userinfo = None
        for header_name in possible_headers:
            userinfo = headers.get(header_name)
            if userinfo:
                break

        if not userinfo:
            return None

        traffic_data = {}
        for item in userinfo.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                try:
                    traffic_data[key.strip()] = int(value.strip())
                except ValueError:
                    pass

        return traffic_data if traffic_data else None

    def format_traffic_info(self, name: str, traffic_info: Dict[str, int]) -> str:
        """格式化流量信息输出"""
        upload = traffic_info.get("upload", 0)
        download = traffic_info.get("download", 0)
        total = traffic_info.get("total", 0)
        expire = traffic_info.get("expire", 0)

        used = upload + download
        remaining = total - used if total > used else 0

        lines = [f"{name} 流量信息"]
        lines.append("=" * 30)

        if self.auto_convert_unit:
            lines.append(f"上传: {self.convert_bytes(upload)}")
            lines.append(f"下载: {self.convert_bytes(download)}")
            lines.append(f"已用: {self.convert_bytes(used)}")
            lines.append(f"总量: {self.convert_bytes(total)}")
            lines.append(f"剩余: {self.convert_bytes(remaining)}")
        else:
            lines.append(f"上传: {upload} bytes")
            lines.append(f"下载: {download} bytes")
            lines.append(f"已用: {used} bytes")
            lines.append(f"总量: {total} bytes")
            lines.append(f"剩余: {remaining} bytes")

        if total > 0:
            usage_percent = (used / total) * 100
            lines.append(f"使用率: {usage_percent:.2f}%")

            bar_length = 20
            filled = int(bar_length * usage_percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            lines.append(f"[{bar}]")

        if expire > 0:
            expire_date = datetime.fromtimestamp(expire)
            lines.append(f"到期时间: {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)

    def convert_bytes(self, bytes_value: int) -> str:
        """将字节转换为人类可读的格式"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
