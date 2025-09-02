from playwright.async_api import (
    Page, 
    Playwright, 
    Browser, 
    async_playwright, 
    BrowserContext
)
from playwright_stealth import Stealth
from fake_useragent import UserAgent

class Browser:
    """
    Browser class for managing browser instances.

    Attributes:
        user_agent (str): The user agent to use for the browser
        random_user_agent (bool): Whether to use a random user agent
        playwright (Playwright): The Playwright instance
        browser_instance (Browser): The browser instance
        browser_context (BrowserContext): The browser context
        page (Page): The page instance
    """

    def __init__(
        self, 
        user_agent: str = None,
        random_user_agent: bool = False,
        ws_endpoint: str = None,
        slow_mo: float = None
    ) -> None:
        self.user_agent = user_agent
        self.random_user_agent = random_user_agent
        self.playwright: Playwright = None
        self.browser_instance: Browser = None
        self.browser_context: BrowserContext = None
        self.page: Page = None
        self.ws_endpoint = ws_endpoint
        self.slow_mo = slow_mo

        if self.random_user_agent:
            self.user_agent = UserAgent().chrome

    async def __aenter__(self) -> Browser:
        """
        Initializes the browser when using the `async with` statement.
        """
        return await self.init_browser()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Closes the browser when the context manager is to be exited.
        """
        await self.close_browser()
    
    async def init_browser(self) -> Browser:
        self.playwright = await async_playwright().start()

        if self.ws_endpoint:
            browser_instance = await self.playwright.chromium.connect(
                self.ws_endpoint, 
                timeout = 1230000, 
                slow_mo = self.slow_mo
            )
    
            self.browser_context = await browser_instance.new_context(
                user_agent = self.user_agent
            )

            stealth = Stealth()
            await stealth.apply_stealth_async(self.browser_context)
            self.page = await self.browser_context.new_page()
            await self.page.set_viewport_size({'width': 1920, 'height': 1080})
            await self.page.goto('about:blank') # default page to be opened

        return self

    async def close_browser(self) -> None:
        """
        Closes the browser instance and releases resources.
        """

        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
                self.page = None

            if self.browser_context:
                await self.browser_context.close()
                self.browser_context = None

            if self.browser_instance:
                await self.browser_instance.close_browser()
                self.browser_instance = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print(f"Error closing browser: {e}")