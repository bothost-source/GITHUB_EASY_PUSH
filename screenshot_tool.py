"""
TARRIFIC HOST BOT - Screenshot Tool
Capture screenshots of deployed sites using Playwright
"""
import os
import asyncio
from playwright.async_api import async_playwright

class ScreenshotTool:
    def __init__(self, output_dir="screenshots"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def capture_screenshot(self, url, filename=None, full_page=False, 
                                 width=1920, height=1080, wait_time=3000):
        """
        Capture screenshot of a webpage

        url: URL to screenshot
        filename: Output filename (auto-generated if None)
        full_page: Capture full scrollable page
        width: Viewport width
        height: Viewport height
        wait_time: Milliseconds to wait after page load
        """
        if not filename:
            # Generate filename from URL
            safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_')
            filename = f"{safe_url}_{asyncio.get_event_loop().time()}.png"

        output_path = os.path.join(self.output_dir, filename)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': width, 'height': height}
                )
                page = await context.new_page()

                # Navigate to URL
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)

                # Wait for network idle and extra time for dynamic content
                await page.wait_for_load_state('networkidle', timeout=10000)
                await asyncio.sleep(wait_time / 1000)  # Convert ms to seconds

                # Take screenshot
                await page.screenshot(
                    path=output_path,
                    full_page=full_page,
                    type='png'
                )

                await browser.close()

                return {
                    'success': True,
                    'path': output_path,
                    'filename': filename,
                    'url': url,
                    'size': os.path.getsize(output_path)
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    async def capture_github_repo(self, repo_url, filename=None):
        """
        Capture screenshot of GitHub repository page

        repo_url: GitHub repo URL
        filename: Output filename
        """
        if not filename:
            parts = repo_url.replace('https://github.com/', '').split('/')
            if len(parts) >= 2:
                filename = f"github_{parts[0]}_{parts[1]}.png"
            else:
                filename = f"github_{repo_url.replace('/', '_')}.png"

        return await self.capture_screenshot(
            url=repo_url,
            filename=filename,
            full_page=True,  # Full page for repo view
            width=1920,
            height=1080,
            wait_time=5000  # Extra wait for GitHub dynamic content
        )

    async def capture_deployment_preview(self, deploy_url, filename=None):
        """
        Capture screenshot of deployed site

        deploy_url: Deployment URL (GitHub Pages or Vercel)
        filename: Output filename
        """
        if not filename:
            safe_url = deploy_url.replace('https://', '').replace('http://', '').replace('/', '_')
            filename = f"deploy_{safe_url}.png"

        return await self.capture_screenshot(
            url=deploy_url,
            filename=filename,
            full_page=True,
            width=1920,
            height=1080,
            wait_time=5000  # Wait for site to fully render
        )

    def get_screenshot_path(self, filename):
        """Get full path for a screenshot file"""
        return os.path.join(self.output_dir, filename)

    def list_screenshots(self):
        """List all captured screenshots"""
        screenshots = []
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f.endswith('.png'):
                    path = os.path.join(self.output_dir, f)
                    screenshots.append({
                        'filename': f,
                        'path': path,
                        'size': os.path.getsize(path),
                        'created': os.path.getctime(path)
                    })
        return sorted(screenshots, key=lambda x: x['created'], reverse=True)
