import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from openai import OpenAI

def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    return webdriver.Chrome(service=service, options=options)

def login_to_semrush(driver):
    driver.get("https://www.semrush.com/login/")
    time.sleep(3)  
    
    try:
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        email_input.clear()
        email_input.send_keys("SEMRUSH_EMAIL")
        
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        password_input.clear()
        password_input.send_keys("SEMRUSH_PASSWORD")
        
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        submit_button.click()
        time.sleep(5)  
        
    except Exception as e:
        print(f"Login failed: {e}")
        driver.quit()
        raise

def navigate_to_organic_research(driver):
    try:
        driver.get("https://www.semrush.com/analytics/organic/overview/")
        time.sleep(2.5)  
    except Exception as e:
        print(f"Navigation failed: {e}")
        driver.quit()
        raise

def search_domain(driver, domain):
    try:
        search_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter domain, subdomain or URL']"))
        )
        search_input.clear()
        time.sleep(0.5)  
        search_input.send_keys(domain)
        time.sleep(0.5)  
        search_input.send_keys(Keys.RETURN)
        time.sleep(3.5)  
        
        positions_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Positions']"))
        )
        positions_tab.click()
        time.sleep(1.5)  
        
    except Exception as e:
        print(f"Domain search failed: {e}")
        driver.quit()
        raise

def apply_filters(driver):
    try:
        kd_filter = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-ui-name='FilterTrigger.Text'][placeholder='KD']"))
        )
        kd_filter.click()
        time.sleep(1.5)  
        
        from_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-ui-name='InputNumber.Value'][placeholder='From']"))
        )
        driver.execute_script("arguments[0].value = '1';", from_input)
        from_input.send_keys(Keys.TAB)
        time.sleep(1)  
        
        to_input = driver.find_element(By.CSS_SELECTOR, "input[data-ui-name='InputNumber.Value'][placeholder='To']")
        driver.execute_script("arguments[0].value = '50';", to_input)
        to_input.send_keys(Keys.TAB)
        time.sleep(1)  
        
        apply_button_kd = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Apply']]"))
        )
        apply_button_kd.click()
        time.sleep(1.5)  
        
        intent_filter = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-ui-name='FilterTrigger.Text'][placeholder='Intent']"))
        )
        intent_filter.click()
        time.sleep(1) 
        
        info_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[value='informational']"))
        )
        info_option.click()
        
        apply_button_intent = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Apply']]"))
        )
        apply_button_intent.click()
        time.sleep(2.5) 
        
    except Exception as e:
        print(f"Filter application failed: {e}")
        driver.quit()
        raise

def scrape_keywords(driver):
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//table"))
        )
        time.sleep(5)
        
        keywords_data = []
        
        for i in range(15):
            try:
                driver.execute_script(f"window.scrollBy(0, {i*30});")
                time.sleep(1)

                keyword = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"(//span[@class='___SText_pr68d-red-team'])[{i+1}]"))
                ).text.strip()

                position = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"(//div[@data-at='display-position'])[{i+1}]"))
                ).text.strip()

                volume = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"(//span[@data-at='display-number'])[{i+1}]"))
                ).text.strip()

                kd = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"(//span[@data-at='kd-value'])[{i+1}]"))
                ).text.strip()
                
                keywords_data.append({
                    'Keyword': keyword,
                    'Position': position,
                    'Volume': volume,
                    'KD%': kd
                })
                
                if (i + 1) % 10 == 0:
                    print(f"Scraped {i + 1} keywords...")
                    # Additional scroll to ensure next batch is loaded
                    driver.execute_script("window.scrollBy(0, 300);")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"Error scraping row {i+1}: {e}")
                # Try scrolling more on error
                driver.execute_script("window.scrollBy(0, 100);")
                time.sleep(2)
                continue
        
        return keywords_data
        
    except Exception as e:
        print(f"Scraping failed: {e}")
        raise

def analyze_with_gpt(keywords_data):
    client = OpenAI(api_key="your_openai_api_key_here")
    
    data_str = "\n".join([
        f"Keyword: {item['Keyword']}, Position: {item['Position']}, Volume: {item['Volume']}, KD%: {item['KD%']}"
        for item in keywords_data
    ])
    
    system_prompt = """You are an AI SEO expert specializing in keyword analysis and organic search optimization. Your analysis should be data-driven, actionable, and focused on delivering measurable improvements in search rankings and traffic."""

    user_prompt = f"""Analyze this SEMrush keyword data and provide strategic SEO recommendations:

{data_str}

Follow these specific steps in your analysis:

1. Process the keyword data to identify:
   - High-volume, low-competition keywords not currently in top positions
   - Keywords just outside first page (positions 11-20) that could reach top 10
   - Well-ranking keywords with potential for position improvements

2. Create a prioritized keyword list based on:
   - Search volume (traffic potential)
   - Keyword difficulty (ranking feasibility)
   - Current position (focus on page 2-3 for quick wins)

3. Provide specific SEO optimization recommendations:
   - Current keyword performance analysis
   - Priority target keywords and optimization steps
   - Projected traffic gains from implementing recommendations

Format your response in very concise, clear, actionable format that summarize the key opportunities and specific steps to improve rankings."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        print("\nSEO Analysis Report:")
        print("-------------------")
        print(analysis)
        return analysis
        
    except Exception as e:
        print(f"GPT analysis failed: {e}")
        raise

def main():
    driver = None
    try:
        driver = setup_driver()
        domain = input("Enter the domain to analyze: ")
        
        login_to_semrush(driver)
        navigate_to_organic_research(driver)
        search_domain(driver, domain)
        apply_filters(driver)
        
        print("\nStarting keyword scraping...")
        keywords = scrape_keywords(driver)
        print(f"\nSuccessfully scraped {len(keywords)} keywords")
        
        print("\nAnalyzing keywords with GPT...")
        analysis = analyze_with_gpt(keywords)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()