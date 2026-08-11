from __future__ import annotations

import json
from datetime import datetime
from ipaddress import ip_address
from typing import Any, Dict, List, Mapping, Optional
from urllib.parse import urlparse


def validate_subscription_url(url: Any) -> Optional[str]:
    """Validate a subscription URL and reject obvious local-network targets."""
    normalized_url = str(url or "").strip()
    if not normalized_url or len(normalized_url) > 2048:
        return None

    try:
        parsed_url = urlparse(normalized_url)
        hostname = (parsed_url.hostname or "").lower().rstrip(".")
    except ValueError:
        return None

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return None
    if not hostname or hostname in {"localhost", "localhost.localdomain"}:
        return None
    if hostname.endswith(".local") or hostname.endswith(".localhost"):
        return None

    try:
        parsed_ip = ip_address(hostname)
    except ValueError:
        parsed_ip = None

    if parsed_ip is not None and not parsed_ip.is_global:
        return None

    return normalized_url


def is_traffic_help_request(argument: Any) -> bool:
    """Return whether a traffic command argument requests help."""
    return str(argument or "").strip().lower() in {"help", "-h", "--help", "\u5e2e\u52a9"}


def format_traffic_help() -> str:
    """Return the user-facing command help text."""
    return (
        "VPN \u6d41\u91cf\u67e5\u8be2\n"
        "/\u6d41\u91cf  \u67e5\u8be2\u81ea\u5df1\u7684\u5168\u90e8\u8ba2\u9605\n"
        "/\u6d41\u91cf <\u8ba2\u9605\u540d\u79f0>  \u67e5\u8be2\u6307\u5b9a\u8ba2\u9605\n"
        "/\u6dfb\u52a0\u8ba2\u9605 <\u540d\u79f0> <\u8ba2\u9605\u94fe\u63a5> [User-Agent]\n"
        "/\u6d41\u91cf help  \u663e\u793a\u5e2e\u52a9"
    )


def normalize_subscriptions(subscriptions: Any) -> List[Dict[str, str]]:
    """将 AstrBot 配置中的订阅数据标准化为统一结构。"""
    if isinstance(subscriptions, str):
        try:
            subscriptions = json.loads(subscriptions)
        except json.JSONDecodeError:
            return []

    if isinstance(subscriptions, dict):
        subscriptions = [subscriptions]

    if not isinstance(subscriptions, list):
        return []

    normalized: List[Dict[str, str]] = []
    for subscription in subscriptions:
        if not isinstance(subscription, dict):
            continue

        url = str(subscription.get("url", "")).strip()
        if not url:
            continue

        normalized.append(
            {
                "__template_key": str(subscription.get("__template_key", "subscription")).strip()
                or "subscription",
                "name": str(subscription.get("name", "未命名订阅")).strip()
                or "未命名订阅",
                "owner_id": str(subscription.get("owner_id", "")).strip(),
                "url": url,
                "user_agent": str(subscription.get("user_agent", "clash")).strip()
                or "clash",
            }
        )

    return normalized


def get_owned_subscriptions(
    subscriptions: List[Dict[str, str]], owner_id: str
) -> List[Dict[str, str]]:
    """仅返回与当前发送者 ID 精确匹配的订阅。"""
    normalized_owner_id = str(owner_id).strip()
    if not normalized_owner_id:
        return []

    return [
        subscription
        for subscription in subscriptions
        if subscription.get("owner_id", "").strip() == normalized_owner_id
    ]


def parse_traffic_headers(headers: Mapping[str, str]) -> Optional[Dict[str, int]]:
    """解析 subscription-userinfo 响应头。"""
    userinfo = None
    for key, value in headers.items():
        if str(key).lower() == "subscription-userinfo":
            userinfo = value
            break

    if not userinfo:
        return None

    traffic_data: Dict[str, int] = {}
    for item in userinfo.split(";"):
        item = item.strip()
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        try:
            traffic_data[key.strip().lower()] = int(value.strip())
        except ValueError:
            continue

    return traffic_data or None


def convert_bytes(bytes_value: int) -> str:
    """将字节转换为适合阅读的单位。"""
    value = float(max(bytes_value, 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} PB"


def format_traffic_info(
    name: str,
    traffic_info: Mapping[str, int],
    auto_convert_unit: bool = True,
) -> str:
    """生成适合手机端显示的紧凑流量信息。"""
    upload = max(int(traffic_info.get("upload", 0)), 0)
    download = max(int(traffic_info.get("download", 0)), 0)
    total = max(int(traffic_info.get("total", 0)), 0)
    expire = max(int(traffic_info.get("expire", 0)), 0)

    used = upload + download
    remaining = max(total - used, 0)

    if auto_convert_unit:
        upload_text = convert_bytes(upload)
        download_text = convert_bytes(download)
        used_text = convert_bytes(used)
        total_text = convert_bytes(total)
        remaining_text = convert_bytes(remaining)
    else:
        upload_text = f"{upload} B"
        download_text = f"{download} B"
        used_text = f"{used} B"
        total_text = f"{total} B"
        remaining_text = f"{remaining} B"

    lines = [
        name,
        f"上传 {upload_text}  下载 {download_text}",
        f"已用 {used_text} / {total_text}",
        f"剩余 {remaining_text}",
    ]

    if expire > 0:
        expire_date = datetime.fromtimestamp(expire)
        lines.append(f"到期 {expire_date:%Y-%m-%d %H:%M:%S}")

    return "\n".join(lines)


