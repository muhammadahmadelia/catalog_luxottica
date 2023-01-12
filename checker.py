import requests
import json
import threading
from time import sleep
import glob

from concurrent.futures import ThreadPoolExecutor
from functools import partial

def get_headers(referer: str) -> dict:
    return {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': 'TS01b8fd87=01ccc2acf4b80080e6933b35aebd0d9138df40205fa96df45a40c2a4451d5af9e671162155cabb14ed6b544354d96f3b9bab7edd98; myl_frontoffice_sessionid=37b6eadf-694d-4577-856d-3864277cfea2; dtCookie=v_4_srv_7_sn_AF3B8F9BBA76350D659DDA854F361279_perc_100000_ol_0_mul_1_app-3Af21c670710308fe3_1; TS012ae825=01ccc2acf4b80080e6933b35aebd0d9138df40205fa96df45a40c2a4451d5af9e671162155cabb14ed6b544354d96f3b9bab7edd98; rxVisitor=1666984436075HLDS1BK0IN07H15OMKB9UHDK8I7TB3D3; dtSa=-; tealium_data2track_Tags_AdobeAnalytics_TrafficSourceMid_ThisHit=direct; tealium_data_tags_adobeAnalytics_trafficSourceMid_thisSession=direct; tealium_data_session_timeStamp=1666984438667; AMCVS_125138B3527845350A490D4C%40AdobeOrg=1; s_cc=true; myluxottica-cookie-accept=All; _shek.0001009076.it=ALL_PRICES; _ga=GA1.3.1795283846.1666984460; _gid=GA1.3.1194749263.1666984460; AMCV_125138B3527845350A490D4C%40AdobeOrg=-1303530583%7CMCIDTS%7C19294%7CMCMID%7C89784603461379300922115057393237125863%7CMCAAMLH-1667589269%7C6%7CMCAAMB-1667589269%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1666991639s%7CNONE%7CMCAID%7CNONE%7CMCSYNCSOP%7C411-19301%7CvVersion%7C3.3.0%7CMCCIDH%7C1673399632; MoodleSession=i24msrb8ma62k5pegsmplbsit1; TS011703df=011f6f69ca2cd925d411b6f9e62e126ca71d00c46978190248a03aa1c16cd3a4c8b1970459fa23201acca1873385077ada414c88ceea0066c201f3d11393faa15e2478e1ef; ak_bmsc=4E23819F3AB79B6FE77DA2861CA8BD86~000000000000000000000000000000~YAAQB77XFz5YmOeDAQAAeLgEIBE0Evvuu6CvEArw5XsjipA1N3KcAh91IRDEt0TaPz5953oggy6c+a91moCf43573T2VAuAYFvwRItshr+OS7V2lqCUFxmgYhw3l2MdT3c8lGy8BT5okWhm6FQQ+1bZ3MVJkzPbIbtfgrSGtTfgn8fjNBgs+fdPSNWHVmd3K+aLtDbP0TeDgNEEvpEkcJpc9TgQdQocab7dK7TwTY+vVFP2Y3ZfCf1/0SvhLK+Jp/ESwfNqmAA1u6GFj9MplVVLAGAV1kGD+vsOoj1DhHN3jJK7p4JA+4KRst2Beyl7wW+OC5OLSboZeHfFQDVZcxktbnjzOZMyAEtJm9TULQpNYuwtNW1j2GN3C8NFw9q3hijLbtEIEnsqKDLnPbqfCVo9kLPw=; mylToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IjRRVDljTDlLWF9pVnViNHc3RXZ3UWlmUVNCYjFHZC00MDRuclc2c0lfaTQifQ.eyJpc3MiOiJodHRwczovL2xvbXlsMjBiMmNwMDEuYjJjbG9naW4uY29tLzk5YTE2MmZhLTkyMDctNDhkNC05NGRkLThiM2NjNWExNDM0MS92Mi4wLyIsImV4cCI6MTY2Njk4ODExNywibmJmIjoxNjY2OTg0NTE3LCJhdWQiOiIzYmQ1Yjk1Yy1kNjg1LTRhZTAtOGM2Ni1iNDdhM2VlNGYxOGQiLCJvaWQiOiIyOTc5OTlkMy1jYjBhLTRiNjctOGIxMy0zM2FhMzVmYWZjZjAiLCJ1cG4iOiJzaGVrLjAwMDEwMDkwNzYuaXRAbG9teWwyMGIyY3AwMS5vbm1pY3Jvc29mdC5jb20iLCJzdWIiOiJOb3Qgc3VwcG9ydGVkIGN1cnJlbnRseS4gVXNlIG9pZCBjbGFpbS4iLCJuYW1lIjoiTmljY28gU2NyYXAiLCJnaXZlbl9uYW1lIjoiTmljY28iLCJmYW1pbHlfbmFtZSI6IlNjcmFwIiwiZXh0ZW5zaW9uX2x4UmVzZXRQYXNzd29yZE9uTmV4dExvZ2luIjpmYWxzZSwidGlkIjoiOTlhMTYyZmEtOTIwNy00OGQ0LTk0ZGQtOGIzY2M1YTE0MzQxIiwiYXpwIjoiM2JkNWI5NWMtZDY4NS00YWUwLThjNjYtYjQ3YTNlZTRmMThkIiwidmVyIjoiMS4wIiwiaWF0IjoxNjY2OTg0NTE3fQ.Vxzc0F0FFwZlsqbXiHlfaQrp-oOjeWtHA9AqkN6YgwFl6AvF93FIz1GwzR4VFaV_uTf0UzLeAjs7YasMTken71gyG5GIW1InCeVy0NjHd3yNlNBtF_bfMEjQYNe1Mrn1QkT7bSrI6AleYMBEJmYo3Y9jaKX2zFtXISs-rmdZs3IjrH-nko636k0rZDmegiDMu6QxY_TdVDTiqlnUWInPFkmHfOaMQhvuIefyyMu7hGkdZfvDcBWSIcIeMWSneFaoMvwm1qRNxI-cePArCY5KjNEtD4B0RY9aCUsy0P7ONzxljE046UGy_KJmcQaXC86iD-_flFueA0gPzp92Vgi_jQ; md5=shek.0001009076.it; bm_sv=6471BAD4420928FA22D423F4849DEC10~YAAQB77XF8dYmOeDAQAAwDEFIBH+B5URVduOjw/brpe5X4pJLuCpvYPjSResAdyoQoD6al2Dzj+sOJMMspZb6bo51l+9P3niJXxRg22YNYj9VRYAQvRoEgre4T9xUHnWxljuoWULVUkQctobgsKkARKnDd1BcnZttTKIa9bdTRnsHD94O/eDVxOlQMSMZOQFYwaPUXs4GZPD8EuRXSdQht3EEKN00zFjeQtTfUPEmsAcUW9w8HgPxdcQMmCYwDi4E6OKpxGVkYwReg==~1; tealium_data2track_Tags_AdobeAnalytics_TrafficSourceJid_ThisHit=210283DIR; tealium_data_tags_adobeAnalytics_trafficSourceJid_stackingInSession=210281DIR-210282DIR-210283DIR; TS01a3ba2e=01ccc2acf4272bb66b42098a9e86c0b55345b5d7b931d33e81e79c19a4e936dfbd4884cf460d6e05db13786a5055479dca1f1f8f4f; utag_main=v_id:01842003eb73000de15c8b4c430d0506f002b06700bd0$_sn:3$_se:1$_ss:1$_st:1666992489204$vapi_domain:essilorluxottica.com$ses_id:1666990689204%3Bexp-session$_pn:1%3Bexp-session; s_sq=lux-myluxottica2021-prod%3D%2526c.%2526a.%2526activitymap.%2526page%253D%25252Fmyl-it%25252Fen-GB%25252Fpdp%25252F0pr%25252B10zs-1ab5s0%2526link%253D360%2525C2%2525B0%252520view%2526region%253Dpage-content%2526pageIDType%253D1%2526.activitymap%2526.a%2526.c%2526pid%253D%25252Fmyl-it%25252Fen-GB%25252Fpdp%25252F0pr%25252B10zs-1ab5s0%2526pidt%253D1%2526oid%253DfunctionNr%252528%252529%25257B%25257D%2526oidt%253D2%2526ot%253DSUBMIT; dtLatC=72; _gat=1; rxvt=1666992629860|1666990508353; dtPC=7$190827406_557h14vHCQKFQNAHFACCTVJEMQHHAVJUUWVPARE-0e0',
        'referer': referer,
        'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'x-dtpc': '7$190827406_557h14vHCQKFQNAHFACCTVJEMQHHAVJUUWVPARE-0e0'
    }

