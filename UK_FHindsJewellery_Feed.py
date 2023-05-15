# -*- coding: utf-8 -*-

import time

import scrapy
import logging

from feedspiders.items import ProductItem
from re import sub

timestamp = time.strftime("%Y-%m-%d %H-%M")

class UK_FHindsJewellery_Feed(scrapy.Spider):
	name = "UK_FHindsJewellery_Feed"
	allowed_domains = ["www.fhinds.co.uk"]
	start_urls = ('https://www.fhinds.co.uk/jewellery/gold-and-silver-jewellery/rings',
				  'https://www.fhinds.co.uk/jewellery/gold-and-silver-jewellery/earrings',
				  'https://www.fhinds.co.uk/jewellery/gold-and-silver-jewellery/necklaces-and-lockets',
				  'https://www.fhinds.co.uk/jewellery/gold-and-silver-jewellery/chains',
				  'https://www.fhinds.co.uk/jewellery/gold-and-silver-jewellery/bracelets-and-bangles',)

	custom_settings = {
		'FEED_FORMAT': 'csv',
		'FEED_URI': f'ftp://scraper:scr4p3@ftp.bevalued.co.uk/%(name)s/%(name)s-{timestamp}.csv',
		'FEED_EXPORT_FIELDS': ["make", "model", "country", "price", "category", "subcategory", "subcategory2", "partNumber", "retailSKU", "EAN", "productURL"],
		'LOG_FORMAT': '%(message)s'}

	def parse(self, response):
		currentURL = response.request.url
		category = str(currentURL).replace('https://www.fhinds.co.uk/jewellery/gold-and-silver-jewellery/', '')

		maxPages = int(response.xpath('//a[@class="fnchangepage show-more-button"]/@data-totalpages').get())
		self.logger.info('maxPages - ' + str(maxPages))

		page = 1
		while page <= maxPages:
			indexURL = currentURL + '?interaction=1&listing_page=' + str(page)

			self.logger.info('indexURL - ' + str(indexURL))

			yield scrapy.Request(indexURL, callback=self.parse_index)

			page += 1

	def parse_index(self, response):
		currentURL = response.request.url

		productURLIndex = response.xpath('//div[@class="fnLoadedPage"]/div[1]/div/div[1]/span[1]/a[1]/@href').getall()

		for productURL in productURLIndex:
			URL = response.urljoin(productURL)
			self.logger.info('productURL - ' + str(URL))

			yield scrapy.Request(URL, callback=self.parse_details)

	def parse_details(self, response):
		item = ProductItem()
		category = response.meta.get('category')

		item['productURL'] = response.request.url

		item['instock'] = True
		item['price'] = str(response.xpath('//span[@class="product-price-large"]/text()').get()).replace('Our Price £', '')

		item['dataOK'] = True
		item['garbageRating'] = 0
		item['country'] = 'UK'

		item['model'] = str(response.xpath('//head/title/text()').get()).split(' | ', 1)[0]
		item['retailSKU'] = item['model'].split(' - ', 1)[-1]
		item['model'] = item['model'].split(' - ', 1)[0]

		item['model'] = item['model'] + ' (' + item['retailSKU'] + ')'

		specKey = response.xpath('//div[@id="details-tab"]//div[@class="table-row"]/div[1]/text()').getall()
		specValue = response.xpath('//div[@id="details-tab"]//div[@class="table-row"]/div[2]/text()').getall()

		specListKey = []
		for key in specKey:
			if key.strip():
				specListKey.append(key.strip())

		specListValue = []
		for value in specValue:
			if value.strip():
				specListValue.append(value.strip())

		specList = dict(zip(specListKey, specListValue))

		try:
			item['make'] = specList['Brand']
		except KeyError:
			item['make'] = 'F. Hinds'

		item['category'] = category

		return item
