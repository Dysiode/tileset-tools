#!/usr/bin/env python
import logging
import itertools
import sys
import urllib

from cStringIO import StringIO

import inkex
import simplestyle
import tti_tools

from PIL import Image

logging.basicConfig(
	level=logging.ERROR,
	stream=sys.stderr
)

def rgb2hex(rgb):
	return "#%02X%02X%02X" % rgb

class VectorizeTiles(inkex.Effect):

	def __init__(self):
		inkex.Effect.__init__(self)

		self.OptionParser.add_option('-s', '--size',
						action = 'store', type = 'int',
						dest = 'tile_size', default = '12',
						help = 'What is the size of a tile in pixels?')

		self.OptionParser.add_option('-a', '--all',
						action = 'store', type = 'inkbool',
						dest = 'all', default = False,
						help = 'Vectorize all tileset layers?')

		self.OptionParser.add_option('-g', '--group',
						action = 'store', type = 'inkbool',
						dest = 'group', default = True,
						help = 'Group like colors into paths?')

	def effect(self):
		self.tile_size = tile_size = self.options.tile_size
		all = self.options.all

		if all:
			layers = self.document.xpath('//svg:g[@inkscape:label="Tileset Layer"]', namespaces=inkex.NSS)
		else:
			base = self.xpathSingle('//sodipodi:namedview[@id="base"]')
			current_layer = base.attrib[inkex.addNS('current-layer', 'inkscape')]
			layers = [self.getElementById(current_layer)]

		for layer in layers:
			tiles = layer.xpath('svg:image', namespaces=inkex.NSS)
			for tile in tiles:
				vector_tile = self.vectorize_tile(tile)
				layer.remove(tile)
				layer.append(vector_tile)

		return


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

	def vectorize_tile(self, tile):
		tile_size = self.tile_size
		tile_x = inkex.unittouu(tile.attrib['x'])
		tile_y = inkex.unittouu(tile.attrib['y'])
		tile_img = Image.open(self.decode_uri(tile.attrib[inkex.addNS('href', 'xlink')]))
		tile_data = tile_img.getdata()

		any_img = tti_tools.AnyImage(tile_size, (tile_x, tile_y), tile_data)

		if self.options.group:
			return any_img.vectorize_with_paths()

		return any_img.vectorize()

	def decode_uri(self, uri):
		if uri.startswith("file:///"):
			return urllib.unquote(uri[len("file:///"):])
		return StringIO(uri[uri.find("base64,") + len("base64,"):].decode('base64'))

	def build_svg_img(self, uri, **attrs):
		img = inkex.etree.Element(inkex.addNS('image', 'svg'), attrs)
		img.set(inkex.addNS('href', 'xlink'), uri)
		return img


if __name__ == '__main__':
	effect = VectorizeTiles()
	effect.affect()


"""m 31,95 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z
m 5,-1 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z
m -5,0 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z
m 8,-1 1,0 0,1 -1,0 z
m -9,0 1,0 0,1 -1,0 z
m 9,-1 1,0 0,1 -1,0 z
m -9,0 1,0 0,1 -1,0 z
m 10,-1 1,0 0,1 -1,0 z
m -11,0 1,0 0,1 -1,0 z
m 11,-1 1,0 0,1 -1,0 z
m -11,0 1,0 0,1 -1,0 z
m 11,-1 1,0 0,1 -1,0 z
m -11,0 1,0 0,1 -1,0 z
m 11,-1 1,0 0,1 -1,0 z
m -11,0 1,0 0,1 -1,0 z
m 10,-1 1,0 0,1 -1,0 z
m -9,0 1,0 0,1 -1,0 z
m 9,-1 1,0 0,1 -1,0 z
m -9,0 1,0 0,1 -1,0 z
m 8,-1 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z
m -5,0 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z
m 5,-1 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z
m -1,0 1,0 0,1 -1,0 z"""