def get_id_and_tokenValue(identifier: str, headers: dict):
    id, tokenValue = '', ''
    try:
        url = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/pages/identifier/{identifier}'
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            json_data = json.loads(response.text)
            id = str(int(json_data['data']['contents'][0]['id']))
            tokenValue = json_data['data']['contents'][0]['tokenValue']
        else: print(f'Status code: {response.status_code} for id and tokenValue')
    except Exception as e:
        print(f'Exception in get_tokenValue_and_id: {e}')
    finally: return id, tokenValue

def get_parentCatalogEntryID(tokenValue: str, headers: dict) -> str:
    parentCatalogEntryID = ''
    try:
        url = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/variants/{tokenValue}'
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            json_data = json.loads(response.text)
            parentCatalogEntryID = json_data['data']['catalogEntryView'][0]['parentCatalogEntryID']
        else: print(f'Status code: {response.status_code} for parentCatalogEntryID')
    except Exception as e:
        print(f'Exception in get_parentCatalogEntryID: {e}')
    finally: return parentCatalogEntryID

def get_all_variants_data(parentCatalogEntryID: str, headers: str) -> list[dict]:
    variants = []
    try:
        url = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/{parentCatalogEntryID}/variants'
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            json_data = json.loads(response.text)
            for variant in json_data['data']['catalogEntryView'][0]['variants']:
                try:
                    partNumber = variant['partNumber']
                    uniqueID = variant['uniqueID']
                    try: name = variant['name']
                    except: pass
                    # sizes, colors, lens_properties, lens_colors = [], [], [], []
                    # for attribute in variant['attributes']:
                    #     if attribute['identifier'] == 'DL_SIZE_CODE':
                    #         for value in attribute['values']:
                    #             size = value['value']
                    #             sizes.append(size)
                    #     elif attribute['identifier'] == 'FRONT_COLOR_DESCRIPTION':
                    #         for value in attribute['values']:
                    #             color = value['value']
                    #             colors.append(color)
                    #     elif attribute['identifier'] == 'LENS_PROPERTIES':
                    #         for value in attribute['values']:
                    #             lens_property = value['value']
                    #             lens_properties.append(lens_property)
                    #     elif attribute['identifier'] == 'LENS_COLOR_DESCRIPTION':
                    #         for value in attribute['values']:
                    #             lens_color = value['value']
                    #             lens_colors.append(lens_color)

                    variants.append({'partNumber': partNumber, 'name': name, 'uniqueID': uniqueID})
                except: pass
        else: print(f'Status code: {response.status_code} for get_all_variants_data')
    except Exception as e:
        print(f'Exception in get_all_variants_data: {e}')
    finally: return variants

