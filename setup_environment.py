#!/usr/bin/env python
import logging
import itertools
import sys
import urllib

from cStringIO import StringIO

import inkex
import simplestyle

from PIL import Image

logging.basicConfig(
	level=logging.ERROR,
	stream=sys.stderr
)

def rgb2hex(rgb):
	return "#%02X%02X%02X" % rgb

def make_data_uri(img):
	"Convert an Image to a base64 URI"
	s = StringIO()
	img.save(s, 'png')
	s.seek(0)
	img_s = ''.join(s.readlines()).encode('base64').translate(None, '\n')
	return "data:image/png;base64,%s" % img_s

def decode_uri(uri):
	"Scrap a URI which suitable to pass to Image.open()"
	if uri.startswith("file:///"):
		return urllib.unquote(uri[len("file:///"):])
	return StringIO(uri[uri.find("base64,") + len("base64,"):].decode('base64'))

def get_unique_tiles_slowly(img, size=12):
	logging.info("Gathering unique tiles...")
	tiles = set()
	_, _, max_x, max_y = img.getbbox()
	for x in range(0, max_x):
		for y in range(0, max_y):
			box = (
				(x * size), (y * size),
				(x+1) * size, (y+1) * size
			)
			tile = img.crop(box)
			tiles.add(tile.tostring())
	logging.info("Found %d unique tiles" % len(tiles))
	return tiles

def calculate_linear_slices(index, width, tile_size):
	"Calculate slices representing a 2D box in a 1D space."
	slices = []
	for i in range(0, tile_size):
		row = ((index[1] * tile_size) + i) * width
		leftmost = row + (index[0] * tile_size)
		slices.append(slice(leftmost, leftmost + tile_size))
	return slices

def get_unique_tiles(img, tile_size=12):
	logging.info("Gathering unique tiles...")

	_, _, max_x, max_y = img.getbbox()

	columns = max_x / float(tile_size)
	rows = max_y / float(tile_size)
	# Using this method we can't reliably assume the tiles properly begin at the
	# upper left corner so we're going to kick it back.
	#TODO: Make this kick back some actual feedback.
	if not columns.is_integer() or not rows.is_integer():
		return set()

	columns = int(columns)
	rows = int(rows)

	pixels = tuple(img.getdata())
	tiles = set()

	for x in range(0, columns):
		for y in range(0, rows):
			slices = calculate_linear_slices((x, y), max_x, tile_size)
			tile = tuple(pixels[s] for s in slices)
			tiles.add(tile)
	logging.info("Found %d unique tiles" % len(tiles))
	return tiles

class SetupEnvironment(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)

		self.OptionParser.add_option('-s', '--size',
						action = 'store', type = 'int',
						dest = 'tile_size', default = 12,
						help = 'What is the size of a tile in pixels?')

		self.OptionParser.add_option('-c', '--columns',
						action = 'store', type = 'int',
						dest = 'columns', default = 8,
						help = 'How many tiles wide the page will be')

	def effect(self):
		tile_size = self.options.tile_size
		columns = self.options.columns

		root = self.document.xpath('//svg:svg',namespaces=inkex.NSS)[0]
		root.set('width', str(columns * tile_size))
		root.set('height', str(columns * 2 * tile_size))

		grid_attrs = dict(
			enabled = 'true',
			visible = 'true',
			type = 'xygrid',
			snaptovisiblegridlinesonly = 'true',
			empspacing = str(tile_size)
		)
		grid = inkex.etree.Element(inkex.addNS('grid', 'inkscape'), grid_attrs)
		base = self.xpathSingle('//sodipodi:namedview[@id="base"]')
		base.set(inkex.addNS('zoom', 'inkscape'), '3')
		base.append(grid)

if __name__ == '__main__':
	effect = SetupEnvironment()
	effect.affect()
