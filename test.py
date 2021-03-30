from PyPDF2 import PdfFileWriter, PdfFileReader
from PyPDF2.pdf import PageObject

path = r'C:\Users\Jake\Documents\Dinnerly Recipes\2020-10-14 - Saucy Beef Meatballs and Pasta with Cheddar.pdf'

#fit 2 pages into one
reader = PdfFileReader(open(path, 'rb'))
page_one = reader.getPage(0).rotateClockwise(90)
page_two = reader.getPage(1).rotateClockwise(90)

translated_page = PageObject.createBlankPage(None, page_two.mediaBox.getHeight(), page_two.mediaBox.getWidth())
translated_page.mergeScaledPage(page_two, 0.705)

translated_page.mergeScaledTranslatedPage(page_one, 0.705, 0, 400)

writer = PdfFileWriter()
writer.addPage(translated_page)

with open(r'C:\Users\Jake\Documents\Dinnerly Recipes\test.pdf', 'wb') as f:
    writer.write(f)