def get_product_variants(uniqueID: str, headers: dict) -> dict:
    properties = {}
    try:
        url = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/variants/{uniqueID}'
        response = requests.get(url=url, headers= headers)
        if response.status_code == 200:
            json_data = json.loads(response.text)
            frame_color, lens_color, for_who, lens_material, frame_shape, frame_material, lens_technology = '', '', '', '', '', '', ''
            for attribute in json_data['data']['catalogEntryView'][0]['attributes']:
                values = []
                if attribute['identifier'] == 'FRONT_COLOR_DESCRIPTION':
                    for value in attribute['values']: values.append(value['value'])
                    frame_color = ', '.join(values)
                elif attribute['identifier'] == 'LENS_COLOR_DESCRIPTION':
                    for value in attribute['values']: values.append(value['value'])
                    lens_color = ', '.join(values)
                elif attribute['identifier'] == 'GENDER':
                    for value in attribute['values']: values.append(value['value'])
                    for_who = ', '.join(values)
                elif attribute['identifier'] == 'LENS_MATERIAL':
                    for value in attribute['values']: values.append(value['value'])
                    lens_material = ', '.join(values)
                elif attribute['identifier'] == 'FACE_SHAPE':
                    for value in attribute['values']: values.append(value['value'])
                    frame_shape = ', '.join(values)
                elif attribute['identifier'] == 'FRAME_MATERIAL':
                    for value in attribute['values']: values.append(value['value'])
                    frame_material = ', '.join(values)
                elif attribute['identifier'] == 'PHOTOCHROMIC':
                    if attribute['values'][0]['value'] == 'TRUE':
                        if lens_technology: lens_technology += str(' PHOTOCHROMIC').title()
                        else: lens_technology = str('PHOTOCHROMIC').title()
                elif attribute['identifier'] == 'POLARIZED':
                    if attribute['values'][0]['value'] == 'TRUE':
                        if lens_technology: lens_technology += str(' POLARIZED').title()
                        else: lens_technology = str('POLARIZED').title()

            if not str(lens_technology).strip():
                for attribute in json_data['data']['catalogEntryView'][0]['attributes']:
                    if attribute['identifier'] == 'LENS_COLORING_PERCEIVED':
                        lens_technology = str(attribute['values'][0]['value']).strip()

            ids = []
            sizes_without_q = []
            for sKU in json_data['data']['catalogEntryView'][0]['sKUs']:
                uniqueID = str(sKU['uniqueID'])
                title = str(sKU['partNumber']).strip()[-2:]
                upc = str(sKU['upc'])
                ids.append(uniqueID)
                sizes_without_q.append({'uniqueID': uniqueID, 'title': title, 'UPC': upc})

            sizes = []
            json_response = check_availability('%2C'.join(ids), headers)
            for json_res in json_response:
                productId = json_res['productId']
                for size_without_q in sizes_without_q:
                    if productId == size_without_q['uniqueID']:
                        inventory_quantity = 0
                        if json_res['inventoryStatus'] == 'Available': inventory_quantity = 1
                        sizes.append({'title': size_without_q['title'], 'inventory_quantity': inventory_quantity, "UPC": size_without_q['UPC']})
            
            properties = {
                'frame_color': frame_color, 
                'lens_color': lens_color, 
                'for_who': for_who, 
                'lens_material': lens_material, 
                'frame_shape': frame_shape, 
                'frame_material': frame_material, 
                'lens_technology': lens_technology,
                'sizes': sizes
            }
        else: print(f'Status code: {response.status_code} for id and tokenValue')
    except Exception as e:
        print(f'Exception in get_tokenValue_and_id: {e}')
    finally: return properties

