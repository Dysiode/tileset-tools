import re

from lxml import etree
from PIL import Image

import inkex
import simplestyle

def rgb2hex(rgb):
	return "#%02X%02X%02X" % rgb

def decode_uri(uri):
	"Scrap a URI which suitable to pass to Image.open()"
	if uri.startswith("file:///"):
		return urllib.unquote(uri[len("file:///"):])
	return StringIO(uri[uri.find("base64,") + len("base64,"):].decode('base64'))

def pos2index(size, x, y):
	return x + (y * size)

def index2pos(size, i, offset=0, scale=1):
	return ((i % size) * scale) + offset, ((i // size) * scale) + offset

class AnyImage(object):
	types = 'raster', 'vector'
	def __init__(self, size, pos=(0,0), data=None):
		self.size = size
		self.data = data
		self.transform = ''
		self.pos = pos

	def decode(self, img, what_is=None):
		if what_is is None:
			what_is = self.find_what_is(img)
			if what_is is None:
				return

		getattr(self, 'decode_'+what_is)(img)

	def find_what_is(self, img):
		if isinstance(img, Image.Image):
			return 'raster'

		if isinstance(img, etree._Element):
			return 'vector'

		return None

	def decode_raster(self, img):
		img_uri = img.attrib[inkex.addNS('href', 'xlink')]
		pil_img = Image.open(decode_uri(img_uri))

		self.data = pil_img.getdata()
		self.transform = img.transform
		self.pos = (inkex.unittouu(img.attrib['x']),
				    inkex.unittouu(img.attrib['y']))

	def decode_vector(self, img):
		self.data = [None] * (self.size ** 2)
		self.transform = img.attrib['transform']
		self.pos = (float('inf'), float('inf'))

		pixels = img.xpath('//svg:rect', namespaces=inkex.NSS)
		paths = img.xpath('//svg:path', namespaces=inkex.NSS)

		# Because svg groups have no set x,y coords we have to decern the
		# position from the contents which we can then use as an offset when
		# reconstructing the image.
		for pixel in pixels + paths:
			pos = (inkex.unittouu(pixel.attrib['x']),
				   inkex.unittouu(pixel.attrib['y']))
			self.pos[0] = self.pos[0] if self.pos[0] < pos[0] else pos[0]
			self.pos[1] = self.pos[1] if self.pos[1] < pos[1] else pos[1]

		for pixel in pixels:
			style = simplestyle.parseStyle(pixel.attrib['style'])
			pos = (inkex.unittouu(pixel.attrib['x']) - self.pos[0],
				   inkex.unittouu(pixel.attrib['y']) - self.pos[1])
			index = pos2index(self.size, *pos)
			self.data[index] = simplestyle.parseColor(style['fill'])

		last_point = (0, 0)
		for path in paths:
			for offset in re.findall('m\s(?P<x>-?\d+),(?P<y>-?\d+).*?z'):
				style = simplestyle.parseStyle(pixel.attrib['style'])
				pos = (inkex.unittouu(path.attrib['x']) - self.pos[0] + last_point[0],
					   inkex.unittouu(path.attrib['y']) - self.pos[1] + last_point[1])
				index = pos2index(self.size, *pos)
				self.data[index] = simplestyle.parseColor(style['fill'])

				last_point[0] += offset[0]
				last_point[1] += offset[1]

	def rasterize(self):
		img = Image.new('rgb', (self.size, self.size))
		img.putdata(self.data)
		return img

	def vectorize(self):
		tile_group = inkex.etree.Element(inkex.addNS('g', 'svg'))
		for i, rgb in enumerate(self.data):
			x, y = index2pos(self.size, i)
			x += self.pos[0]
			y += self.pos[1]

			style = {
				'stroke': 'none',
				'fill': rgb2hex(rgb),
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

	def vectorize_with_paths(self):
		tile_group = inkex.etree.Element(inkex.addNS('g', 'svg'))
		color_groups = {}
		for i, rgb in enumerate(self.data):
			x, y = index2pos(self.size, i)
			x += self.pos[0]
			y += self.pos[1]

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
				'fill': rgb2hex(rgb),
			}

			attrs = {
				'd': path,
				'style': simplestyle.formatStyle(style),
			}

			pixel_group = inkex.etree.Element(inkex.addNS('path', 'svg'), attrs)
			tile_group.append(pixel_group)
		return tile_group
