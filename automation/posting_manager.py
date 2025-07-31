import threading
import time
import random
from PyQt5.QtCore import QObject, pyqtSignal
from playwright.sync_api import sync_playwright
import json
import os

class PostingManager(QObject):
    log_message = pyqtSignal(str, str)
    account_status_changed = pyqtSignal(int, str, str) 
    posting_completed = pyqtSignal(int) 
    batch_started = pyqtSignal(list) 
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.is_running = False
        self.is_paused = False
        self.current_thread = None
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
    
    def start_posting(self, group_id, batch_size, min_price, max_price):
        """Start the posting process"""
        if self.is_running:
            return
        
        self.is_running = True
        self.is_paused = False
        
        self.current_thread = threading.Thread(
            target=self._posting_worker,
            args=(group_id, batch_size, min_price, max_price)
        )
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def pause_posting(self):
        """Pause the posting process"""
        self.is_paused = True
    
    def continue_posting(self):
        """Continue the posting process"""
        self.is_paused = False
    
    def stop_posting(self):
        """Stop the posting process"""
        self.is_running = False
        self.is_paused = False
    
    def _posting_worker(self, group_id, batch_size, min_price, max_price):
        """Worker thread for posting process"""
        try:
            self.log_message.emit(f"Starting posting process for group {group_id}", "INFO")
            
            # Get accounts and products
            accounts = self.db_manager.get_accounts_by_group(group_id)
            products = self.db_manager.get_products_by_group(group_id)
            
            # Filter products by price range
            filtered_products = [
                p for p in products 
                if min_price <= p['price'] <= max_price
            ]
            
            if not accounts:
                self.log_message.emit("No accounts found in group", "ERROR")
                return
            
            if not filtered_products:
                self.log_message.emit("No products found in price range", "ERROR")
                return
            
            self.log_message.emit(f"Found {len(accounts)} accounts and {len(filtered_products)} products", "INFO")
            
            # Process accounts in batches
            for i in range(0, len(accounts), batch_size):
                if not self.is_running:
                    break
                
                # Wait if paused
                while self.is_paused and self.is_running:
                    time.sleep(1)
                
                if not self.is_running:
                    break
                
                batch_accounts = accounts[i:i + batch_size]
                batch_emails = [acc['email'] for acc in batch_accounts]
                
                self.log_message.emit(f"Processing batch {i//batch_size + 1} with {len(batch_accounts)} accounts", "INFO")
                self.batch_started.emit(batch_emails)
                
                # Process batch in parallel
                threads = []
                for account in batch_accounts:
                    thread = threading.Thread(
                        target=self._process_account,
                        args=(account, filtered_products)
                    )
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                
                for thread in threads:
                    thread.join()

                if i + batch_size < len(accounts) and self.is_running:
                    delay = random.randint(10, 30)
                    self.log_message.emit(f"Waiting {delay} seconds before next batch...", "INFO")
                    time.sleep(delay)
            
            self.log_message.emit("Posting process completed", "INFO")
            self.posting_completed.emit(group_id)
            
        except Exception as e:
            self.log_message.emit(f"Error in posting process: {str(e)}", "ERROR")
        finally:
            self.is_running = False
    
    def _process_account(self, account, products):
        """Process a single account with human-like behavior"""
        account_id = account['id']
        email = account['email']
        
        try:
            self.account_status_changed.emit(account_id, "processing", "Initializing browser")
            self.log_message.emit(f"Processing account: {email}", "INFO")
            
            with sync_playwright() as p:
                user_agent = random.choice(self.user_agents)
                
                viewport_width = random.randint(1200, 1920)
                viewport_height = random.randint(800, 1080)
                
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        f'--user-agent={user_agent}',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                )
                
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': viewport_width, 'height': viewport_height},
                    locale='en-US',
                    timezone_id='America/New_York'
                )
                context.set_default_timeout(60000) 
                # Load cookies if available
                if account['cookies']:
                    try:
                        cookies = json.loads(account['cookies'])
                        context.add_cookies(cookies)
                        self.log_message.emit(f"Loaded cookies for {email}", "INFO")
                    except:
                        self.log_message.emit(f"Failed to load cookies for {email}", "WARNING")
                
                page = context.new_page()
                
                # Add stealth scripts
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    window.chrome = {
                        runtime: {},
                    };
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                """)
                
                # Check if logged in
                self.account_status_changed.emit(account_id, "processing", "Checking login status")
                page.goto("https://www.facebook.com/", wait_until='domcontentloaded')
                
                # Human-like delay
                time.sleep(random.uniform(2, 5))
                
                if self._is_login_required(page):
                    self.account_status_changed.emit(account_id, "processing", "Logging in")
                    if not self._login_facebook(page, account['email'], account['password']):
                        self.log_message.emit(f"Login failed for {email}", "ERROR")
                        self.account_status_changed.emit(account_id, "failed", "Login failed")
                        self.db_manager.update_account_status(account_id, "failed")
                        browser.close()
                        return
                    
                    # Save cookies after successful login
                    cookies = context.cookies()
                    self.db_manager.update_account_cookies(account_id, json.dumps(cookies))
                    self.log_message.emit(f"Login successful for {email}", "INFO")
                
                # Post products with human-like behavior
                successful_posts = 0
                for product in products:
                    if not self.is_running:
                        break
                    
                    # Wait if paused
                    while self.is_paused and self.is_running:
                        time.sleep(1)
                    
                    if not self.is_running:
                        break
                    
                    self.account_status_changed.emit(account_id, "processing", f"Posting: {product['name']}")
                    
                    success, reason = self._post_product(page, product)
                    
                    # Log the attempt
                    status = "Success" if success else "Failed"
                    self.db_manager.log_posting_attempt(account_id, product['id'], status, reason)
                    
                    if success:
                        successful_posts += 1
                        self.log_message.emit(f"Posted '{product['name']}' for {email}", "INFO")
                    else:
                        self.log_message.emit(f"Failed to post '{product['name']}' for {email}: {reason}", "ERROR")
                    
                    # Human-like delay between posts
                    delay = random.randint(15, 30)
                    time.sleep(delay)
                
                browser.close()
                
                # Update account status
                if successful_posts > 0:
                    self.account_status_changed.emit(account_id, "completed", f"Posted {successful_posts} products")
                    self.db_manager.update_account_status(account_id, "active")
                    self.log_message.emit(f"Completed processing {email} - {successful_posts} products posted", "INFO")
                else:
                    self.account_status_changed.emit(account_id, "failed", "No products posted")
                    self.log_message.emit(f"No products posted for {email}", "WARNING")
        
        except Exception as e:
            self.log_message.emit(f"Error processing account {email}: {str(e)}", "ERROR")
            self.account_status_changed.emit(account_id, "failed", str(e))
            self.db_manager.update_account_status(account_id, "failed")
    
    def _is_login_required(self, page):
        """Check if login is required with less strict verification"""
        try:
            page.wait_for_timeout(32000)
            logged_in_selectors = [
                '[data-testid="blue_bar_profile_link"]',
                '[aria-label="Account"]',
                '[data-testid="left_nav_menu_item"]',
                'div[role="banner"]',
                '[data-testid="nav-search-input"]',
                '[aria-label="home"]',
            ]
            
            for selector in logged_in_selectors:
                try:
                    if page.query_selector(selector):
                        return False
                except:
                    continue
            return True
            
        except:
            return True
    
    def _login_facebook(self, page, email, password):
        """Login to Facebook with human-like behavior"""
        try:
            page.goto("https://www.facebook.com/", wait_until='domcontentloaded')
            time.sleep(random.uniform(2, 4))
            page.wait_for_selector("input[name='email']")
            email_field = page.query_selector("input[name='email']")
            if email_field:
                email_field.click()
                time.sleep(random.uniform(1, 3))
                
                for char in email:
                    page.keyboard.type(char)
                    time.sleep(random.uniform(0.05, 0.15))
            time.sleep(random.uniform(1, 3))

            password_field = page.query_selector("input[name='pass']")
            if password_field:
                password_field.click()
                time.sleep(random.uniform(1, 3))
                
                for char in password:
                    page.keyboard.type(char)
                    time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(1, 3))
            
            login_button = page.query_selector("button[name='login']")
            if login_button:
                login_button.click()

            time.sleep(random.uniform(3, 6))
            page.wait_for_load_state("networkidle")

            time.sleep(random.uniform(3, 5))
            current_url = page.url.lower()

            if "login" in current_url or "checkpoint" in current_url or "challenge" in current_url:
                return False
            if "two_step_verification" in current_url or "authentication" in current_url:
                raise Exception("2FA or Captcha detected")
            return True
            
        except Exception as e:
            self.log_message.emit(f"Login error: {str(e)}", "ERROR")
            return False
    
    def _post_product(self, page, product):
        """Post a single product to Facebook Marketplace with improved selectors"""
        try:
            page.goto("https://www.facebook.com/marketplace/create/item", timeout=80000, wait_until="domcontentloaded")

            time.sleep(random.uniform(3, 5))
            title_selectors = [
                "input[id='_r_4n_']",
                "input[placeholder*='What are you selling']",
                "input[aria-label*='Title']",
                "input[name='title']",
                "input[placeholder*='title']",
                "input[aria-label*='What are you selling']",
                "//span[contains(text(), 'Title')]/following::input[1]",
                "//label[contains(., 'What are you selling')]/following::input[1]",
                "//input[@aria-label='Title']",
                "//input[contains(@placeholder, 'What are you selling')]",
            ]
            
            title_field = None
            for selector in title_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    title_field = page.query_selector(selector)
                    if title_field:
                        break
                except:
                    continue
            
            if not title_field:
                return False, "Could not find title field"
            
            title_field.click()
            time.sleep(random.uniform(0.5, 1))

            page.keyboard.press("Control+a")
            time.sleep(0.2)
            
            for char in product['name']:
                page.keyboard.type(char)
                time.sleep(random.uniform(0.05, 0.12))

            time.sleep(random.uniform(2, 4))
            page.evaluate("""
                document.querySelectorAll('input[type="file"][accept*="image"]').forEach(input => {
                    input.style.display = 'block';
                    input.style.opacity = '1';
                    input.style.visibility = 'visible';
                    input.style.width = '300px';
                    input.style.height = '50px';
                    input.style.zIndex = '9999';
                    input.style.position = 'fixed';
                    input.style.top = '30px';
                    input.style.left = '30px';
                    input.removeAttribute('hidden');
                });
            """)
            time.sleep(random.uniform(1, 2))
            price_selectors = [
                "input[aria-label*='Price']",
                "input[placeholder*='Price']",
                "input[name='price']",
                "input[aria-label*='price']",
                "//span[contains(text(), 'Price')]/following::input[1]",
                "//label[contains(., 'Price')]/following::input[1]",
                "//input[@id='_r_4r_']"
            ]
            
            price_filled = False
            for selector in price_selectors:
                try:
                    price_field = page.query_selector(selector)
                    if price_field:
                        price_field.click()
                        time.sleep(random.uniform(0.5, 1))
                        
                        page.keyboard.press("Control+a")
                        time.sleep(0.2)
                        
                        price_str = str(int(product['price']))
                        for char in price_str:
                            page.keyboard.type(char)
                            time.sleep(random.uniform(0.05, 0.1))
                        
                        price_filled = True
                        break
                except:
                    continue
            
            if not price_filled:
                self.log_message.emit("Could not find price field", "WARNING")
            
            # Human delay
            time.sleep(random.uniform(1, 2))

            # === CATEGORY SELECTION ===
            if product['category']:
                category_selectors = [
                    "//span[contains(text(), 'Category')]/ancestor::label[1]",
                    "//label[contains(@aria-labelledby, '_r_') and descendant::span[contains(text(), 'Category')]]",
                    "//div[contains(@class, 'xjhjgkd')]//label[@role='combobox' and descendant::span[contains(text(), 'Category')]]",
                ]
                
                for selector in category_selectors:
                    try:
                        category_field = page.query_selector(selector)
                        if category_field:
                            category_field.click()
                            time.sleep(random.uniform(0.5, 1))

                            # Wait for dropdown to load
                            time.sleep(random.uniform(0.3, 0.7))

                            category_options = [
                                f"//span[contains(text(), '{product['category']}')]",
                                f"//div[contains(text(), '{product['category']}')]",
                                f"[role='button'][aria-label*='{product['category']}']",
                                f"div[data-visualcompletion='ignore-dynamic'] span:has-text('{product['category']}')",
                                f"//div[@role='button']//span[contains(text(), '{product['category']}')]"
                            ]

                            for option_selector in category_options:
                                try:
                                    category_option = page.query_selector(option_selector)
                                    if category_option:
                                        time.sleep(random.uniform(0.2, 0.5))
                                        category_option.click()
                                        time.sleep(random.uniform(0.3, 0.8))
                                        break
                                except Exception:
                                    continue
                            break  # Break outer loop once category is handled
                    except Exception:
                        continue


            # === CONDITION SELECTION ===
            time.sleep(random.uniform(1, 2))
            if product['condition']:
                condition_selectors = [
                    "//span[contains(text(), 'Condition')]/ancestor::label[1]",
                    "//label[contains(@aria-labelledby, '_r_') and descendant::span[contains(text(), 'Condition')]]",
                    "//div[contains(@class, 'xjhjgkd')]//label[@role='combobox' and descendant::span[contains(text(), 'Condition')]]",
                ]

                for selector in condition_selectors:
                    try:
                        condition_field = page.query_selector(selector)
                        if condition_field:
                            print(f"Found condition field, clicking...")
                            condition_field.click()
                            time.sleep(random.uniform(0.8, 1.2))

                            # Wait for dropdown options with specific ID pattern to appear
                            dropdown_appeared = False
                            for attempt in range(15):
                                # Look for elements with the specific ID pattern from your HTML: _r_1q___0, _r_1q___1, etc.
                                options = page.query_selector_all("//div[starts-with(@id, '_r_') and contains(@id, '___') and @role='option']")
                                if options and len(options) > 0:
                                    dropdown_appeared = True
                                    print(f"Found {len(options)} condition options with unique IDs")
                                    break
                                time.sleep(0.3)

                            if not dropdown_appeared:
                                print("Condition dropdown with unique IDs didn't appear")
                                continue

                            # Ultra-precise XPath targeting only dropdown options with unique IDs
                            option_found = False
                            
                            # Get all condition options using the unique ID pattern
                            condition_xpath_selectors = [
                                # Exact text match within uniquely identified dropdown options
                                f"//div[starts-with(@id, '_r_') and contains(@id, '___') and @role='option']//span[text()='{product['condition']}']",
                                
                                # Case insensitive exact match
                                f"//div[starts-with(@id, '_r_') and contains(@id, '___') and @role='option']//span[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')=translate('{product['condition']}', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')]",
                                
                                # Partial match for complex conditions like "Used – like new"
                                f"//div[starts-with(@id, '_r_') and contains(@id, '___') and @role='option']//span[contains(text(), '{product['condition']}')]",
                                
                                # Match first word (for "New", "Used" etc.)
                                f"//div[starts-with(@id, '_r_') and contains(@id, '___') and @role='option']//span[starts-with(text(), '{product['condition'].split()[0]}')]",
                            ]

                            # Debug: Show available options
                            available_options = page.query_selector_all("//div[starts-with(@id, '_r_') and contains(@id, '___') and @role='option']//span")
                            available_texts = []
                            for opt in available_options:
                                try:
                                    text = opt.text_content().strip()
                                    if text:
                                        available_texts.append(text)
                                except:
                                    pass
                            print(f"Available condition options: {available_texts}")
                            print(f"Looking for: '{product['condition']}'")

                            # Try each XPath selector
                            for xpath_selector in condition_xpath_selectors:
                                try:
                                    print(f"Trying XPath: {xpath_selector}")
                                    option_span = page.query_selector(xpath_selector)
                                    if option_span:
                                        # Get the parent div with role='option' to click
                                        option_div = option_span.query_selector("xpath=./ancestor::div[@role='option']")
                                        if option_div:
                                            print(f"Found option div with ID: {option_div.get_attribute('id')}")
                                            option_div.scroll_into_view_if_needed()
                                            time.sleep(0.2)
                                            
                                            # Click the option div
                                            option_div.click()
                                            print(f"Successfully clicked condition: {product['condition']}")
                                            time.sleep(random.uniform(0.5, 1.0))
                                            option_found = True
                                            break
                                    else:
                                        print("No match found with this XPath")
                                except Exception as e:
                                    print(f"Error with XPath selector: {e}")
                                    continue

                            # Alternative approach: Direct ID-based clicking if text matching fails
                            if not option_found:
                                print("Trying direct ID-based approach...")
                                option_divs = page.query_selector_all("//div[starts-with(@id, '_r_') and contains(@id, '___') and @role='option']")
                                
                                for div in option_divs:
                                    try:
                                        span = div.query_selector(".//span")
                                        if span:
                                            span_text = span.text_content().strip()
                                            # Exact match or case-insensitive match
                                            if (span_text == product['condition'] or 
                                                span_text.lower() == product['condition'].lower() or
                                                product['condition'].lower() in span_text.lower()):
                                                
                                                div_id = div.get_attribute('id')
                                                print(f"Direct clicking option with ID: {div_id}, text: '{span_text}'")
                                                div.scroll_into_view_if_needed()
                                                time.sleep(0.2)
                                                div.click()
                                                time.sleep(random.uniform(0.5, 1.0))
                                                option_found = True
                                                break
                                    except Exception as e:
                                        print(f"Error in direct ID approach: {e}")
                                        continue

                            if not option_found:
                                print(f"FAILED: Could not find and click condition '{product['condition']}'")
                                print(f"Available options were: {available_texts}")
                            else:
                                print(f"SUCCESS: Condition '{product['condition']}' selected")

                            break
                            
                    except Exception as e:
                        print(f"Error with condition selector {selector}: {e}")
                        continue

            if product.get('images_folder') and os.path.exists(product['images_folder']):
                try:
                    image_files = [
                        os.path.join(product['images_folder'], file)
                        for file in os.listdir(product['images_folder'])
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
                    ][:10]

                    if image_files:
                        page.wait_for_selector('input[type="file"][accept*="image"]', timeout=31000)
                        page.set_input_files('input[type="file"][accept*="image"]', image_files)
                        time.sleep(random.uniform(5, 8))

                except Exception as e:
                    self.log_message.emit(f"Image upload error: {str(e)}", "WARNING")

            time.sleep(random.uniform(4, 8))
            
            # try:
            #     more_details_selectors = [
            #         "//span[text()='More details']/ancestor::div[@role='button']",
            #         "//span[contains(text(), 'More details')]/ancestor::div[@role='button']",
            #         "div[role='button']:has(span#_r_22_)",
            #         "#_r_22_",  # Direct ID target, safest if static
            #         "span:has-text('More details')",
            #     ]

            #     for selector in more_details_selectors:
            #         try:
            #             more_details_btn = page.query_selector(selector)
            #             if more_details_btn:
            #                 time.sleep(random.uniform(0.3, 0.6))
            #                 more_details_btn.click()
            #                 time.sleep(random.uniform(0.4, 0.8))
            #                 break
            #         except Exception as e:
            #             self.log_message.emit(f"[!] Failed selector: {selector} | {e}", "WARNING")
            #             continue
            # except Exception as e:
            #     self.log_message.emit(f"[!] Error clicking 'More details': {e}", "WARNING")

            # Fill description if available
            if product['description']:
                description_selectors = [
                    "textarea#_r_3l_",
                    "//span[text()='Description']/ancestor::label//textarea",
                    "//label[contains(., 'Description')]//textarea",
                    "textarea[class*='x1tutvks']",
                    "textarea[class*='x1s07b3s']",
                    "textarea[class*='xcrlgei']"
                ]

                for selector in description_selectors:
                    try:
                        desc_field = page.query_selector(selector)
                        if desc_field:
                            desc_field.click()
                            time.sleep(random.uniform(0.3, 0.5))

                            # Clear existing content
                            desc_field.fill("")  # optional, safe reset

                            # Paste full text instantly
                            page.keyboard.insert_text(product['description'])

                            time.sleep(random.uniform(0.4, 0.7))
                            break
                    except Exception as e:
                        continue

            time.sleep(random.uniform(2, 4))
            if product['location']:
                location_selectors = [
                    'input[placeholder="Location"]',
                    '//label[contains(., "Location")]/following-sibling::div//input',
                    '//input[contains(@aria-label, "Location")]',
                    '//div[contains(text(),"Location")]/following::input[1]',
                    'input[id="_r_5d_"]',
                ]

                for selector in location_selectors:
                    try:
                        location_input = page.query_selector(selector)
                        if location_input:
                            location_input.click()
                            time.sleep(random.uniform(0.3, 0.5))

                            location_input.fill("")
                            page.keyboard.insert_text(product['location'])

                            time.sleep(random.uniform(1.0, 1.5))  # wait for dropdown

                            # Multi-tag selectors for the suggestion list
                            suggestion_selectors = [
                                'ul[role="listbox"] > li:nth-child(1)',
                                '//ul[@role="listbox"]/li[1]',
                                '//div[@role="listbox"]//li[1]',
                                '//div[@aria-label="Location"]/following::ul//li[1]',
                            ]

                            for s_selector in suggestion_selectors:
                                try:
                                    first_suggestion = page.query_selector(s_selector)
                                    if first_suggestion:
                                        first_suggestion.click()
                                        time.sleep(random.uniform(0.4, 0.6))
                                        break
                                except Exception:
                                    continue

                            break  # exit outer loop once filled and selected
                    except Exception:
                        continue

            # Human delay before publishing
            time.sleep(random.uniform(4, 6))
            
            # Try to find and click publish/next button
            # --- STEP 1: Click "Next" button ---
            next_selectors = [
                "div[aria-label='Next'][aria-disabled!='true'][role='button']",
                "//div[@role='button' and @aria-label='Next' and not(@aria-disabled='true')]",
                "div[class*='x1i10hfl'][role='button'][tabindex='0']"  # generic enabled button fallback
            ]

            next_clicked = False
            for selector in next_selectors:
                try:
                    for _ in range(10):
                        next_btn = page.query_selector(selector)
                        if next_btn and next_btn.is_visible():
                            aria_disabled = next_btn.get_attribute("aria-disabled")
                            if not aria_disabled or aria_disabled == "false":
                                next_btn.scroll_into_view_if_needed()
                                time.sleep(random.uniform(0.5, 0.8))
                                next_btn.click()
                                self.log_message.emit(f"Clicked Next button: {selector}", "INFO")
                                next_clicked = True
                                break
                        time.sleep(0.5)
                    if next_clicked:
                        break
                except Exception:
                    continue

            # --- STEP 2: Click "Publish" button after Next is done ---
            if next_clicked:
                time.sleep(random.uniform(1.2, 2.0))  # wait for transition to publish

                publish_selectors = [
                    "div[aria-label='Publish'][aria-disabled!='true'][role='button']",
                    "//div[@role='button' and @aria-label='Publish' and not(@aria-disabled='true')]",
                    "div[class*='x1i10hfl'][role='button'][tabindex='0']"
                ]

                for selector in publish_selectors:
                    try:
                        for _ in range(10):
                            publish_btn = page.query_selector(selector)
                            if publish_btn and publish_btn.is_visible():
                                aria_disabled = publish_btn.get_attribute("aria-disabled")
                                if not aria_disabled or aria_disabled == "false":
                                    publish_btn.scroll_into_view_if_needed()
                                    time.sleep(random.uniform(0.5, 0.8))
                                    publish_btn.click()
                                    self.log_message.emit(f"Clicked Publish button: {selector}", "INFO")
                                    break
                            time.sleep(0.5)
                        else:
                            self.log_message.emit("Publish button not found or disabled", "ERROR")
                    except Exception:
                        continue


                # Wait for navigation or UI change
                time.sleep(random.uniform(4, 6))

                current_url = page.url.lower()
                success_indicators = [
                    "marketplace/item",
                    "marketplace/you/selling",
                    "marketplace/you"
                ]

                for indicator in success_indicators:
                    if indicator in current_url:
                        return True, "Posted successfully"

                # If URL changed away from the create page, assume success
                if "marketplace/create" not in current_url:
                    return True, "Posting completed"

            
            return True, "Posting may have completed"
            
        except Exception as e:
            return False, f"Error posting product: {str(e)}"
