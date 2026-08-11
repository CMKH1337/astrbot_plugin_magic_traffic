from __future__ import annotations

import asyncio
from typing import Dict, Optional

import aiohttp

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

try:
    from .traffic_utils import (
        format_traffic_help,
        format_traffic_info,
        get_owned_subscriptions,
        is_traffic_help_request,
        normalize_subscriptions,
        parse_traffic_headers,
        validate_subscription_url,
    )
except ImportError:
    from traffic_utils import (
        format_traffic_help,
        format_traffic_info,
        get_owned_subscriptions,
        is_traffic_help_request,
        normalize_subscriptions,
        parse_traffic_headers,
        validate_subscription_url,
    )


@register(
    "astrbot_plugin_vpn_traffic",
    "CMKH",
    "按拥有者查询 Clash 或 V2Ray 订阅流量",
    "v1.2.2",
)
class VPNTrafficPlugin(Star):
    """仅允许订阅拥有者查询自己的 Clash 或 V2Ray 订阅流量。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.subscriptions = normalize_subscriptions(config.get("subscriptions", []))
        self.auto_convert_unit = bool(config.get("auto_convert_unit", True))
        self.allow_group_add = bool(config.get("allow_group_add", False))
        self.max_user_subscriptions = max(int(config.get("max_user_subscriptions", 10) or 10), 1)
        self._subscription_lock = asyncio.Lock()
        logger.info(
            f"VPN 流量查询插件已加载，已配置 {len(self.subscriptions)} 个订阅"
        )

    @filter.command("\u6dfb\u52a0\u8ba2\u9605", alias={"add_subscription", "add-subscription"})
    async def add_subscription_command(
        self,
        event: AstrMessageEvent,
        subscription_name: str = "",
        url: str = "",
        user_agent: str = "clash",
    ):
        """Add a subscription owned by the current sender."""
        group_id = str(event.get_group_id() or "").strip()
        if group_id and not self.allow_group_add:
            yield event.plain_result("\u51fa\u4e8e\u5b89\u5168\u8003\u8651\uff0c\u6dfb\u52a0\u8ba2\u9605\u8bf7\u4f7f\u7528\u79c1\u804a\u3002")
            return

        owner_id = str(event.get_sender_id()).strip()
        name = str(subscription_name or "").strip()
        normalized_url = validate_subscription_url(url)
        normalized_user_agent = str(user_agent or "clash").strip() or "clash"

        if not name or not normalized_url:
            yield event.plain_result(
                "\u7528\u6cd5\uff1a\u6dfb\u52a0\u8ba2\u9605 <\u540d\u79f0> <\u8ba2\u9605\u94fe\u63a5> [User-Agent]\n"
                "\u793a\u4f8b\uff1a\u6dfb\u52a0\u8ba2\u9605 \u4e3b\u8ba2\u9605 https://example.com/sub clash"
            )
            return
        if len(name) > 64:
            yield event.plain_result("\u8ba2\u9605\u540d\u79f0\u4e0d\u80fd\u8d85\u8fc7 64 \u4e2a\u5b57\u7b26\u3002")
            return
        if len(normalized_user_agent) > 256:
            yield event.plain_result("User-Agent \u4e0d\u80fd\u8d85\u8fc7 256 \u4e2a\u5b57\u7b26\u3002")
            return

        subscription = {
            "__template_key": "subscription",
            "name": name,
            "owner_id": owner_id,
            "url": normalized_url,
            "user_agent": normalized_user_agent,
        }

        async with self._subscription_lock:
            owned_subscriptions = get_owned_subscriptions(self.subscriptions, owner_id)
            if len(owned_subscriptions) >= self.max_user_subscriptions:
                yield event.plain_result(
                    f"\u6bcf\u4e2a\u7528\u6237\u6700\u591a\u4fdd\u5b58 {self.max_user_subscriptions} \u4e2a\u8ba2\u9605\u3002"
                )
                return

            if any(item.get("name") == name for item in owned_subscriptions):
                yield event.plain_result(f"\u4f60\u5df2\u7ecf\u6dfb\u52a0\u8fc7\u540d\u4e3a\u201c{name}\u201d\u7684\u8ba2\u9605\u3002")
                return

            self.subscriptions.append(subscription)
            self.config["subscriptions"] = self.subscriptions
            try:
                self.config.save_config()
            except Exception as error:
                self.subscriptions.pop()
                logger.error(
                    "Failed to save a user-added subscription, error type: %s",
                    type(error).__name__,
                )
                yield event.plain_result("\u8ba2\u9605\u4fdd\u5b58\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002")
                return

        yield event.plain_result(
            f"\u8ba2\u9605\u201c{name}\u201d\u5df2\u6dfb\u52a0\u3002\n"
            "\u73b0\u5728\u53ef\u4ee5\u53d1\u9001\uff1a\u6d41\u91cf \u6216 \u6d41\u91cf <\u540d\u79f0> \u6765\u67e5\u8be2\u3002"
        )

    @filter.command("流量")
    async def query_traffic_command(
        self,
        event: AstrMessageEvent,
        subscription_name: Optional[str] = None,
    ):
        """查询当前账号拥有的订阅流量。"""
        if is_traffic_help_request(subscription_name):
            yield event.plain_result(format_traffic_help())
            return

        sender_id = str(event.get_sender_id()).strip()
        result = await self.query_traffic(sender_id, subscription_name)
        yield event.plain_result(result)

    async def query_traffic(
        self,
        owner_id: str,
        subscription_name: Optional[str] = None,
    ) -> str:
        """查询指定拥有者可见的流量信息。"""
        if not self.subscriptions:
            return "管理员尚未配置订阅。"

        owned_subscriptions = get_owned_subscriptions(self.subscriptions, owner_id)
        if not owned_subscriptions:
            return f"当前账号未绑定订阅。\n你的用户 ID：{owner_id}"

        if subscription_name:
            target = next(
                (
                    subscription
                    for subscription in owned_subscriptions
                    if subscription.get("name") == subscription_name
                ),
                None,
            )
            if target is None:
                return "未找到属于你的同名订阅。"
            owned_subscriptions = [target]

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            results = [
                await self.fetch_traffic_info(session, subscription)
                for subscription in owned_subscriptions
            ]

        return "\n\n".join(results)

    async def fetch_traffic_info(
        self,
        session: aiohttp.ClientSession,
        subscription: Dict[str, str],
    ) -> str:
        """获取单项订阅的流量信息。"""
        name = subscription.get("name", "未命名订阅")
        url = subscription.get("url", "")
        user_agent = subscription.get("user_agent", "clash")

        safe_url = validate_subscription_url(url)
        if not safe_url:
            return "{}\uff1a\u8ba2\u9605\u5730\u5740\u65e0\u6548\u6216\u4e0d\u5141\u8bb8\u8bbf\u95ee".format(name)

        try:
            headers = {"User-Agent": user_agent}
            async with session.get(safe_url, headers=headers) as response:
                if response.status != 200:
                    return f"{name}：请求失败，HTTP {response.status}"

                traffic_info = parse_traffic_headers(response.headers)
                if not traffic_info:
                    return f"{name}：订阅未返回流量信息"

                return format_traffic_info(
                    name,
                    traffic_info,
                    auto_convert_unit=self.auto_convert_unit,
                )
        except aiohttp.ClientError as error:
            logger.error(f"请求订阅 {name} 失败，错误类型：{type(error).__name__}")
            return f"{name}：网络请求失败"
        except Exception as error:
            logger.error(f"查询订阅 {name} 失败，错误类型：{type(error).__name__}")
            return f"{name}：查询失败"

