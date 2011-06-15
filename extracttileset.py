#!/usr/bin/env python
import logging
import itertools
import sys
import urllib

from cStringIO import StringIO

import inkex

from PIL import Image

logging.basicConfig(
	level=logging.ERROR,
	stream=sys.stderr
)

def make_data_uri(img):
	s = StringIO()
	img.save(s, 'png')
	s.seek(0)
	img_s = ''.join(s.readlines()).encode('base64').translate(None, '\n')
	return "data:image/png;base64,%s" % img_s

def get_tileset_size(tiles, columns, tile_size):
	width = columns * tile_size
	height = int(round(
			(tiles / float(columns)) + 0.5
		)) * tile_size
	return width, height

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

def calculate_linear_ranges(index, width, tile_size):
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
			slices = calculate_linear_ranges((x, y), max_x, tile_size)
			tile = tuple(pixels[s] for s in slices)
			tiles.add(tile)
	logging.info("Found %d unique tiles" % len(tiles))
	return tiles

def rebuild_tile(tile_tuple, tile_size):
	tile_img = Image.new('RGB', (tile_size, tile_size))
	tile_img.putdata(tuple(itertools.chain.from_iterable(tile_tuple)))
	return tile_img

def compile_tileset(tiles, columns=10, tile_size=12):
	logging.info("Compiling tileset...")
	tiles = [Image.fromstring('RGB', (tile_size, tile_size), tile) for tile in tiles]
	set_size = get_tileset_size(len(tiles), columns, tile_size)
	tileset = Image.new('RGB', set_size)
	for i, tile in enumerate(tiles):
		x = i % columns
		y = (i / columns)
		box = (
			(x * tile_size), (y * tile_size),
			(x+1) * tile_size, (y+1) * tile_size
		)
		tileset.paste(tile, box)
	logging.info("Finished compiling tileset")
	return tileset

class CompileTileset(inkex.Effect):

	def __init__(self):
		inkex.Effect.__init__(self)

		self.OptionParser.add_option('-s', '--size',
						action = 'store', type = 'int',
						dest = 'tile_size', default = '12',
						help = 'What is the size of a tile in pixels?')

		self.OptionParser.add_option('-c', '--clear',
						action = 'store', type = 'inkbool',
						dest = 'clear_first', default = False,
						help = 'Clear existing Tileset Layers?')

	def effect(self):
		tile_size = self.options.tile_size
		clear_old_layers = self.options.clear_first

		root = self.document.xpath('//svg:svg',namespaces=inkex.NSS)[0]

		width = inkex.unittouu(root.attrib['width'])
		height = inkex.unittouu(root.attrib['height'])

		columns = width // tile_size

		if clear_old_layers:
			set_layer_path = '//svg:g[@inkscape:label="Tileset Layer"]'
			set_layer = root.xpath(set_layer_path, namespaces=inkex.NSS)
			for layer in set_layer:
				root.remove(layer)

		set_layer = inkex.etree.SubElement(root, 'g')
		set_layer.set(inkex.addNS('label', 'inkscape'), 'Tileset Layer')
		set_layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')


		tiles = set()
		for uri in self.gather_source_uris():
			tiles |= get_unique_tiles(Image.open(self.decode_uri(uri)), tile_size)

		tiles = [rebuild_tile(tile, tile_size) for tile in tiles]
		for i, tile in enumerate(tiles):
			uri = make_data_uri(tile)
			img = self.build_svg_img(
				uri,
				x = str((i % columns) * tile_size),
				y = str((i // columns) * tile_size),
				width = str(tile_size),
				height = str(tile_size)
			)
			set_layer.append(img)

	def gather_source_uris(self):
		path = '//svg:g[@inkscape:label="Source Layer"]/svg:image'
		source_elements = self.document.xpath(path, namespaces=inkex.NSS)

		for element in source_elements:
			yield element.attrib[inkex.addNS('href', 'xlink')]

	def decode_uri(self, uri):
		if uri.startswith("file:///"):
			return urllib.unquote(uri[len("file:///"):])
		return StringIO(uri[uri.find("base64,") + len("base64,"):].decode('base64'))

	def build_svg_img(self, uri, **attrs):
		img = inkex.etree.Element(inkex.addNS('image', 'svg'), attrs)
		img.set(inkex.addNS('href', 'xlink'), uri)
		return img


if __name__ == '__main__':
	effect = CompileTileset()
	effect.affect()

	# Forgive the mess, I'll clean it up when I'm done! I promise!
	#imgs = sys.argv[1:]
	#tiles = set()
	#for path in [r"C:\Users\Patrick\My Dropbox\src\games\drain storm\2011-06-13_104602.png"]:#imgs:
	#	global img
	#	img = Image.open(path)
	#	tiles = tiles.union(get_unique_tiles(img))
	#	#tiles = tiles.union(get_unique_tiles(img))
	#	#import timeit
	#	#The new fn
	#	#print timeit.timeit('get_unique_tiles(img)', 'from __main__ import get_unique_tiles, img', number=5)
	#	#print timeit.timeit('get_unique_tiles_slowly(img)', 'from __main__ import get_unique_tiles_slowly, img', number=5)
	##tileset = compile_tileset(tiles)
	##tileset.show()
	##print make_data_uri(tileset)
	##input()