def check_availability(payload: str, headers: dict) -> list[dict]:
    json_data = {}
    try:
        
        url = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/availability?productId={payload}'
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            json_data = json.loads(response.text)
            json_data = json_data['data']
            json_data = json_data['doorInventoryAvailability'][0]['inventoryAvailability']
    except Exception as e:
        print(f'Exception in check_availability: {e}')
    finally: return json_data

def get_360_images(tokenValue: str, headers: dict) -> list[str]:
    image_360_urls = []
    try:
        url = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/variants/{tokenValue}/attachments?type=PHOTO_360'
        response = requests.get(url=url, headers= headers)
        if response.status_code == 200:
            json_data = json.loads(response.text)
            for attachment in json_data['data']['catalogEntryView'][0]['attachments']:
                image_360_urls.append(attachment['attachmentAssetPath'])
    except Exception as e:
        print(f'Exception in get_360_images: {e}')
    finally: return image_360_urls

def get_prices(tokenValue: str, headers: dict) -> list[str]:
    prices = []
    try:
        url = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/prices?productId={tokenValue}'
        response = requests.get(url=url, headers= headers)
        if response.status_code == 200:
            json_data = json.loads(response.text)
            for data in json_data['data']:
                wholesale_price = float(data[tokenValue]['OPT'][0]['price']['value'])
                listing_price = float(data[tokenValue]['PUB'][0]['price']['value'])
                prices.append({'wholesale_price': wholesale_price, 'listing_price': listing_price})
    except Exception as e:
        print(f'Exception in get_prices: {e}')
    finally: return prices


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
                frame_code = str(json_d['frame_code']).strip().upper()
                if '/' in frame_code: frame_code = frame_code.replace('/', '-').strip()
                frame_color = str(json_d['frame_color']).strip().title()
                lens_color = str(json_d['lens_color']).strip().title()
                
                for json_metafiels in json_d['metafields']:
                    if json_metafiels['key'] == 'img_url':img_url = str(json_metafiels['value']).strip()
                    
                for json_variant in json_d['variants']:
                    sku, price = '', ''
                    sku = str(json_variant['sku']).strip().upper()
                    if '/' in sku: sku = sku.replace('/', '-').strip()
                    wholesale_price = str(json_variant['wholesale_price']).strip()
                    listing_price = str(json_variant['listing_price']).strip()
                    img_url = img_url.replace('impolicy=MYL_EYE&wid=262', 'impolicy=MYL_EYE&wid=600')
                    image_attachment = download_image(img_url)
                    if image_attachment:
                        with open(f'Images/{sku}.jpg', 'wb') as f: f.write(image_attachment)
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
                    image_attachment = response.content
                    break
                else: print(f'{response.status_code} found for downloading image')
            except: sleep(0.3)
            counter += 1
            if counter == 10: break
    except Exception as e: print(f'Exception in download_image: {str(e)}')
    finally: return image_attachment

