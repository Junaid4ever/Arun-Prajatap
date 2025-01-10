import asyncio
from playwright.async_api import async_playwright
import indian_names
import requests

# Read password from GitHub
def read_password_from_github(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip()
    else:
        raise Exception("Failed to read password from GitHub")

# Verify password
def verify_password(input_password, github_password_url):
    github_password = read_password_from_github(github_password_url)
    return input_password == github_password

# Start function (hidden in GitHub)
async def start(wait_time, meetingcode, passcode):
    try:
        user = indian_names.get_full_name()
        print(f"{user} joined.")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(f'http://app.zoom.us/wc/join/{meetingcode}', timeout=200000)

            # Grant microphone permissions
            for _ in range(5):
                await page.evaluate('() => { navigator.mediaDevices.getUserMedia({ audio: true }); }')

            try:
                await page.click('//button[@id="onetrust-accept-btn-handler"]', timeout=5000)
            except Exception:
                pass

            try:
                await page.click('//button[@id="wc_agree1"]', timeout=5000)
            except Exception:
                pass

            try:
                await page.wait_for_selector('input[type="text"]', timeout=200000)
                await page.fill('input[type="text"]', user)
                
                password_field_exists = await page.query_selector('input[type="password"]')
                if password_field_exists:
                    await page.fill('input[type="password"]', passcode)
                    join_button = await page.wait_for_selector('button.preview-join-button', timeout=200000)
                    await join_button.click()
                else:
                    join_button = await page.wait_for_selector('button.preview-join-button', timeout=200000)
                    await join_button.click()
            except Exception:
                pass

            try:
                await page.wait_for_selector('button.join-audio-by-voip__join-btn', timeout=300000)
                mic_button_locator = await page.query_selector('button[class*="join-audio-by-voip__join-btn"]')
                await asyncio.sleep(5)
                await mic_button_locator.evaluate_handle('node => node.click()')
                print(f"{user} mic enabled.")
            except Exception as e:
                print(f"{user} mic error: {e}")

            print(f"{user} sleeping for {wait_time} seconds...")
            while wait_time > 0:
                await asyncio.sleep(1)
                wait_time -= 1
            print(f"{user} ended session!")

        await context.close()
        await browser.close()
    except Exception as e:
        print(f"Error: {e}")
