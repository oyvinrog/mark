# Mark

A small, importable native Markdown editor. `Note()` creates a new window.
PyQt6 is the only runtime dependency; no browser or server is needed.

## Try it

```bash
python3 mark.py --demo
python3 example.py
python3 mark.py existing-note.md
```

PyQt6 is already installed in this workspace's Python. For another environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python mark.py --demo
```

An installation also provides the `mark-note` command. Python 3.10+ is required.

## Import it

```python
from mark import Note

note = Note('Project notes')
note.heading('Research').text('Some **bold** ideas.')
note.image('photo.png', alt='Experiment', width=320)
note.task('Review results').task('Collect samples', checked=True)
note.save('research.md')
Note.run()
```

Construct as many notes as you like, then call `Note.run()` **once**. The
constructor shows the window without blocking. The event loop keeps windows
responsive until they close. Inside an existing Qt app, use that app's event
loop instead. All widget operations must run on the main GUI thread.

## API

Builder methods return the note, so calls can be chained.

| Method/property | Purpose |
| --- | --- |
| `Note(title='Untitled', text='', path=None, mode='split', show=True)` | Create a window, optionally loading a file |
| `note.markdown` | Read or replace the complete Markdown string |
| `append(markdown)` | Append exact raw Markdown |
| `text(text)` | Append a paragraph; Markdown is accepted |
| `heading(text, level=1)` | Heading levels 1–6 |
| `bullet_list(items, ordered=False)` | Bullet or numbered list |
| `task(text, checked=False)` | Task checkbox |
| `quote(text)` | Block quote |
| `code(code, language='')` | Fenced code, including code containing backticks |
| `link(label, url)` | Link |
| `image(src, alt='', width=None, height=None)` | Image with optional pixel dimensions |
| `table(headers, rows)` | Table with escaped pipes |
| `rule()` / `clear()` | Separator / clear contents |
| `set_mode('source' / 'split' / 'wysiwyg')` | Change editing mode |
| `resize_image(width, height=None)` | Resize a selected/adjacent image; omitted height keeps proportions |
| `save(path=None)` / `load(path)` | UTF-8 Markdown persistence |
| `export_html(path)` | Export rendered HTML |
| `on_change(callback)` | Receive Markdown changes; returns an unsubscribe function |
| `dirty` / `path` | Unsaved-change status / resolved file path |
| `show()` / `close(force=False)` | Window lifecycle |

`source`, `editor`, `window`, and `app` expose Qt objects for further customization.
`load()` and programmatic replacement deliberately replace the current content;
closing a dirty window prompts to save. `close(force=True)` discards without a prompt.
Callbacks run synchronously on the GUI thread; keep them short.

## Editing

- **Source:** direct Markdown editing with native undo/redo.
- **Split:** editable source and a rendered, read-only preview.
- **WYSIWYG:** edit rendered text with a Word-style formatting toolbar: paragraph
  styles (Normal and Heading 1–6), Bold, Italic, Strikethrough, Bullets, Numbering,
  Quote, Task, Link, and Image. Select text or place the cursor in a paragraph to
  format it. Undo/Redo are also available on the toolbar. Formatting controls
  insert Markdown when editing source; Ctrl+K inserts a link.
- Insert local images with the toolbar, choosing a pixel width. For later resizing,
  right-click an image in preview or WYSIWYG and choose **Resize image…**.
  You can also select it and click **Resize image…** in the toolbar, or double-click it.
  Resizing keeps the image proportions. You can also edit the
  HTML image's width/height in source mode.
- Ctrl+S saves, Ctrl+Shift+S saves as, Ctrl+F finds text; Ctrl+Z undoes typing.

### Tables

Click **Insert table…** and choose the number of data rows and columns. In
WYSIWYG, type directly into cells; the shaded first row holds column headings.
Use **Tab** / **Shift+Tab** to move between cells. Tab in the last cell adds a row.
Click a cell to enable the table toolbar, or right-click it to add rows above or
below, add columns left or right, or delete a row, column, or the whole table.
These changes support Undo. In source mode, Insert table creates Markdown syntax.

Relative image paths resolve against the saved note's folder, or the working
folder for an unsaved note. Toolbar images use absolute file URLs. Images inserted from files remain
external references, not copied when saving/exporting. **Ctrl+V pastes clipboard
images in source or WYSIWYG**, embedding PNG data in the Markdown so it survives
saving, reopening, and moving the file. This makes the Markdown file larger.
Selecting an image in WYSIWYG and copying it also puts image data on the clipboard.
Use local
files for predictable display; remote image downloading is not implemented.

## Fidelity and scope

Source mode preserves your text exactly. Simply switching modes also preserves
it. **Editing in WYSIWYG normalizes Markdown** through Qt's Markdown writer:
spacing and syntax choices may change. Arbitrary HTML, custom styles, and
extensions such as math, Mermaid, and footnotes are not losslessly supported.
Use source mode for those documents. Image dimensions are preserved through a
custom HTML-image serializer because standard Markdown has no size syntax.

The renderer and rich editor use Qt's native Markdown support:
[QTextEdit documentation](https://doc.qt.io/qt-6/qtextedit.html).
Replacing content via the API resets editor undo history; normal typing retains
undo history within its active editor. Switching editing surfaces does not
provide a shared undo timeline. This is a local editor, without autosave,
collaboration, or syntax highlighting.

## Tests

Tests use the standard library's unittest and Qt's offscreen platform; no display
or additional test dependencies are required.

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v
```

The tests were written and run before implementation, then used to drive the
builders, source/rich synchronization, image-size preservation, file round trips,
validation, callbacks, and window behavior. For your own code:

```python
note = Note(show=False)
try:
    note.heading('Test')
    assert '# Test' in note.markdown
finally:
    note.close(force=True)
```
