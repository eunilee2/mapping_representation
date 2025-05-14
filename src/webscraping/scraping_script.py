from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Set up headless Chrome
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)

url = "https://pittsburgh.legistar.com/Calendar.aspx"
driver.get(url)

# Click to filter for 2024 if needed (we assume already filtered here)
wait = WebDriverWait(driver, 10)

# Store all meeting links
meeting_links = []

wait = WebDriverWait(driver, 10)

while True:
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.rgMasterTable")))

    rows = driver.find_elements(By.CSS_SELECTOR, ".rgRow")

    for row in rows:
        print(row.text)  # See what data is visible
        try:
            link_element = row.find_element(By.TAG_NAME, "a")
            href = link_element.get_attribute("href")
            if href and href.startswith("http") and "Calendar.aspx" in href:
                meeting_links.append(href)
        except Exception as e:
            print("Skipping invalid row:", e)
            continue

    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, ".rgPageNext")
        if "disabled" in next_btn.get_attribute("class"):
            break
        next_btn.click()
        time.sleep(2.5)
    except Exception as e:
        print("Pagination end or error:", e)
        break

# while True:
#     # Wait until table is present
#     wait.until(EC.presence_of_element_located((By.CLASS_NAME, "rgMasterTable")))
#     rows = driver.find_elements(By.CSS_SELECTOR, ".rgRow")

#     for row in rows:
#         try:
#             # Only get the first link (meeting detail link)
#             detail_link = row.find_element(By.TAG_NAME, "a").get_attribute("href")
#             if detail_link and detail_link.startswith("http"):
#                 meeting_links.append(detail_link)
#         except Exception as e:
#             print("Skipping a row due to missing link:", e)
#             continue

#     try:
#         next_btn = driver.find_element(By.CSS_SELECTOR, ".rgPageNext")
#         if "disabled" in next_btn.get_attribute("class"):
#             break
#         next_btn.click()
#         time.sleep(2)
#     except:
#         break

print(f"Found {len(meeting_links)} meetings.")

# Now go to each meeting detail and extract info
data = []

for link in meeting_links:
    if not link or not link.startswith("http"):
        print(f"Skipping invalid link: {link}")
        continue
    driver.get(link)
    time.sleep(2)

    # Meeting info
    try:
        meeting_type = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_lblMeetingName").text
        meeting_date = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_lblMeetingDate").text
    except:
        continue

    # Agenda table
    rows = driver.find_elements(By.CSS_SELECTOR, ".ctl00_ContentPlaceHolder1_gridMain_ctl00__ tbody tr")

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        print(cells)
        if len(cells) >= 4:
            resolution_id = cells[0].text.strip()
            title = cells[1].text.strip()
            committee = cells[2].text.strip()
            result = cells[3].text.strip()

            data.append({
                "Meeting Date": meeting_date,
                "Meeting Type": meeting_type,
                "Resolution ID": resolution_id,
                "Title": title,
                "Committee": committee,
                "Result": result,
                "Link": link
            })

# Export to Excel
df = pd.DataFrame(data)
df.to_excel("pittsburgh_meetings_2024.xlsx", index=False)
print("Exported to pittsburgh_meetings_2024.xlsx")

driver.quit()
