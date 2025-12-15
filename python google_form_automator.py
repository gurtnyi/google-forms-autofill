#!/usr/bin/env python3
"""
Google Form Automation Script with File Input Support
Features:
- Read URL from url.txt
- Read target text from text.txt
- Option to use file input or manual input
- Simplified proxy handling
"""

import random
import time
import os
import sys
from typing import Tuple, List, Dict, Optional
from datetime import datetime

# Third-party imports
try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    from selenium_stealth import stealth
    from fake_useragent import UserAgent
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install undetected-chromedriver selenium selenium-stealth fake-useragent")
    sys.exit(1)


class GoogleFormAutomator:
    """Automation class with file input support"""

    def __init__(self, use_proxies: bool = False):
        """Initialize the automator"""
        self.driver = None
        self.use_proxies = use_proxies
        self.proxy_list = self.load_proxies() if use_proxies else []
        self.current_proxy_index = 0
        self.ua = UserAgent()
        self.log_file = 'log.txt'
        self.progress_file = 'completed_requests.txt'

        # Statistics
        self.stats = {
            'success': 0,
            'failed': 0,
            'captcha_encountered': 0,
            'proxy_rotations': 0,
            'start_time': None,
            'end_time': None
        }

        # Progress tracking
        self.progress_data = self.load_progress()

        # Setup log.txt
        self.setup_log_file()

    def load_from_file(self, filename: str, default_value: str = "") -> str:
        """Load content from a file"""
        if not os.path.exists(filename):
            return default_value

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    print(f"Loaded from {filename}: {content[:50]}..." if len(
                        content) > 50 else f"Loaded from {filename}: {content}")
                    return content
                else:
                    print(f"{filename} is empty")
                    return default_value
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return default_value

    def load_proxies(self) -> List[str]:
        """Load proxies from proxies.txt file"""
        proxy_file = 'proxies.txt'

        if not os.path.exists(proxy_file):
            print(f"Note: {proxy_file} not found.")
            return []

        proxies = []
        try:
            with open(proxy_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxies.append(line)

            print(f"Loaded {len(proxies)} proxies from {proxy_file}")

            # Show first few proxies
            for i, proxy in enumerate(proxies[:3]):
                print(f"  Proxy {i + 1}: {proxy}")
            if len(proxies) > 3:
                print(f"  ... and {len(proxies) - 3} more")

            return proxies

        except Exception as e:
            print(f"Error reading {proxy_file}: {e}")
            return []

    def setup_driver(self) -> uc.Chrome:
        """Setup Chrome driver with optional proxy"""
        options = uc.ChromeOptions()

        # Anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")

        # Window size
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f"--window-size={width},{height}")

        # User agent
        user_agent = self.ua.random
        options.add_argument(f'user-agent={user_agent}')

        # Add proxy if available
        if self.use_proxies and self.proxy_list:
            proxy = self.get_next_proxy()
            if proxy:
                # Format proxy correctly
                if proxy.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
                    proxy_arg = proxy
                else:
                    proxy_arg = f'http://{proxy}'

                options.add_argument(f'--proxy-server={proxy_arg}')
                print(f"Using proxy: {proxy}")
                self.log_message(f"Using proxy: {proxy}")

        # Create driver
        try:
            driver = uc.Chrome(
                options=options,
                headless=False,
                version_main=None
            )
        except Exception as e:
            print(f"Error initializing Chrome: {e}")
            print("Trying without proxy...")
            # Remove proxy and try again
            options.arguments = [arg for arg in options.arguments if not arg.startswith('--proxy-server=')]
            driver = uc.Chrome(
                options=options,
                headless=False,
                version_main=None
            )

        # Set timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(5)

        # Apply stealth
        try:
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )
        except:
            pass

        # Hide WebDriver
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy from the list"""
        if not self.proxy_list:
            return None

        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    def load_progress(self) -> Dict:
        """Load progress from completed_requests.txt or create new"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return self.create_new_progress()

                    lines = content.split('\n')
                    progress_data = {
                        'total_desired': 0,
                        'completed': 0,
                        'history': []
                    }

                    for line in lines:
                        if line.startswith('TOTAL_DESIRED:'):
                            progress_data['total_desired'] = int(line.split(':')[1].strip())
                        elif line.startswith('COMPLETED:'):
                            progress_data['completed'] = int(line.split(':')[1].strip())
                        elif line.startswith('[') and ']' in line:
                            progress_data['history'].append(line)

                    print(f"Loaded progress: {progress_data['completed']}/{progress_data['total_desired']} completed")
                    return progress_data

            except Exception as e:
                print(f"Error reading progress file: {e}")
                return self.create_new_progress()
        else:
            return self.create_new_progress()

    def create_new_progress(self) -> Dict:
        """Create new progress structure"""
        return {
            'total_desired': 0,
            'completed': 0,
            'history': []
        }

    def save_progress(self, additional_completed: int = 0):
        """Save progress to completed_requests.txt"""
        if additional_completed > 0:
            self.progress_data['completed'] += additional_completed

        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                f.write(f"TOTAL_DESIRED: {self.progress_data['total_desired']}\n")
                f.write(f"COMPLETED: {self.progress_data['completed']}\n")
                f.write(f"REMAINING: {max(0, self.progress_data['total_desired'] - self.progress_data['completed'])}\n")
                f.write(f"LAST_UPDATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")

                for entry in self.progress_data['history'][-100:]:
                    f.write(entry + "\n")

                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] Added {additional_completed} successful submissions\n")
                self.progress_data['history'].append(
                    f"[{timestamp}] Added {additional_completed} successful submissions")

            print(f"Progress saved: {self.progress_data['completed']}/{self.progress_data['total_desired']} completed")
            self.log_message(f"Progress saved: {self.progress_data['completed']}/{self.progress_data['total_desired']}")

        except Exception as e:
            print(f"Error saving progress: {e}")

    def setup_log_file(self):
        """Initialize or clear log.txt at the start of each run"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Google Form Automation Log ===\n")
                f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(
                    f"Progress: {self.progress_data['completed']}/{self.progress_data['total_desired']} completed\n")
                f.write("=" * 50 + "\n\n")
            print(f"Log file initialized: {self.log_file}")
        except Exception as e:
            print(f"Warning: Could not create log file: {e}")

    def log_message(self, message: str):
        """Write a message to log.txt"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

    def find_form_elements(self, target_option: str) -> Tuple[bool, str]:
        """Find and interact with form elements"""
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form, div[role='form'], body"))
            )

            time.sleep(random.uniform(1, 2))

            target_lower = target_option.lower()

            # Look for radio buttons
            elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='radio'], input[type='radio'], label")

            for element in elements:
                try:
                    element_text = element.text.strip().lower()
                    if target_lower in element_text:
                        time.sleep(random.uniform(0.3, 0.8))
                        element.click()
                        self.log_message(f"Selected option: {element_text[:50]}...")
                        return True, f"Option selected: {element_text[:30]}"
                except:
                    continue

            # Try by value attribute
            input_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            for element in input_elements:
                try:
                    value = element.get_attribute("value") or ""
                    if target_lower in value.lower():
                        time.sleep(random.uniform(0.3, 0.8))
                        element.click()
                        return True, "Option selected via value"
                except:
                    continue

            # Fallback: click first option
            if elements:
                time.sleep(random.uniform(0.3, 0.8))
                elements[0].click()
                return True, "Selected first option (fallback)"

            return False, f"Could not find option: {target_option}"

        except TimeoutException:
            return False, "Form loading timeout"
        except Exception as e:
            return False, f"Error finding elements: {str(e)[:100]}"

    def submit_form(self) -> Tuple[bool, str]:
        """Submit the form"""
        try:
            # Find submit button
            submit_selectors = [
                "//*[contains(text(), 'Submit')]",
                "//*[contains(text(), 'Küldés')]",
                "div[role='button']",
                "button",
                "input[type='submit']"
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            submit_button = element
                            break
                    if submit_button:
                        break
                except:
                    continue

            if not submit_button:
                return False, "Submit button not found"

            # Human-like delay
            time.sleep(random.uniform(0.5, 1.5))

            # Click
            try:
                submit_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", submit_button)

            # Wait for submission
            time.sleep(random.uniform(1, 3))

            # Check for success
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()

            # Success indicators
            if 'formresponse' in current_url or 'thank you' in page_source or 'köszönjük' in page_source:
                return True, "Submission successful"

            # Check for CAPTCHA
            if any(word in page_source for word in ['captcha', 'recaptcha', 'not a robot']):
                self.stats['captcha_encountered'] += 1
                return False, "CAPTCHA detected"

            # If still on form page
            if 'viewform' in current_url:
                return False, "Still on form page"

            return True, "Submission completed"

        except Exception as e:
            return False, f"Submission error: {str(e)[:100]}"

    def run_submission(self, form_url: str, target_option: str, attempt: int) -> bool:
        """Execute a single form submission"""
        try:
            self.log_message(f"Attempt {attempt}: Loading form")

            self.driver.get(form_url)
            time.sleep(random.uniform(2, 4))

            success, error = self.find_form_elements(target_option)
            if not success:
                self.log_message(f"Attempt {attempt}: Failed to find option - {error}")
                return False

            submit_success, error = self.submit_form()
            if submit_success:
                self.log_message(f"Attempt {attempt}: Successfully submitted")
                return True
            else:
                self.log_message(f"Attempt {attempt}: Submission failed - {error}")
                return False

        except Exception as e:
            error_msg = f"Attempt {attempt}: Exception - {str(e)[:100]}"
            print(error_msg)
            self.log_message(error_msg)
            return False

    def rotate_session(self):
        """Rotate to new session with new proxy"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

        time.sleep(random.uniform(2, 4))

        if self.use_proxies:
            print("Rotating to new proxy...")
            self.stats['proxy_rotations'] += 1

        self.driver = self.setup_driver()

    def run_campaign(self, form_url: str, target_option: str, max_requests: int = None) -> Dict:
        """Main method to run the submission campaign"""

        # Calculate requests for this session
        if max_requests is None:
            remaining = max(0, self.progress_data['total_desired'] - self.progress_data['completed'])
            if remaining == 0:
                print(
                    f"\n✓ Goal already reached: {self.progress_data['completed']}/{self.progress_data['total_desired']}")
                return self.stats
            requests_this_session = remaining
        else:
            remaining = max(0, self.progress_data['total_desired'] - self.progress_data['completed'])
            requests_this_session = min(max_requests, remaining) if remaining > 0 else max_requests

        if requests_this_session <= 0:
            print(f"\n✓ Goal already reached: {self.progress_data['completed']}/{self.progress_data['total_desired']}")
            return self.stats

        start_msg = f"Starting session | This session: {requests_this_session} | Remaining: {remaining}"
        print(start_msg)
        self.log_message(start_msg)

        self.stats['start_time'] = datetime.now()

        # Setup initial driver
        try:
            self.driver = self.setup_driver()
            if not self.driver:
                print("Failed to initialize driver. Exiting.")
                return self.stats

        except Exception as e:
            error_msg = f"Failed to initialize driver: {e}"
            print(error_msg)
            self.log_message(error_msg)
            return self.stats

        try:
            for i in range(1, requests_this_session + 1):
                global_attempt = self.progress_data['completed'] + i

                print(
                    f"\n[Attempt {i}/{requests_this_session}] Global: {global_attempt}/{self.progress_data['total_desired']}")

                if self.use_proxies:
                    print(f"Using proxy rotation (rotation #{self.stats['proxy_rotations']})")

                # Run submission
                success = self.run_submission(form_url, target_option, i)

                # Update statistics
                if success:
                    self.stats['success'] += 1
                    status = "✓ Success"
                else:
                    self.stats['failed'] += 1
                    status = "✗ Failed"

                # Display progress
                session_success_rate = (self.stats['success'] / i * 100) if i > 0 else 0
                global_progress = self.progress_data['completed'] + self.stats['success']

                progress_msg = f"[{i}/{requests_this_session}] {status} | Session: {self.stats['success']}S/{self.stats['failed']}F ({session_success_rate:.1f}%) | Global: {global_progress}/{self.progress_data['total_desired']}"
                print(progress_msg)
                self.log_message(progress_msg)

                # Rotate session periodically if using proxies
                if i < requests_this_session:
                    if self.use_proxies and i % 5 == 0:  # Rotate every 5 submissions
                        print("Rotating proxy...")
                        self.rotate_session()

                    # Delay between submissions
                    delay = random.uniform(3, 6)
                    print(f"Waiting {delay:.1f} seconds...")
                    time.sleep(delay)

        except KeyboardInterrupt:
            interrupt_msg = "\nSession interrupted by user"
            print(interrupt_msg)
            self.log_message(interrupt_msg)
        except Exception as e:
            error_msg = f"Session error: {str(e)}"
            print(f"\n{error_msg}")
            self.log_message(error_msg)
        finally:
            # Cleanup
            self.stats['end_time'] = datetime.now()
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

            # Save progress
            if self.stats['success'] > 0:
                self.save_progress(self.stats['success'])

            # Calculate final statistics
            duration = self.stats['end_time'] - self.stats['start_time']
            self.stats['duration'] = str(duration)

            # Log final results
            self.log_final_results()

            return self.stats

    def log_final_results(self):
        """Write final results to log.txt"""
        total = self.stats['success'] + self.stats['failed']

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write("\n" + "=" * 50 + "\n")
                f.write("SESSION RESULTS\n")
                f.write("=" * 50 + "\n")
                f.write(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Session duration: {self.stats['duration']}\n")
                f.write(f"Session attempts: {total}\n")
                f.write(f"Session successful: {self.stats['success']}\n")
                f.write(f"Session failed: {self.stats['failed']}\n")
                if total > 0:
                    f.write(f"Session success rate: {self.stats['success'] / total * 100:.1f}%\n")
                f.write(f"CAPTCHA encounters: {self.stats['captcha_encountered']}\n")
                if self.use_proxies:
                    f.write(f"Proxy rotations: {self.stats['proxy_rotations']}\n")
                f.write(f"Global progress: {self.progress_data['completed']}/{self.progress_data['total_desired']}\n")
                f.write(f"Remaining: {max(0, self.progress_data['total_desired'] - self.progress_data['completed'])}\n")
                f.write("=" * 50 + "\n")
        except Exception as e:
            print(f"Warning: Could not write final results: {e}")


def check_required_packages():
    """Check if all required packages are installed"""
    required = [
        ('undetected-chromedriver', 'undetected_chromedriver'),
        ('selenium', 'selenium'),
        ('selenium-stealth', 'selenium_stealth'),
        ('fake-useragent', 'fake_useragent')
    ]

    missing = []
    for pip_name, import_name in required:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)

    return missing


def get_input_method(prompt: str, filename: str, input_type: str = "text") -> str:
    """Get input from file or manual entry"""
    print(f"\n--- {prompt.upper()} ---")

    # Check if file exists
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            file_content = f.read().strip()

        if file_content:
            print(f"Found {filename} with content:")
            print(f"  {file_content[:80]}..." if len(file_content) > 80 else f"  {file_content}")

            choice = input(f"Use {filename}? (Y/n): ").strip().lower()
            if choice != 'n':
                return file_content
        else:
            print(f"{filename} exists but is empty")

    # Manual input
    if input_type == "url":
        return input(f"Enter Google Form URL: ").strip()
    else:
        return input(f"Enter exact option text: ").strip()


def main():
    """Main execution function"""
    print("=" * 60)
    print("GOOGLE FORM AUTOMATION - FILE INPUT SUPPORT")
    print("=" * 60)
    print("Supports: url.txt, text.txt, proxies.txt files")
    print("=" * 60)

    # Check packages
    missing = check_required_packages()
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return

    # Initialize automator early to load progress
    print("\n--- PROGRESS CHECK ---")
    automator = GoogleFormAutomator(use_proxies=False)

    # Check if we need to set total desired
    if automator.progress_data['total_desired'] == 0:
        print("No total desired count set. First time setup.")
        while True:
            try:
                total_input = input("Enter TOTAL number of submissions desired: ").strip()
                if total_input:
                    total_desired = int(total_input)
                    if total_desired > 0:
                        automator.progress_data['total_desired'] = total_desired
                        automator.save_progress()
                        print(f"Set total desired to: {total_desired}")
                        break
                    else:
                        print("Please enter a positive number.")
                else:
                    print("You must enter a total number.")
            except ValueError:
                print("Please enter a valid number.")

    # Display current progress
    print(f"\nCurrent progress: {automator.progress_data['completed']}/{automator.progress_data['total_desired']}")
    remaining = max(0, automator.progress_data['total_desired'] - automator.progress_data['completed'])
    print(f"Remaining submissions: {remaining}")

    if remaining == 0:
        print("\n✓ Goal already achieved!")
        choice = input("Do you want to set a new goal? (y/N): ").strip().lower()
        if choice == 'y':
            while True:
                try:
                    new_total = int(input("Enter new total desired: ").strip())
                    if new_total > automator.progress_data['completed']:
                        automator.progress_data['total_desired'] = new_total
                        automator.save_progress()
                        remaining = new_total - automator.progress_data['completed']
                        print(f"New goal set: {automator.progress_data['completed']}/{new_total}")
                        break
                    else:
                        print(
                            f"New total must be greater than current completed ({automator.progress_data['completed']})")
                except ValueError:
                    print("Please enter a valid number.")
        else:
            print("Exiting.")
            return

    # Get form URL (from file or manual)
    form_url = get_input_method("FORM URL", "url.txt", "url")

    if not form_url:
        print("Error: No URL provided. Exiting.")
        return

    # Get target option (from file or manual)
    target_option = get_input_method("TARGET OPTION", "text.txt", "text")

    if not target_option:
        print("Error: No target option provided. Exiting.")
        return

    # Show what we're using
    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"Form URL: {form_url[:60]}..." if len(form_url) > 60 else f"Form URL: {form_url}")
    print(f"Target option: {target_option[:60]}..." if len(target_option) > 60 else f"Target option: {target_option}")
    print("=" * 60)

    # Get number of requests for THIS SESSION
    print("\n--- SESSION CONFIGURATION ---")
    print(f"Remaining to reach goal: {remaining}")
    while True:
        try:
            requests_input = input(f"Number of requests for this session (1-{remaining}, Enter for all): ").strip()
            if not requests_input:
                requests_this_session = remaining
                break
            requests_this_session = int(requests_input)
            if 1 <= requests_this_session <= remaining:
                break
            else:
                print(f"Please enter a number between 1 and {remaining}.")
        except ValueError:
            print("Please enter a valid number.")

    # Proxy configuration
    print("\n--- PROXY CONFIGURATION ---")
    use_proxies = False

    if os.path.exists('proxies.txt'):
        with open('proxies.txt', 'r', encoding='utf-8') as f:
            proxy_count = len([line.strip() for line in f if line.strip() and not line.strip().startswith('#')])

        if proxy_count > 0:
            print(f"Found {proxy_count} proxies in proxies.txt")
            use_proxies_input = input("Use proxies? (y/N): ").strip().lower()
            use_proxies = use_proxies_input == 'y'
        else:
            print("proxies.txt is empty.")
    else:
        print("proxies.txt not found.")

    # Recreate automator with correct proxy settings
    automator = GoogleFormAutomator(use_proxies=use_proxies)

    # Final confirmation
    print("\n" + "=" * 60)
    print("FINAL CONFIRMATION")
    print("=" * 60)
    print(f"Target option: {target_option[:40]}..." if len(target_option) > 40 else f"Target option: {target_option}")
    print(f"Global progress: {automator.progress_data['completed']}/{automator.progress_data['total_desired']}")
    print(f"This session: {requests_this_session} requests")
    print(
        f"Will be at: {automator.progress_data['completed'] + requests_this_session}/{automator.progress_data['total_desired']} after")
    print(f"Use proxies: {'Yes' if use_proxies else 'No'}")
    if use_proxies:
        print(f"Proxies loaded: {len(automator.proxy_list)}")
    print(f"Log file: log.txt")
    print(f"Progress file: completed_requests.txt")
    print("=" * 60)

    confirm = input("\nStart automation? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return

    # Run automation
    print("\n" + "=" * 60)
    print("STARTING AUTOMATION")
    print("=" * 60)
    print("Press Ctrl+C to stop at any time\n")

    try:
        stats = automator.run_campaign(form_url, target_option, requests_this_session)

        # Display final results
        print("\n" + "=" * 60)
        print("SESSION COMPLETE")
        print("=" * 60)
        total_attempts = stats['success'] + stats['failed']
        if total_attempts > 0:
            print(f"Session attempts: {total_attempts}")
            print(f"Session successful: {stats['success']} ({stats['success'] / total_attempts * 100:.1f}%)")
            print(f"Session failed: {stats['failed']} ({stats['failed'] / total_attempts * 100:.1f}%)")
            print(f"CAPTCHA encounters: {stats['captcha_encountered']}")
            if use_proxies:
                print(f"Proxy rotations: {stats['proxy_rotations']}")
            print(f"Session duration: {stats['duration']}")
        print(f"\nGlobal progress: {automator.progress_data['completed']}/{automator.progress_data['total_desired']}")
        remaining = max(0, automator.progress_data['total_desired'] - automator.progress_data['completed'])
        print(f"Remaining to goal: {remaining}")
        print("=" * 60)
        print(f"\nDetailed log saved to: log.txt")
        print(f"Progress saved to: completed_requests.txt")

        if remaining == 0:
            print("\n🎉 CONGRATULATIONS! Goal reached! 🎉")

    except KeyboardInterrupt:
        print("\n\nAutomation interrupted by user.")
        print(f"Progress saved to: completed_requests.txt")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")


if __name__ == "__main__":
    main()