f = open('requirements/Luxottica Results.json')
json_data = json.loads(f.read())
f.close()

filename = 'requirements/Luxottica Results.json'


def webtohtml(data, filename):
    print(data['number'], filename)
    sleep(0.2)


# sorted(json_data, key=lambda d: d['number'], reverse=True)
# sorted(json_data, key=lambda d: d['frame_code'], reverse=True)

# with open('requirements/Luxottica Results 2.json', 'w') as f: json.dump(json_data, f)

with ThreadPoolExecutor(max_workers=50) as e:
        e.map(partial (webtohtml, filename = filename), json_data)
print('Now')
# class myThread (threading.Thread):
#     def __init__(self, threadID, name, counter):
#         threading.Thread.__init__(self)
#         self.threadID = threadID
#         self.name = name
#         self.counter = counter

#     def run(self):
#         print ("Starting " + self.name)
#         # Get lock to synchronize threads
#         threadLock.acquire()
#         print_time(self.name, self.counter, 3)
#         # Free lock to release next thread
#         threadLock.release()









# referer = 'https://my.essilorluxottica.com/myl-it/en-GB/pdp/0rb3016-1366g6'
# headers = get_headers(referer)
# identifier = str(referer).split('/')[-1].strip()
# id, tokenValue = get_id_and_tokenValue(identifier, headers)
# # print(id, tokenValue)
# parentCatalogEntryID = get_parentCatalogEntryID(tokenValue, headers)
# # print(parentCatalogEntryID)
# variants = get_all_variants_data(parentCatalogEntryID, headers)

