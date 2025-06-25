import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Launch a Playwright server to expose a WSS endpoint
        # Listen on 0.0.0.0 to be accessible externally
        browser_server = await p.chromium.launch_server(headless=False, port=8000, host='0.0.0.0')
        print(f"Playwright browser server running at: {browser_server.ws_endpoint}")
        # Keep the server alive indefinitely
        await browser_server.wait_until_closed()

if __name__ == "__main__":
    asyncio.run(main()) 