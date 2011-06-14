#!/usr/bin/env python
import logging
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

def get_unique_tiles(img, size=12):
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
						action = 'store', type = 'inkboolean',
						dest = 'clear', default = False,
						help = 'Clear existing Tileset Layers?')

	def effect(self):
		tile_size = self.options.tile_size
		clear_old_layers = self.options.clear_old_layers

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

		tiles = [Image.fromstring('RGB', (tile_size, tile_size), tile) for tile in tiles]
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



effect = CompileTileset()
effect.affect()

#if __name__ == '__main__':
#	imgs = sys.argv[1:]
#	tiles = set()
#	for path in imgs:
#		img = Image.open(path)
#		tiles = tiles.union(get_unique_tiles(img))
#	tileset = compile_tileset(tiles)
#	tileset.show()
#	print make_data_uri(tileset)
#	input()
