from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Setup headless browser
options = Options()
options.add_argument("--headless")  # Remove this line if you want to see the browser
driver = webdriver.Chrome(options=options)

url = "https://pittsburgh.legistar.com/Calendar.aspx"
driver.get(url)
wait = WebDriverWait(driver, 20)

# Loop through the years 2025 to 2017
for year in range(2025, 2016, -1):
    print(f"🔄 Processing year: {year}")

    driver.save_screenshot("debug_before_wait.png")
    # time.sleep(5)
    # ==== STEP 1: Filter for Year using dropdown ====
    try:
        # Wait for the dropdown to appear
        wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_lstYears_Input")))
        year_dropdown = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_lstYears_Input")
        year_dropdown.click()
        time.sleep(1)

        # Click the year option
        year_option = driver.find_element(By.XPATH, f"//li[text()='{year}']")
        year_option.click()
        time.sleep(1)

        # Click the "Search" button
        search_button = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btnSearch")
        search_button.click()
        print(f"✅ Year {year} selected. Searching for meetings...")

        # Wait for the meeting table to appear
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.rgMasterTable")))
        print(f"✅ Meeting {year} loaded!")
        time.sleep(2)

    except Exception as e:
        print(f"⚠️ Failed to process year {year}: {e}")
        driver.save_screenshot(f"error_year_{year}.png")  # Save a screenshot for debugging
        continue  # Skip to the next year

    # ==== STEP 2: Extract meeting links from all pages ====
    meeting_links = []

    def scrape_meeting_links():
        rows = driver.find_elements(By.CSS_SELECTOR, ".rgRow, .rgAltRow")
        print(f"🕵️ Rows found on this page: {len(rows)}")
        for row in rows:
            try:
                # Look specifically for the <a> tag with ID containing 'hypMeetingDetail'
                link_element = row.find_element(By.XPATH, ".//a[contains(@id, 'hypMeetingDetail')]")
                href = link_element.get_attribute("href")
                # print(f"🔗 Found meeting detail link: {href}")
                if href and href.startswith("https") and "MeetingDetail.aspx" in href:
                    meeting_links.append(href)
                    # print(f"✅ Meeting detail link added: {href}")
            except Exception as e:
                print(f"❌ Could not find meeting detail link in row: {e}")

# print("the final meeting_links array after scraping?: ")
# count  = 0
# for link in meeting_links:
#     count += 1
#     print (count)
#     print(link)

