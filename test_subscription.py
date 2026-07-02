import aiohttp
import asyncio

async def test_subscription():
    url = "https://kipfelsuki.com/api/ef975ccdd497f469da209e1b81f2b06d"
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "clash"}
            async with session.get(url, headers=headers, timeout=10) as response:
                print(f"状态码: {response.status}")
                print(f"\n响应头:")
                print("-" * 50)
                
                # 打印所有响应头
                for key, value in response.headers.items():
                    print(f"{key}: {value}")
                
                # 检查流量信息
                userinfo = response.headers.get("subscription-userinfo") or \
                          response.headers.get("Subscription-UserInfo")
                
                if userinfo:
                    print(f"\n✅ 找到流量信息:")
                    print(f"   {userinfo}")
                    
                    # 解析流量数据
                    traffic_data = {}
                    for item in userinfo.split(";"):
                        item = item.strip()
                        if "=" in item:
                            key, value = item.split("=", 1)
                            try:
                                traffic_data[key.strip()] = int(value.strip())
                            except ValueError:
                                pass
                    
                    if traffic_data:
                        print(f"\n解析结果:")
                        for key, value in traffic_data.items():
                            # 转换为 GB
                            gb_value = value / (1024 ** 3)
                            print(f"   {key}: {value} bytes ({gb_value:.2f} GB)")
                else:
                    print(f"\n❌ 未找到流量信息 (subscription-userinfo 响应头)")
    
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_subscription())
