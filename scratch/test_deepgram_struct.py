from deepgram import DeepgramClient
import asyncio

async def test():
    client = DeepgramClient("fake-key")
    print(f"Listen: {client.listen}")
    # Check if we can reach v1 media
    try:
        print(f"Listen v1: {client.listen.v('1')}")
        print(f"Listen v1 media: {client.listen.v('1').media}")
        print(f"Transcribe file: {client.listen.v('1').media.transcribe_file}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