# First page
# scrape_meeting_links()

    # Base JavaScript function for pagination
    # base_postback = "Telerik.Web.UI.Grid.NavigateToPage('ctl00_ContentPlaceHolder1_gridCalendar_ctl00', '{page_num}');"
    try:
        # Locate the pagination container
        pagination_container = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_gridCalendar_ctl00NPPHTop")

        # Find all the page links within the container
        pagination_links = pagination_container.find_elements(By.TAG_NAME, "a")

        # Loop through each pagination link
        for page_num in range(1, len(pagination_links) + 1):  # Adjust based on the number of pages
            try:
                # Re-locate the pagination container and links after each page load
                pagination_container = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_gridCalendar_ctl00NPPHTop")
                pagination_links = pagination_container.find_elements(By.TAG_NAME, "a")
                
                # Locate the specific link for the current page
                link = pagination_links[page_num - 1]  # Adjust index for zero-based indexing
                print(f"🔄 Clicking on page {page_num} link.")
                
                # Scroll the link into view (optional, in case it's not visible)
                driver.execute_script("arguments[0].scrollIntoView();", link)
                
                # Click the pagination link
                link.click()
                
                # Wait for the table to reload
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.rgMasterTable"))
                )
                time.sleep(2)  # Optional: Add a delay to ensure the page is fully loaded
                
                # Scrape meeting links on the current page
                scrape_meeting_links()
                print(f"✅ Finished scraping page {page_num}. Total links collected so far: {len(meeting_links)}")
            except Exception as e:
                print(f"⚠️ Failed to navigate to page {page_num}: {e}")
                driver.save_screenshot(f"error_page_{page_num}.png")  # Save a screenshot for debugging
    except Exception as e:
        # If the pagination container does not exist, scrape the single page
        print("ℹ️ No pagination detected. Scraping single page.")
        scrape_meeting_links()

    # Collect all postback hrefs for pagination (e.g., Page$2, Page$3, ...)
    # pagination_links = driver.find_elements(By.XPATH, "//a[contains(ctl00, '__doPostBack')]")
    # postback_hrefs = sorted(set(link.get_attribute("href") for link in pagination_links))

    # for link in pagination_links:
    #     print(link)

    # Visit each page using JS
    # for postback_js in postback_hrefs:
    #     driver.execute_script(postback_js)
    #     time.sleep(2.5)
    #     scrape_meeting_links()


    # Loop through pages using the postback command in the href
    # for link in pagination_links:
    #     postback_href = link.get_attribute("href")  # e.g., javascript:__doPostBack('ctl00$ContentPlaceHolder1$rgCalendar','Page$2')
    #     if postback_href and postback_href.startswith("javascript:__doPostBack"):
    #         try:
    #             print(f"🔄 Navigating with: {postback_href}")
    #             driver.execute_script(postback_href)
    #             WebDriverWait(driver, 10).until(
    #                 EC.presence_of_element_located((By.CSS_SELECTOR, "table.rgMasterTable"))
    #             )
    #             time.sleep(2)
    #             scrape_meeting_links()
    #         except Exception as e:
    #             print(f"⚠️ Failed to navigate with postback: {e}")

    print(f"✅ Total meetings found: {len(meeting_links)}")
    print(f"✅ Total meeting links collected: {len(meeting_links)}")

    # ==== STEP 3: Scrape each meeting's resolutions ====
    data = []
    count = 0
    for link in meeting_links:
        count += 1
        print(f"🔗 Visiting meeting link: {count}")
        driver.get(link)
        # driver.save_screenshot("debug_after_get_link.png")
        # time.sleep(2)

        try:
            meeting_type = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_hypName").text
            meeting_date = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_lblDate").text
        except:
            continue

        # print(meeting_type, meeting_date)

        number_of_rows = len(driver.find_elements(By.TAG_NAME, "tr"))
        # print("number_of_rows: ", number_of_rows)
        for i in range(number_of_rows):
            # print(f"ctl00_ContentPlaceHolder1_gridMain_ctl00__{i}")
            rows = driver.find_elements(By.ID, f"ctl00_ContentPlaceHolder1_gridMain_ctl00__{i}")
            # print("rows: ", rows)
            for row in rows:
                # print ("before cells")
                cells = row.find_elements(By.TAG_NAME, "td")
                # print ("after cells")
                # print(cells)
                if len(cells) >= 4:
                    file_no = cells[0].text.strip()
                    ver = cells[1].text.strip()
                    type = cells[3].text.strip()
                    title = cells[4].text.strip()
                    action = cells[5].text.strip()
                    result = cells[6].text.strip()
                
                    # print({
                    #     "Meeting Date": meeting_date,
                    #     "Meeting Type": meeting_type,
                    #     "File No": file_no,
                    #     "Ver": ver,
                    #     "Type": type,
                    #     "Title": title,
                    #     "Action": action,
                    #     "Result": result,
                    #     "Link": link
                    # })

                    data.append({
                        "Meeting Date": meeting_date,
                        "Meeting Type": meeting_type,
                        "File No": file_no,
                        "Ver": ver,
                        "Type": type,
                        "Title": title,
                        "Action": action,
                        "Result": result,
                        "Link": link
                    })

    # ==== STEP 4: Export to Excel ====
    df = pd.DataFrame(data)
    df.to_excel(f"pittsburgh_meetings_{year}.xlsx", index=False)
    print(f"✅ Exported to pittsburgh_meetings_{year}.xlsx")
   
    # Navigate back to the main calendar page
    try:
        # Locate and click the "Calendar" button (or another button that navigates back)
        calendar_button = driver.find_element(By.CSS_SELECTOR, "a.rtsSelected")  # Replace with the correct ID or locator
        calendar_button.click()
        print("🔄 Navigated back to the main calendar page.")
        
        # Wait for the calendar page to reload
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_lstYears_Input"))
        )
        time.sleep(2)  # Optional: Add a delay to ensure the page is fully loaded
    except Exception as e:
        print(f"⚠️ Failed to navigate back to the main calendar page: {e}")
        driver.save_screenshot("error_navigate_back.png")

print("✅ All years processed successfully!")
driver.quit()
