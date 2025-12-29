import asyncio
import ssl
import aiomqtt

async def test_mqtt_connection():
    try:
        print("尝试连接到MQTT服务器...")
        async with aiomqtt.Client(
            hostname="localhost",
            port=1883,
            username="qxy1",
            password="5686670",
            identifier="test_client",
            keepalive=60
        ) as client:
            print("连接成功！")
            # 发布一条消息以确认完全连接
            await client.publish("test/connection", "Hello from test")
            print("消息发布成功！")
            return True
    except Exception as e:
        print(f"连接失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mqtt_connection())
    if success:
        print("MQTT连接测试成功")
    else:
        print("MQTT连接测试失败")