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

class VectorizeTiles(inkex.Effect):

	def __init__(self):
		inkex.Effect.__init__(self)

		self.OptionParser.add_option('-s', '--size',
						action = 'store', type = 'int',
						dest = 'tile_size', default = '12',
						help = 'What is the size of a tile in pixels?')

		self.OptionParser.add_option('-g', '--group',
						action = 'store', type = 'inkbool',
						dest = 'group', default = True,
						help = 'Group like colors into paths?')

	def effect(self):
		self.tile_size = tile_size = self.options.tile_size

		layers = self.document.xpath('//svg:g[@inkscape:label="Tileset Layer"]', namespaces=inkex.NSS)

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

		if self.options.group:
			return self.vectorize_data_with_path(tile_data, (tile_x, tile_y))

		return self.vectorize_data(tile_data, (tile_x, tile_y))

	def vectorize_data(self, tile_data, tile_xy):
		tile_size = self.tile_size
		tile_x, tile_y = tile_xy

		#TODO: It may make sense to compile each pixel into a path of that color
		tile_group = inkex.etree.Element(inkex.addNS('g', 'svg'))
		for i, rgb in enumerate(tile_data):
			x = tile_x + (i % tile_size)
			y = tile_y + (i // tile_size)

			style = {
				'stroke': 'none',
				'fill': str(rgb2hex(rgb)),
			}

			attrs = {
				'style': simplestyle.formatStyle(style),
				'x': str(x),
				'y': str(y),
				'width': '1',
				'height': '1',
			}

			pixel = inkex.etree.Element(inkex.addNS('rect', 'svg'), attrs)
			tile_group.append(pixel)
		return tile_group

	def vectorize_data_with_path(self, tile_data, tile_xy):
		tile_size = self.tile_size
		tile_x, tile_y = tile_xy

		#TODO: It may make sense to compile each pixel into a path of that color
		tile_group = inkex.etree.Element(inkex.addNS('g', 'svg'))
		color_groups = {}
		for i, rgb in enumerate(tile_data):
			x = tile_x + (i % tile_size)
			y = tile_y + (i // tile_size)

			if rgb not in color_groups:
				color_groups[rgb] = []
			color_groups[rgb].append((x, y))

		for rgb, points in color_groups.iteritems():
			path = ""
			path_template = "m %d,%d 1,0 0,1 -1,0 z "
			last_point = (0, 0)
			for point in points:
				path += path_template % (point[0]-last_point[0],
										 point[1]-last_point[1])
				last_point = point

			style = {
				'stroke': 'none',
				'fill': str(rgb2hex(rgb)),
			}

			attrs = {
				'd': path,
				'style': simplestyle.formatStyle(style),
			}

			pixel_group = inkex.etree.Element(inkex.addNS('path', 'svg'), attrs)
			tile_group.append(pixel_group)
		return tile_group


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
