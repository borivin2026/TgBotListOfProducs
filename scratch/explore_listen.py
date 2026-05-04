from deepgram import DeepgramClient
import asyncio

async def test():
    client = DeepgramClient(api_key="fake")
    print(f"Listen dir: {dir(client.listen)}")
    try:
        print(f"Rest dir: {dir(client.listen.rest)}")
    except:
        print("No rest")
    try:
        print(f"Prerecorded dir: {dir(client.listen.prerecorded)}")
    except:
        print("No prerecorded")

asyncio.run(test())
