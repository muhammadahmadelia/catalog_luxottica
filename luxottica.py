import os
import sys
from time import sleep
import json
import glob
from models.product import Product
from models.metafields import Metafields
from models.variant import Variant
from selenium import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
# import pandas as pd
import requests

from openpyxl import Workbook
from openpyxl.drawing.image import Image as Imag
from openpyxl.utils import get_column_letter
from PIL import Image

class Luxottica_Scraper:
    def __init__(self, DEBUG: bool, result_filename: str) -> None:
        self.DEBUG = DEBUG
        self.result_filename = result_filename
        self.chrome_options = Options()
        self.chrome_options.add_argument('--disable-infobars')
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.args = ["hide_console", ]
        self.browser = webdriver.Chrome(options=self.chrome_options, service_args=self.args)
        self.data = []
        pass

    def controller(self, brands: list[dict], url: str, username: str, password: str) -> None:
        try:
            cookies = ''
            dtPC = ''
            self.browser.get(url)
            self.wait_until_browsing()

            if self.login(username, password):
                sleep(10)
                for brand in brands:
                    glasses_types = []
                    if bool(brand["glasses_type"]["sunglasses"]): glasses_types.append("Sunglasses")
                    if bool(brand["glasses_type"]["sunglasses_kids"]): glasses_types.append("Sunglasses Kids")
                    if bool(brand["glasses_type"]["eyeglasses"]): glasses_types.append("Eyeglasses")
                    if bool(brand["glasses_type"]["eyeglasses_kids"]): glasses_types.append("Eyeglasses Kids")
                    if bool(brand["glasses_type"]["snowglasses"]): glasses_types.append("Ski & Snowboard Goggles")

                    for index, glasses_type in enumerate(glasses_types):
                        # self.browser.get(brand_url)
                        brand_url = self.select_category(brand, glasses_type, username, password)
                        # self.wait_until_element_found(40, 'css_selector', 'div[class^="PLPTitle__Section"] > p[class^="CustomText__Text"]')
                        
                        total_products = self.get_total_products_for_brand()
                        
                        print(f'Brand: {brand["brand"]}')
                        print(f'Total products found: {total_products} | Type: {glasses_type}')

                        if int(total_products) > 0:
                            page_number = 1
                            scraped_products = 0

                            while int(scraped_products) != int(total_products):
                                for product_div in self.get_product_divs_on_page():
                                    ActionChains(self.browser).move_to_element(product_div.find_element(By.CSS_SELECTOR, 'div[class^="Tile__SeeAllContainer"] > div > button')).perform()
                                    product_number = str(product_div.get_attribute('data-description')).strip()[1:].upper()
                                    product_name = str(product_div.find_element(By.CSS_SELECTOR, 'div[class^="TileHeader__Header"] > div > span').text).strip().upper()
                                    total_varinats_for_product = str(product_div.find_element(By.CSS_SELECTOR, 'div[class^="Tile__ColorSizeContainer"] > div > span').text).strip()
                                    scraped_products += 1

                                    if self.DEBUG: print(scraped_products, product_number, total_varinats_for_product)
                                    
                                    color_varinats_data = self.get_all_variants(product_div, total_varinats_for_product)
                                    for color_varinat_index, color_varinat_data in enumerate(color_varinats_data):
                                        try:
                                            product = Product()
                                            product.brand = brand['brand']
                                            product.number = str(product_number).strip().upper()
                                            if product.number[0] == '0': product.number = product.number[1:]
                                            product.name = str(product_name).strip().title()

                                            product.frame_code = str(color_varinat_data['frame_code']).strip()
                                            if '/' in product.frame_code: product.frame_code = str(product.frame_code).replace('-', '/')

                                            product.url = str(color_varinat_data['url']).strip()

                                            if product.frame_code and product.url:
                                                if self.DEBUG: print((color_varinat_index + 1), product.frame_code)
                                                self.open_new_tab(product.url)
                                                self.wait_until_browsing()
                                                self.wait_until_element_found(30, 'css_selector', 'div[class^="TileLensInfo__PropertiesContainer"] > div')
                                                
                                                self.get_frame_color(product)
                                                self.get_lens_color(product)
                                                product.status = 'active'
                                                product.type = str(glasses_type).strip().title()
                                                
                                                product.metafields = self.get_metafeilds(str(color_varinat_data['img_url']).strip())
                                                self.get_size_variants(product)

                                                self.close_last_tab()
                                                
                                                if '/' in product.number: product.number = product.number.replace('-', '/')
                                                if '/' in product.frame_code: product.frame_code = product.frame_code.replace('-', '/')
                                                if '/' in product.lens_code: product.lens_code = product.lens_code.replace('-', '/')

                                                self.data.append(product)
                                                self.save_to_json(self.data)
                                        except Exception as e:
                                            if self.DEBUG: print(f'Exception in variants loop: {e}')
                                            else: pass

                                if int(scraped_products) < int(total_products):
                                    page_number += 1
                                    self.move_to_next_page(brand_url, page_number)
                                    self.wait_until_element_found(40, 'css_selector', 'div[class^="PLPTitle__Section"] > p[class^="CustomText__Text"]')
                                    total_products = self.get_total_products_for_brand()
                                else: break
                            
            else: print(f'Failed to login \nURL: {self.URL}\nUsername: {str(username)}\nPassword: {str(password)}')
        except Exception as e:
            if self.DEBUG: print(f'Exception in Luxottica_All_Scraper controller: {e}')
            else: pass
        finally: 
            self.browser.quit()

    def wait_until_browsing(self) -> None:
        while True:
            try:
                state = self.browser.execute_script('return document.readyState; ')
                if 'complete' == state: break
                else: sleep(0.2)
            except: pass
    
    def wait_until_element_found(self, wait_value: int, type: str, value: str) -> bool:
        flag = False
        try:
            if type == 'id':
                WebDriverWait(self.browser, wait_value).until(EC.presence_of_element_located((By.ID, value)))
                flag = True
            elif type == 'xpath':
                WebDriverWait(self.browser, wait_value).until(EC.presence_of_element_located((By.XPATH, value)))
                flag = True
            elif type == 'css_selector':
                WebDriverWait(self.browser, wait_value).until(EC.presence_of_element_located((By.CSS_SELECTOR, value)))
                flag = True
            elif type == 'class_name':
                WebDriverWait(self.browser, wait_value).until(EC.presence_of_element_located((By.CLASS_NAME, value)))
                flag = True
            elif type == 'tag_name':
                WebDriverWait(self.browser, wait_value).until(EC.presence_of_element_located((By.TAG_NAME, value)))
                flag = True
        except: pass
        finally: return flag

    def accept_cookies_before_login(self) -> None:
        try:
            if self.wait_until_element_found(5, 'css_selector', 'div[class^="CookiesBanner__SecondButtonWrap"] > button'):
                self.browser.find_element(By.CSS_SELECTOR, 'div[class^="CookiesBanner__SecondButtonWrap"] > button').click()
                sleep(0.3)
        except Exception as e:
            self.logs.append(f'Exception in accept_cookies_before_login: {str(e)}')
            if self.DEBUG: print(f'Exception in accept_cookies_before_login: {str(e)}')
            else: pass

    def accept_cookies_after_login(self) -> None:
        try:
            if self.wait_until_element_found(5, 'css_selector', 'div[class^="CookiesContent__Container"] > div > button[class$="underline"]'):
                btn = self.browser.find_element(By.CSS_SELECTOR, 'div[class^="CookiesContent__Container"] > div > button[class$="underline"]')
                ActionChains(self.browser).move_to_element(btn).click().perform()
                sleep(0.3)
        except Exception as e:
            self.logs.append(f'Exception in accept_cookies_after_login: {str(e)}')
            if self.DEBUG: print(f'Exception in accept_cookies_after_login: {str(e)}')
            else: pass

    def login(self, username: str, password: str) -> bool:
        login_flag = False
        while not login_flag:
            try:
                self.accept_cookies_before_login()
                if self.wait_until_element_found(10, 'xpath', '//input[@id="signInName"]'):
                    for _ in range(0, 30):
                        try:
                            self.browser.find_element(By.XPATH, '//input[@id="signInName"]').send_keys(username)
                            break
                        except: sleep(0.3)
                    sleep(0.2)
                    
                    if self.wait_until_element_found(20, 'xpath', '//button[@id="continue"]'):
                        for _ in range(0, 30):
                            try:
                                self.browser.find_element(By.XPATH, '//button[@id="continue"]').click()
                                break
                            except: sleep(0.3)

                        if self.wait_until_element_found(20, 'xpath', '//input[@id="password"]'):
                            for _ in range(0, 30):
                                try:
                                    self.browser.find_element(By.XPATH, '//input[@id="password"]').send_keys(password)
                                    break
                                except: sleep(0.5)
                            sleep(0.2)
                            self.browser.find_element(By.XPATH, '//button[@id="next"]').click()
                            self.wait_until_browsing()
                            for _ in range(0, 100):
                                try:
                                    a = self.browser.find_element(By.CSS_SELECTOR, 'div[class^="AccountMenu__MenuContainer"]')
                                    if a: 
                                        login_flag = True
                                        if '/myl-it/it-IT/homepage' in self.browser.current_url:
                                            self.browser.get('https://my.essilorluxottica.com/myl-it/en-GB/homepage')
                                        self.accept_cookies_after_login()
                                        break
                                    else: sleep(0.3)
                                except: sleep(0.3)
                        else: print('Password input not found')
                else: print('Email input not found')
            except Exception as e:
                self.print_logs(f'Exception in login: {str(e)}')
                if self.DEBUG: print(f'Exception in login: {str(e)}')

            if not login_flag: 
                self.browser.get(url)
                self.wait_until_browsing()
        return login_flag

    def open_new_tab(self, url: str) -> None:
        # open category in new tab
        self.browser.execute_script('window.open("'+str(url)+'","_blank");')
        self.browser.switch_to.window(self.browser.window_handles[len(self.browser.window_handles) - 1])
        self.wait_until_browsing()
    
    def select_category(self, brand: dict, glasses_type: str, username: str, password: str) -> str:
        brand_url = ''
        for _ in range(0, 10):
            try:
                url = ''
                if str(brand["brand"]).strip().lower() == 'arnette':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/arnette'
                elif str(brand["brand"]).strip().lower() == 'burberry':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/burberry'
                elif str(brand["brand"]).strip().lower() == 'bvlgari':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/bvlgari'
                elif str(brand["brand"]).strip().lower() == 'dolce & gabbana':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/dolce-gabbana'
                elif str(brand["brand"]).strip().lower() == 'ess':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/ess'
                elif str(brand["brand"]).strip().lower() == 'emporio armani':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/emporio-armani'
                elif str(brand["brand"]).strip().lower() == 'giorgio armani':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/giorgio-armani'
                elif str(brand["brand"]).strip().lower() == 'luxottica':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/luxottica'
                elif str(brand["brand"]).strip().lower() == 'michael kors':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/michael-kors'
                elif str(brand["brand"]).strip().lower() == 'oakley':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/oakley'
                elif str(brand["brand"]).strip().lower() == 'persol':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/persol'
                elif str(brand["brand"]).strip().lower() == 'polo ralph lauren':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/polo-ralph-lauren'
                elif str(brand["brand"]).strip().lower() == 'prada':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/prada'
                elif str(brand["brand"]).strip().lower() == 'prada linea rossa':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/prada-linea-rossa'
                elif str(brand["brand"]).strip().lower() == 'ralph':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/ralph'
                elif str(brand["brand"]).strip().lower() == 'ralph lauren':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/ralph-lauren'
                elif str(brand["brand"]).strip().lower() == 'ray-ban':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/ray-ban'
                elif str(brand["brand"]).strip().lower() == 'sferoflex':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/sferoflex'
                elif str(brand["brand"]).strip().lower() == 'valentino':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/valentino'
                elif str(brand["brand"]).strip().lower() == 'versace':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/versace'
                elif str(brand["brand"]).strip().lower() == 'vogue':
                    url = 'https://my.essilorluxottica.com/myl-it/en-GB/preplp/vogue'
                
                if url and self.browser.current_url == 'https://my.essilorluxottica.com/myl-it/en-GB/homepage' or 'https://my.essilorluxottica.com/myl-it/en-GB/plp/frames' in self.browser.current_url:
                    self.wait_until_element_found(30, 'xpath', "//span/button[contains(text(),'BRANDS')]")
                    ActionChains(self.browser).move_to_element(self.browser.find_element(By.XPATH, "//span/button[contains(text(),'BRANDS')]")).perform()
                    sleep(0.5)
                    self.browser.get(url)
                    self.wait_until_browsing()
                    sleep(5)

                if self.browser.current_url == 'https://my.essilorluxottica.com/en-GB/login':
                    for _ in range(0, 30):
                        try:
                            if self.wait_until_element_found(5, 'xpath', '//input[@name="username"]'):
                                self.browser.find_element(By.XPATH, '//input[@name="username"]')
                                if self.login(username, password):
                                    sleep(10)
                                    break
                                else: sleep(0.4)
                            elif self.wait_until_element_found(5, 'xpath', 'button[data-element-id^="Categories_sunglasses_ViewAll"]'): break
                        except: sleep(0.5)

                # print(self.browser.current_url, url, self.browser.current_url == url)
                if self.browser.current_url == url:
                    category_css_selector = ''
                    if glasses_type == 'Sunglasses':
                        category_css_selector = 'button[data-element-id^="Categories_sunglasses_"]'
                    if glasses_type == 'Sunglasses Kids':
                        category_css_selector = 'button[data-element-id^="Categories_sunglasses-kids"]'
                    elif glasses_type == 'Eyeglasses':
                        category_css_selector = 'button[data-element-id^="Categories_eyeglasses_"]'
                    elif glasses_type == 'Eyeglasses Kids':
                        category_css_selector = 'button[data-element-id^="Categories_eyeglasses-kids"]'
                    elif glasses_type == 'Ski & Snowboard Goggles':
                        category_css_selector = 'button[data-element-id^="Categories_gogglesHelmets"]'
                    # print(category_css_selector)
                    
                    self.wait_until_element_found(20, 'css_selector', category_css_selector)
                    element = self.browser.find_element(By.CSS_SELECTOR, category_css_selector)
                    ActionChains(self.browser).move_to_element(element).perform()
                    sleep(0.5)
                    ActionChains(self.browser).move_to_element(element).click().perform()
                    sleep(0.4)

                    for _ in range(0, 100):
                        try:
                            value = str(self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PLPTitle__Section"] > p[class^="CustomText__Text"]').text).strip()
                            if '(' in value or ')' in value: break
                        except: sleep(0.5)

                    brand_url = self.browser.current_url
                    break
                
                
            except Exception as e:
                if self.DEBUG: print(f'Exception in select_category: {e}')
                else: pass
        return brand_url

    def close_last_tab(self) -> None:
        self.browser.close()
        self.browser.switch_to.window(self.browser.window_handles[len(self.browser.window_handles) - 1])

    def get_total_products_for_brand(self) -> int:
        total_products = 0
        try:
            for _ in range(0, 200):
                try:
                    total_sunglasses = str(self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PLPTitle__Section"] > p[class^="CustomText__Text"]').text).strip()
                    if '(' in total_sunglasses:
                        # if 'Sunglasses' in total_sunglasses: 
                        #     total_sunglasses = total_sunglasses.replace('Sunglasses', '').replace('(', '').replace(')', '').strip()
                        # elif 'Eyeglasses' in total_sunglasses: 
                        #     total_sunglasses = total_sunglasses.replace('Eyeglasses', '').replace('(', '').replace(')', '').strip()
                        # elif 'Goggles and helmets' in total_sunglasses: 
                        #     total_sunglasses = total_sunglasses.replace('Goggles and helmets', '').replace('(', '').replace(')', '').strip()
                        total_sunglasses = total_sunglasses.split('(')[-1].strip().replace(')', '').strip()
                        if total_sunglasses: total_products = int(total_sunglasses)
                        else: total_products = 0
                        break
                    else: sleep(0.3)
                except: 
                    try:
                        text = str(self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PLPGeneric__MainColumn"] > div > p').text).strip()
                        if 'Sorry, there are no products' in text: break
                        else: sleep(0.3)
                    except: sleep(0.3)
        except Exception as e:
            if self.DEBUG: print(f'Exception in get_total_products_and_pages: {str(e)}')
            else: pass
        finally: return total_products

    def get_product_divs_on_page(self) -> list:
        product_divs = []
        for _ in range(0, 30):
            try:
                product_divs = self.browser.find_elements(By.CSS_SELECTOR, 'div[data-element-id="Tiles"] > div[class^="Tile"]')
                for product_div in product_divs:
                    product_number = str(product_div.get_attribute('data-description')).strip()
                    product_name = str(product_div.find_element(By.CSS_SELECTOR, 'div[class^="TileHeader__Header"] > div > span').text).strip()
                    total_varinats_for_product = str(product_div.find_element(By.CSS_SELECTOR, 'div[class^="Tile__ColorSizeContainer"] > div > span').text).strip()
                break
            except: sleep(0.2)
        return product_divs

    def get_all_variants(self, div, nbr_of_varinats: str) -> list[dict]:
        variants = []
        try:
            self.open_variants_box(div)
            self.go_back_to_first_variant()
            while len(variants) < int(nbr_of_varinats):
                try:
                    new_variants = self.get_variants_data()
                    for new_variant in new_variants:
                        if new_variant not in variants: variants.append(new_variant)
                    if new_variants: self.move_to_next_varinats_grid()
                except:
                    sleep(0.3)
            self.browser.find_element(By.CSS_SELECTOR, 'div[class="icon-container"] > div[class^="IconButton__Container"] > button').click()
        except Exception as e:
            if self.DEBUG: print(f'Exception in get_variants: {str(e)}')
            else: pass
        finally: return variants

    def get_variants_data(self):
        variants = []
        for _ in range(0, 30):
            try:
                variants_divs = self.browser.find_elements(By.CSS_SELECTOR, 'div[data-element-id="Variants"]')
                if len(variants_divs) == 2:
                    variants_grids = variants_divs[1].find_elements(By.CSS_SELECTOR, 'div[class^="ExpandedTile__TilesSection"] > div')
                            
                    for variants_grid in variants_grids:
                        frame_code, url, img_url = '', '', ''
                        sizes = []
                        inner_divs = variants_grid.find_elements(By.CSS_SELECTOR, 'div[class^="Tile__StyledTile"] > div')
                        
                        try:frame_code = str(inner_divs[0].find_element(By.CSS_SELECTOR, 'div[class^="TileHeader__Header"] > div > button').text).strip().replace('/', '-')
                        except: pass

                        try:
                            for _ in range(0, 40):
                                for _ in range(0, 20):
                                    try: 
                                        inner_divs[0].find_element(By.CSS_SELECTOR, 'a[class^="Tile__ImageContainer"] > img').get_attribute('src')
                                        break
                                    except: sleep(0.1)
                                img_url = str(inner_divs[0].find_element(By.CSS_SELECTOR, 'a[class^="Tile__ImageContainer"] > img').get_attribute('src'))
                                if '/static/media/placeholder' not in img_url: break
                                else: sleep(0.3)
                        except: pass


                        try: url = str(variants_grid.find_element(By.CSS_SELECTOR, 'a[class^="Tile__ImageContainer"]').get_attribute('href')).strip()
                        except: pass
                        if frame_code and url:
                            json_data = { 'frame_code': frame_code, 'url': url, 'img_url': img_url }
                            if json_data not in variants:
                                variants.append(json_data)
                    break
            except:
                sleep(0.3)
        return variants

    def open_variants_box(self, div) -> None:
        for _ in range(0, 30):
            try:
                variants_divs = self.browser.find_elements(By.CSS_SELECTOR, 'div[data-element-id="Variants"]')
                if len(variants_divs) != 2:
                    div.find_element(By.CSS_SELECTOR, 'div[class^="Tile__SeeAllContainer"] > div > button').click()
                else: break
            except: sleep(0.3)

    def go_back_to_first_variant(self) -> None:
        while self.is_css_selector_found('div[class^="CarouselNavBar__PrevButtonLateral"]'):
            try:
                prev_btn_div = self.browser.find_element(By.CSS_SELECTOR, 'div[class^="CarouselNavBar__PrevButtonLateral"]')
                prev_btn_div.find_element(By.TAG_NAME, 'button').click()
                sleep(0.5)
            except: pass
    
    def is_css_selector_found(self, css_selector) -> bool:
        try:
            self.browser.find_element(By.CSS_SELECTOR, css_selector)
            return True
        except: return False

    def move_to_next_varinats_grid(self) -> None:
        for _ in range(0, 30):
            try:
                variants_divs = self.browser.find_elements(By.CSS_SELECTOR, 'div[data-element-id="Variants"]')
                btn = variants_divs[1].find_elements(By.CSS_SELECTOR, 'div[class^="IconButton__Container"] > button')[1]
                if 'button-out-of-stock' in btn.get_attribute('class'): break
                else: 
                    btn.click()
                    for _ in range(0, 30):
                        try:
                            variants_divs = self.browser.find_elements(By.CSS_SELECTOR, 'div[data-element-id="Variants"]')
                            if len(variants_divs) == 2:
                                variants_grids = variants_divs[1].find_elements(By.CSS_SELECTOR, 'div[class^="ExpandedTile__TilesSection"] > div')
                                if len(variants_grids) > 0: break
                        except: sleep(0.3)
                    break
            except: pass

    def get_frame_color(self, product: Product) -> None:
        for _ in range(0, 40):
            try:
                product.frame_color = str(self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PDPVariantColumn__ProductModel"] > span').text).strip()
                if product.frame_color: product.frame_color = str(product.frame_color).lower().replace(str(product.frame_code).strip().lower().replace('-', '/'), '').strip()
                if product.frame_color[0] == '-': product.frame_color = str(product.frame_color[1:]).strip().title()
                else: product.frame_color = str(product.frame_color).strip().title()
            except: 
                try:
                    for div in self.browser.find_elements(By.CSS_SELECTOR, 'div[class^="TileLensInfo__PropertiesContainer"] > div'):
                        if 'color' in str(div.find_element(By.TAG_NAME, 'p').text).strip().lower():
                            product.frame_color = str(div.find_element(By.TAG_NAME, 'span').text).strip().title()
                            break
                except: sleep(0.1)
            if product.frame_color: break

    def get_lens_color(self, product: Product):
        for _ in range(0, 30):
            try:
                for div in self.browser.find_elements(By.CSS_SELECTOR, 'div[class^="TileLensInfo__PropertiesContainer"] > div'):
                        if 'lens color' in str(div.find_element(By.TAG_NAME, 'p').text).strip().lower():
                            product.lens_color = str(div.find_element(By.TAG_NAME, 'span').text).strip().title()
                            break
            except: sleep(0.1)
            if product.lens_color: break

    def get_metafeilds(self, img_url: str) -> Metafields:
        metafields = Metafields()
        
        if not img_url or '/static/media/placeholder' in img_url: self.get_image_url(metafields)
        else: metafields.img_url = img_url

        # if metafields.img_url: self.get_360_images(metafields)
        
        # for _ in range(0, 50):
        try:
            lens_sun_feature, polarized, photochromic = '', '', ''
            for div in self.browser.find_elements(By.CSS_SELECTOR, 'div[class^="PDPProductDetails__DetailLine"]'):
                spans = div.find_elements(By.TAG_NAME, 'span')
                if 'front material' in str(spans[0].text).strip().lower():
                    metafields.frame_material = str(spans[1].text).strip().title()
                elif 'shape' in str(spans[0].text).strip().lower():
                    metafields.frame_shape = str(spans[1].text).strip().title()
                elif 'gender' in str(spans[0].text).strip().lower():
                    metafields.for_who = str(spans[1].text).strip().title()
                elif 'lens material' in str(spans[0].text).strip().lower():
                    metafields.lens_material = str(spans[1].text).strip().title()
                elif 'lens sun feature' in str(spans[0].text).strip().lower():
                    lens_sun_feature = str(spans[1].text).strip().title()
                elif 'polarized' in str(spans[0].text).strip().lower():
                    polarized = str(spans[1].text).strip()
                elif 'photochromic' in str(spans[0].text).strip().lower():
                    photochromic = str(spans[1].text).strip()

            if ',' in polarized: polarized = str(polarized).split(',')[0].strip()

            if str(photochromic).strip().lower() == 'false' and str(polarized).strip().lower() == 'false':
                metafields.lens_technology = str(lens_sun_feature).strip().title()
            else:
                if str(photochromic).strip().lower() == 'true' and str(polarized).strip().lower() == 'true':
                    metafields.lens_technology = 'Photochromic Polarized'
                elif str(photochromic).strip().lower() == 'true' and str(polarized).strip().lower() == 'false':
                    metafields.lens_technology = 'Photochromic'
                elif str(photochromic).strip().lower() == 'false' and str(polarized).strip().lower() == 'true':
                    metafields.lens_technology = 'Polarized'
            # break
        except: pass
                # try: ActionChains(self.browser).move_to_element(self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PDPProductDetails__DetailLine"]')).perform()
                # except: pass
                # sleep(0.3)
        
        return metafields

    def get_image_url(self, metafields: Metafields) -> None:
        for _ in range(0, 30):
            try:
                metafields.img_url = self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PDPGlassesColumn__ImageContainer"]').find_element(By.TAG_NAME, 'img').get_attribute('src')
                if '/static/media/placeholder' not in metafields.img_url:
                    sleep(1)
                    metafields.img_url = str(metafields.img_url).strip()
                    break
                else: sleep(0.1)
            except: sleep(0.1)

    def get_360_images(self, metafields: Metafields) -> None:
        flag = False
        if self.wait_until_element_found(2, 'css_selector', 'button[data-description="360° view"]'):
            flag = False
            for _ in range(0, 40):
                try:
                    button = self.browser.find_element(By.CSS_SELECTOR, 'button[data-description="360° view"]')
                    ActionChains(self.browser).move_to_element(self.browser.find_element(By.CSS_SELECTOR, 'div[class^="AccordionSection__AccordionTitle"]')).perform()
                    button.click()
                    sleep(0.5)
                    flag = True
                    break
                except: sleep(0.2)
            if flag:
                image_tags = []
                for _ in range(0, 40):
                    try:
                        image_tags = self.browser.find_elements(By.CSS_SELECTOR, 'div[class^="View360Popup__ImageContainer"] > img')
                        if len(image_tags) >= 12: break
                    except: sleep(0.2)
                if image_tags:
                    for img_tag in image_tags: metafields.img_360_urls = str(img_tag.get_attribute('src')).strip()

                for _ in range(0, 40):
                    try:
                        self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PopupInElement__Container"]')
                        break
                    except: 
                        try: ActionChains(self.browser).move_to_element(self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PopupInElement__Container"]')).perform()
                        except: sleep(0.2)
            
    def get_size_variants(self, product: Product) -> None:
        for _ in range(0, 20):
            try:
                for index, div in enumerate(self.browser.find_elements(By.CSS_SELECTOR, 'div[class^="SizeContainer__AddSizeContainer"]')):
                    variant = Variant()
                    variant.position = (index + 1)
                    try: variant.title = str(div.find_element(By.CSS_SELECTOR, 'div[class^="AddSize__SizeValue"]').text).strip()
                    except: pass
                    variant.sku = f'{product.number} {product.frame_code} {variant.title}'
                    if '-' in variant.sku: variant.sku = str(variant.sku).replace('-', '/')
                    try:
                        src = div.find_element(By.CSS_SELECTOR, 'div[class^="Tooltip__StyledContainer"] > div[class^="AvailabilityStatus"] > img').get_attribute('src')
                        if '/Green.' in src: variant.inventory_quantity = 1
                        else: variant.inventory_quantity = 0
                    except: pass
                    variant.found_status = 1
                    try: variant.listing_price = str(self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PriceTile__ContainerAlignLeft"] > span[color="primary"]').text).strip().replace('€', '')
                    except: pass
                    try: variant.wholesale_price = str(self.browser.find_element(By.CSS_SELECTOR, 'div[class^="PriceTile__ContainerAlignRight"] > span[color="primary"]').text).strip().replace('€', '')
                    except: pass
                    product.variants = variant
                break
            except: sleep(0.1)

    def move_to_next_page(self, brand_url: str, page_number: int) -> None:
        self.browser.get(f'{brand_url}&pageNumber={page_number}')
        self.wait_until_browsing()
        sleep(0.8)

    def save_to_json(self, products: list[Product]):
        try:
            json_products = []
            for product in products:
                json_varinats = []
                for index, variant in enumerate(product.variants):
                    json_varinat = {
                        'position': (index + 1), 
                        'title': variant.title, 
                        'sku': variant.sku, 
                        'inventory_quantity': variant.inventory_quantity,
                        'found_status': variant.found_status,
                        'wholesale_price': variant.wholesale_price,
                        'listing_price': variant.listing_price, 
                        'barcode_or_gtin': variant.barcode_or_gtin,
                        'size': variant.size,
                        'weight': variant.weight
                    }
                    json_varinats.append(json_varinat)
                json_product = {
                    'brand': product.brand, 
                    'number': product.number, 
                    'name': product.name, 
                    'frame_code': product.frame_code, 
                    'frame_color': product.frame_color, 
                    'lens_code': product.lens_code, 
                    'lens_color': product.lens_color, 
                    'status': product.status, 
                    'type': product.type, 
                    'url': product.url, 
                    'metafields': [
                        { 'key': 'for_who', 'value': product.metafields.for_who },
                        { 'key': 'product_size', 'value': product.metafields.product_size }, 
                        { 'key': 'lens_material', 'value': product.metafields.lens_material }, 
                        { 'key': 'lens_technology', 'value': product.metafields.lens_technology }, 
                        { 'key': 'frame_material', 'value': product.metafields.frame_material }, 
                        { 'key': 'frame_shape', 'value': product.metafields.frame_shape },
                        { 'key': 'gtin1', 'value': product.metafields.gtin1 }, 
                        { 'key': 'img_url', 'value': product.metafields.img_url }
                    ],
                    'variants': json_varinats
                }
                json_products.append(json_product)
        
        
            with open(self.result_filename, 'w') as f: json.dump(json_products, f)
            
        except Exception as e:
            if self.DEBUG: print(f'Exception in save_to_json: {e}')
            else: pass

def read_data_from_json_file(DEBUG, result_filename: str):
    data = []
    try:
        files = glob.glob(result_filename)
        if files:
            f = open(files[-1])
            json_data = json.loads(f.read())
            products = []

            for json_d in json_data:
                number, frame_code, brand, img_url, frame_color, lens_color = '', '', '', '', '', ''
                # product = Product()
                brand = json_d['brand']
                number = str(json_d['number']).strip().upper()
                if '/' in number: number = number.replace('/', '-').strip()
                # product.name = str(json_d['name']).strip().upper()
                frame_code = str(json_d['frame_code']).strip().upper()
                if '/' in frame_code: frame_code = frame_code.replace('/', '-').strip()
                frame_color = str(json_d['frame_color']).strip().title()
                # product.lens_code = str(json_d['lens_code']).strip().upper()
                lens_color = str(json_d['lens_color']).strip().title()
                # product.status = str(json_d['status']).strip().lower()
                # product.type = str(json_d['type']).strip().title()
                # product.url = str(json_d['url']).strip()
                # metafields = Metafields()
                
                for json_metafiels in json_d['metafields']:
                    # if json_metafiels['key'] == 'for_who':metafields.for_who = str(json_metafiels['value']).strip().title()
                    # elif json_metafiels['key'] == 'product_size':metafields.product_size = str(json_metafiels['value']).strip().title()
                    # elif json_metafiels['key'] == 'activity':metafields.activity = str(json_metafiels['value']).strip().title()
                    # elif json_metafiels['key'] == 'lens_material':metafields.lens_material = str(json_metafiels['value']).strip().title()
                    # elif json_metafiels['key'] == 'graduabile':metafields.graduabile = str(json_metafiels['value']).strip().title()
                    # elif json_metafiels['key'] == 'interest':metafields.interest = str(json_metafiels['value']).strip().title()
                    # elif json_metafiels['key'] == 'lens_technology':metafields.lens_technology = str(json_metafiels['value']).strip().title()
                    # elif json_metafiels['key'] == 'frame_material':metafields.frame_material = str(json_metafiels['value']).strip().title()
                    # elif json_metafiels['key'] == 'frame_shape':metafields.frame_shape = str(json_metafiels['value']).strip().title()
                    # elif json_metafiels['key'] == 'gtin1':metafields.gtin1 = str(json_metafiels['value']).strip().title()
                    if json_metafiels['key'] == 'img_url':img_url = str(json_metafiels['value']).strip()
                    # elif json_metafiels['key'] == 'img_360_urls':
                    #     value = str(json_metafiels['value']).strip()
                    #     if '[' in value: value = str(value).replace('[', '').strip()
                    #     if ']' in value: value = str(value).replace(']', '').strip()
                    #     if "'" in value: value = str(value).replace("'", '').strip()
                    #     for v in value.split(','):
                    #         metafields.img_360_urls = str(v).strip()
                # product.metafields = metafields
                for json_variant in json_d['variants']:
                    sku, price = '', ''
                    # variant = Variant()
                    # variant.position = json_variant['position']
                    # variant.title = str(json_variant['title']).strip()
                    sku = str(json_variant['sku']).strip().upper()
                    if '/' in sku: sku = sku.replace('/', '-').strip()
                    # variant.inventory_quantity = json_variant['inventory_quantity']
                    # variant.found_status = json_variant['found_status']
                    wholesale_price = str(json_variant['wholesale_price']).strip()
                    listing_price = str(json_variant['listing_price']).strip()
                    # variant.barcode_or_gtin = str(json_variant['barcode_or_gtin']).strip()
                    # variant.size = str(json_variant['size']).strip()
                    # variant.weight = str(json_variant['weight']).strip()
                    # product.variants = variant
                    img_url = img_url.replace('impolicy=MYL_EYE&wid=262', 'impolicy=MYL_EYE&wid=600')
                    image_filename = f'Images/{sku.replace("/", "_")}.jpg'
                    if not os.path.exists(image_filename):
                        image_attachment = download_image(img_url)
                        if image_attachment:
                            with open(image_filename, 'wb') as f: f.write(image_attachment)
                    data.append([number, frame_code, frame_color, lens_color, brand, sku, wholesale_price, listing_price])
    except Exception as e:
        if DEBUG: print(f'Exception in read_data_from_json_file: {e}')
        else: pass
    finally: return data

def download_image(url):
    image_attachment = ''
    try:
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-Encoding': 'gzip, deflate, br',
            'accept-Language': 'en-US,en;q=0.9',
            'cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'Sec-Fetch-User': '?1',
            'upgrade-insecure-requests': '1',
        }
        counter = 0
        while True:
            try:
                response = requests.get(url=url, headers=headers, timeout=20)
                if response.status_code == 200:
                    # image_attachment = base64.b64encode(response.content)
                    image_attachment = response.content
                    break
                else: print(f'{response.status_code} found for downloading image')
            except: sleep(0.3)
            counter += 1
            if counter == 10: break
    except Exception as e: print(f'Exception in download_image: {str(e)}')
    finally: return image_attachment

def saving_picture_in_excel(data: list):
    try:
        workbook = Workbook()
        worksheet = workbook.active

        worksheet.cell(row=1, column=1, value='Model Code')
        worksheet.cell(row=1, column=2, value='Lens Code')
        worksheet.cell(row=1, column=3, value='Color Frame')
        worksheet.cell(row=1, column=4, value='Color Lens')
        worksheet.cell(row=1, column=5, value='Brand')
        worksheet.cell(row=1, column=6, value='SKU')
        worksheet.cell(row=1, column=7, value='Wholesale Price')
        worksheet.cell(row=1, column=8, value='Listing Price')
        worksheet.cell(row=1, column=9, value="Image")

        for index, d in enumerate(data):
            new_index = index + 2
            worksheet.cell(row=new_index, column=1, value=d[0])
            worksheet.cell(row=new_index, column=2, value=d[1])
            worksheet.cell(row=new_index, column=3, value=d[2])
            worksheet.cell(row=new_index, column=4, value=d[3])
            worksheet.cell(row=new_index, column=5, value=d[4])
            worksheet.cell(row=new_index, column=6, value=d[5])
            worksheet.cell(row=new_index, column=7, value=d[6])
            worksheet.cell(row=new_index, column=8, value=d[7])
            
            image = f'Images/{str(d[-3]).replace("/", "_")}.jpg'
            if os.path.exists(image):
                try:
                    im = Image.open(image)
                    # if image is WebP save it as JPEG and open it again
                    if im.format_description == 'WebP image':
                        im.convert("RGB")
                        im.save(image, "jpeg")
                        im = Image.open(image)
                        
                    width, height = im.size
                    worksheet.row_dimensions[new_index].height = height
                    worksheet.add_image(Imag(image), anchor='I'+str(new_index))
                    
                except: pass
                
        
        workbook.save('Luxottica Results.xlsx')
    except Exception as e: print(f'Exception in saving_picture_in_excel: {str(e)}')   


DEBUG = True
try:
    pathofpyfolder = os.path.realpath(sys.argv[0])
    # get path of Exe folder
    path = pathofpyfolder.replace(pathofpyfolder.split('\\')[-1], '')
    # download chromedriver.exe with same version and get its path
    if os.path.exists('chromedriver.exe'): os.remove('chromedriver.exe')
    if os.path.exists('Luxottica Results.xlsx'): os.remove('Luxottica Results.xlsx')

    chromedriver_autoinstaller.install(path)
    if '.exe' in pathofpyfolder.split('\\')[-1]: DEBUG = False
    
    f = open('Luxottica start.json')
    json_data = json.loads(f.read())
    f.close()

    brands = json_data['brands']

    
    f = open('requirements/luxottica.json')
    data = json.loads(f.read())
    f.close()
    url = data['url']
    username = data['username']
    password = data['password']

    result_filename = 'requirements/Luxottica Results.json'
    Luxottica_Scraper(DEBUG, result_filename).controller(brands, url, username, password)
    
    for filename in glob.glob('Images/*'): os.remove(filename)
    data = read_data_from_json_file(DEBUG, result_filename)
    os.remove(result_filename)

    saving_picture_in_excel(data)
except Exception as e:
    if DEBUG: print('Exception: '+str(e))
    else: pass