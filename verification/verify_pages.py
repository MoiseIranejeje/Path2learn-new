from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Visit Home Page
        page.goto("http://127.0.0.1:5000/")
        page.screenshot(path="verification/home_page.png", full_page=True)
        print("Captured Home Page")

        # 2. Visit Smart Search
        page.goto("http://127.0.0.1:5000/smart-search")
        page.screenshot(path="verification/smart_search.png", full_page=True)
        print("Captured Smart Search")

        # 3. Visit Team Page
        page.goto("http://127.0.0.1:5000/team")
        page.screenshot(path="verification/team_page.png", full_page=True)
        print("Captured Team Page")

        browser.close()

if __name__ == "__main__":
    verify_frontend()
