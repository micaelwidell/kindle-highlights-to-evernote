import re
from datetime import datetime
import codecs 

try:
    # for Python2
    from Tkinter import *
    import tkMessageBox
except ImportError:
    # for Python3
    from tkinter import *
    from tkinter import messagebox as tkMessageBox

class EvernoteFile():
	notes = []

	def add_book_quote(self, title, author, quote, location, note, last_annotated):
		nnote = "\n<br/>\n<br/>\n<br/><span style=\"background-color: rgb(255, 250, 165);-evernote-highlight:true;\">Note: {}</span>".format(note) if note else ""
		tags = ["book-highlight", "{}".format(title), "{}".format(author)]
		content = quote + nnote
		if note:
			tags.append("has note")
		self.notes.append({"title": title + "; location " + location, "content": content, "tags": tags})

	def save_to_file(self, filename):
		lines = []

		pre_lines = """<?xml version="1.0" encoding="UTF-8"?>
					   <!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
					   <en-export export-date="20160116T193600Z" application="Micaelwidell.com kindle-to-evernote script" version="0.1">
					"""
		lines.append(pre_lines)


		for note in self.notes:
			if note["tags"]:
				tags_xml = "<tag>" + "</tag><tag>".join(note["tags"]) + "</tag>"
			else:
				tags_xml = ""
			note_line = u"""
<note>
  <title>{title}</title>
  <content><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
<div>{content}</div>
</en-note>
]]></content>{tags_xml}
</note>
			""".format(title=note["title"], content=note["content"], tags_xml=tags_xml)
			lines.append(note_line)

		post_lines = """</en-export>"""
		lines.append(post_lines)

		with codecs.open(filename, mode="w", encoding='utf-8') as f:
			for line in lines:
  				f.write("%s\n" % line)


class AmazonHighlightsFile():
	highlights = []
	properties = {}

	title_author_regex = r"^(?P<title>.*) by (?P<author>.*)$"
	readmore_str = "Read more at location "
	note_str_begin = "Note: "
	note_str_end = " Edit"
	note_regex = r"^" + note_str_begin + "(?P<note>.*)" + note_str_end + "$"
	quote_regex = r"^(?P<quote>.*)" + readmore_str + "(?P<location>\d+)" + " .*" + "$"
	last_annotated_regex = r"^Last annotated on (?P<last_annotated>.*)$"
	runtime_error_str = "Something unexpected was encountered during parsing. Line = {}"
	num_passages_regex = r"^You have (?P<num_passages>\d+) highlighted passage.*$"
	num_notes_regex = r"^You have (?P<num_notes>\d+) note.*$"
	add_a_note_regex = r"^Add a note$"

	def __init__(self, lines):

		# Look for and extract first line of the text, which should be title and author
		tre = re.match(self.title_author_regex, lines[0])
		if tre:
			self.properties["title"] = tre.group("title")
			self.properties["author"] = tre.group("author")
		else:
			raise RuntimeError(self.runtime_error_str.format(lines[0]))

		# Look for and extract number of passages on line 2
		p_re = re.match(self.num_passages_regex, lines[1])
		if p_re:
			self.properties["num_passages"] = p_re.group("num_passages")
		else:
			raise RuntimeError(self.runtime_error_str.format(lines[1]))

		# Look for and extract number of notes on line 3
		nn_re = re.match(self.num_notes_regex, lines[2])
		if nn_re:
			self.properties["num_notes"] = nn_re.group("num_notes")
		else:
			raise RuntimeError(self.runtime_error_str.format(lines[2]))


		# Look for the "Last annotated" information on line four
		lre = re.match(self.last_annotated_regex, lines[3])
		if lre:
			self.properties["last_annotated"] = lre.group("last_annotated")
		else:
			raise RuntimeError(self.runtime_error_str.format(lines[3]))

		for line in lines:

			# Look for and extract note
			nre = re.match(self.note_regex, line)
			note = nre.group("note") if nre else None

			# Look for and extract quote and location
			qre = re.match(self.quote_regex, line)
			quote = qre.group("quote") if qre else None
			location = qre.group("location") if qre else None

			if quote and location:
				self.highlights.append({"quote": quote, "location": location})
			elif note:
				self.highlights[-1]["note"] = note
			elif re.match(self.add_a_note_regex, line) or \
				re.match(self.title_author_regex, line) or \
				re.match(self.last_annotated_regex, line) or \
				re.match(self.num_passages_regex, line) or \
				re.match(self.num_notes_regex, line) or \
				len(line) == 0:
				pass
			else:
				raise RuntimeError("Something unexpected was encountered during parsing. Line: {}".format(line))


def main():
	root = Tk()
	root.title("Micaelwidell.com kindle-to-evernote script")
	ta = Text(borderwidth=2)
	ta.pack(expand=YES, fill=BOTH)

	def convertToEvernote():
		lines = ta.get(1.0, END).split("\n")
		try:
			hlfile = AmazonHighlightsFile(lines)
			enf = EvernoteFile()
			for hl in hlfile.highlights:
				note = hl["note"] if "note" in hl else ""
				enf.add_book_quote(title = hlfile.properties["title"], 
					author = hlfile.properties["author"], 
					quote = hl["quote"], 
					location = hl["location"],
					note = note,
					last_annotated = hlfile.properties["last_annotated"])
			filename = "{}_{}.enex".format(hlfile.properties["title"],hlfile.properties["last_annotated"])
			enf.save_to_file(filename)
			msg = "Successfully converted your highlights to the Evernote file named {}".format(filename)
		except RuntimeError as r:
			msg = "Error: {}".format(r)

		tkMessageBox.showinfo("Message", msg)
		root.quit()


	button = Button(root, text="Ok", command=convertToEvernote).pack()
	root.mainloop()


main()