# for varinat in variants:
#     url = f'https://my.essilorluxottica.com/myl-it/en-GB/pdp/{str(varinat["partNumber"]).replace(" ", "+").replace("_", "-").replace("/", "-").lower()}'
#     number = str(varinat['partNumber']).strip().split('_')[0].strip()[1:]
#     name = str(varinat['name']).strip()
#     frame_code = str(varinat['partNumber']).strip().split('_')[-1].strip()
#     prices = get_prices(varinat['uniqueID'])
#     # image_360_urls = get_360_images(varinat['uniqueID'])
#     properties = get_product_variants(varinat['uniqueID'])
#     frame_color = properties['frame_color'] 
#     lens_color = properties['lens_color'] 
#     for_who = properties['for_who'] 
#     lens_material = properties['lens_material'] 
#     frame_shape = properties['frame_shape'] 
#     frame_material = properties['frame_material'] 
#     lens_technology = properties['lens_technology']
#     sizes = properties['sizes']
#     print(url, number, name, frame_code, prices, frame_color, lens_color, for_who, lens_material, lens_technology, frame_shape, frame_material, sizes)

#     break





# url1 = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/pages/identifier/0pr+10zs-1ab5s0'

# response = requests.get(url=url1, headers=headers)
# if response.status_code == 200:
#     json_data = json.loads(response.text)
#     # print(json_data)
#     status = json_data['status']
#     message = json_data['message']
#     data = json_data['data']
#     contents = data['contents']
#     # print(contents)
#     for content in contents:
#         content_identifier = content['identifier']
#         content_tokenName = content['tokenName']
#         content_tokenExternalValue = content['tokenExternalValue']
#         content_language = content['language']
#         content_id = int(content['id'])
#         content_page = content['page']
#         content_page_imageAlternateDescription = content_page['imageAlternateDescription']
#         content_page_name = content_page['name']
#         content_page_title = content_page['title']
#         content_page_type = content_page['type']
#         content_page_metaKeyword = content_page['metaKeyword']
#         content_storeId = content['storeId']
#         content_tokenValue = content['tokenValue']
#         content_status = content['status']
        # print(content_identifier, content_id, content_page, content_storeId, content_tokenValue)

        # url2 = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/variants/{content_tokenValue}'

        # response = requests.get(url=url2, headers=headers)

        # if response.status_code == 200:
        #     json_data = json.loads(response.text)
        #     # print(json_data)

        # get 360 images
        # url3 = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/variants/{content_tokenValue}/attachments?type=PHOTO_360'
        # response = requests.get(url=url3, headers=headers)

        # if response.status_code == 200:
        #     json_data = json.loads(response.text)
            # print(json_data)

        # get image
        # url4 = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/variants/{content_tokenValue}/attachments?type=PHOTO'
        # response = requests.get(url=url4, headers=headers)

        # if response.status_code == 200:
        #     json_data = json.loads(response.text)
        #     print(json_data)

        # get availability
        # url5 = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/availability?productId=3074457345622796989'
        # response = requests.get(url=url5, headers=headers)

        # if response.status_code == 200:
        #     json_data = json.loads(response.text)
        #     print(json_data)

        # url6 = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/brandgroup/brands'
        # response = requests.get(url=url6, headers=headers)

        # if response.status_code == 200:
        #     json_data = json.loads(response.text)
        #     print(json_data)

        # get price
        # url7 = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/prices?productId={content_tokenValue}'
        # response = requests.get(url=url7, headers=headers)

        # if response.status_code == 200:
        #     json_data = json.loads(response.text)
        #     print(json_data)
        
        # get prices
        # url8 = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/prices?productId=3074457345616677757&productId=3074457345616677176&productId=3074457345616854232&productId=3074457345616677204'
        # response = requests.get(url=url8, headers=headers)

        # if response.status_code == 200:
        #     json_data = json.loads(response.text)
        #     print(json_data)
        
        # get variants info
        # url9 = f'https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-it/en-GB/products/3074457345622788570/variants'
        # response = requests.get(url=url9, headers=headers)

        # if response.status_code == 200:
        #     json_data = json.loads(response.text)
        #     print(json_data)