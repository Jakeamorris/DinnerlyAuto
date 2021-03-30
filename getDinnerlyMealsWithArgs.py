from bs4 import BeautifulSoup
from os.path import exists
from PyPDF2 import PdfFileWriter, PdfFileReader
from PyPDF2.pdf import PageObject
import requests
import json, re, io
import ghostscript, win32print, locale
import argparse

url = "https://dinnerly.com.au/login"
session = requests.Session()

parser = argparse.ArgumentParser()
parser.add_argument("email")
parser.add_argument("password")
args = parser.parse_args()

#Load login page and get form auth token
response = session.get(url)

soup = BeautifulSoup(response.text, 'html.parser')
token = soup.find('input', {'name':'authenticity_token'})['value']

payload = {
        'spree_user[email]': args.email,
        'spree_user[password]': args.password,
        'authenticity_token': token,
        'spree_user[brand]': 'dn',
        'utf8': '✓'
}

#Use token to login
response = session.post(
                url, 
                data = payload, 
                headers = dict(referer=url)
)

response = session.get("https://dinnerly.com.au/accounts/orders")

#Get api auth token from orders page
soup = BeautifulSoup(response.text, 'html.parser')
script_list = soup.find_all('script', type='text/javascript')

for s in script_list:
        if s.string is not None:
                if "CDATA" in s.string:
                        auth_token = re.search('(?<=gon\\.api_token=")(.*?)(?=")', s.string).group()
                        user_id = re.search('(?<=gon.current_user_id=)(.*?)(?=;)', s.string).group()

#Make request to api.dinnerly with auth_token
url = 'https://api.dinnerly.com/users/' + user_id + '/orders/current?brand=dn&country=au&product_type=web'
auth_header = {'Authorization': 'Bearer ' + auth_token}

response = session.get(url, headers=auth_header)

#Parse orders json
orders = json.loads(response.text)
recipes = orders[len(orders) - 1]['recipes']
due_date = orders[len(orders) - 1]['delivery_date']

#using the id in each recipe, get the url to its pdf
recipe_dict = {}

for r in recipes:
        url = 'https://api.dinnerly.com/recipes/' + str(r['id']) + '?brand=dn&country=au&product_type=web'
        response = session.get(url, headers=auth_header)
        recipe = json.loads(response.text)
        recipe_dict[recipe['name_with_subtitle']] = recipe['recipe_card_url']

recipe_paths = []

#download pdfs
for key, value in recipe_dict.items():
        key_formatted = re.sub(r'[<>:"/|\\?*]+', '', key)

        path = r'C:\Users\Jake\Documents\Dinnerly Recipes\{date} - {name}.pdf'.format(date = due_date, name = key_formatted)

        #if pdfs exist then they have already been printed, probably
        if not exists(path):
                response = session.get(value)

                recipe_paths.append(path)

                with io.BytesIO(response.content) as pdf_file:
                        reader = PdfFileReader(pdf_file)
                        page_one = reader.getPage(0).rotateClockwise(90)
                        page_two = reader.getPage(1).rotateClockwise(90)

                        translated_page = PageObject.createBlankPage(None, page_two.mediaBox.getHeight(), page_two.mediaBox.getWidth())
                        translated_page.mergeScaledPage(page_two, 0.705)

                        translated_page.mergeScaledTranslatedPage(page_one, 0.705, 0, 400)

                        writer = PdfFileWriter()
                        writer.addPage(translated_page)

                        with open(path, 'wb') as f:
                                writer.write(f)
        else:
                continue

args = [
        "-dPrinted", "-dBATCH", "-dNOSAFER", "-dNOPAUSE", "-dNOPROMPT", "-dQUIET"
        "-q",
        "-dNumCopies#1",
        "-sDEVICE#mswinpr2",
        f'-sOutputFile#"%printer%{win32print.GetDefaultPrinter()}"'
]

for p in recipe_paths:
        args.append(f'"{p}"')
                        
encoding = locale.getpreferredencoding()
args = [a.encode(encoding) for a in args]
ghostscript.Ghostscript(*args)
        