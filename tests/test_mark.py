import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from mark import Note
from PyQt6.QtGui import QTextCursor, QImage, QTextTable
from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtTest import QTest


class NoteTests(unittest.TestCase):
    def setUp(self):
        self.note = Note(show=False)

    def tearDown(self):
        self.note.close(force=True)

    def test_builder(self):
        n = self.note
        self.assertIs(n.heading('Hello').text('World').bullet_list(['One', 'Two'])
                      .task('Ship', checked=True).code('print(1)', 'python'), n)
        self.assertIn('# Hello', n.markdown)
        self.assertIn('- [x] Ship', n.markdown)
        self.assertIn('```python\nprint(1)\n```', n.markdown)

    def test_source_sync_and_callback(self):
        seen = []
        self.note.on_change(seen.append)
        self.note.source.setPlainText('**changed**')
        self.assertEqual(self.note.markdown, '**changed**')
        self.assertEqual(self.note.editor.toPlainText(), 'changed')
        self.assertEqual(seen[-1], '**changed**')

    def test_wysiwyg_sync(self):
        self.note.text('Hello').set_mode('wysiwyg')
        self.note.editor.moveCursor(QTextCursor.MoveOperation.End)
        self.note.editor.insertPlainText(' world')
        self.assertIn('Hello world', self.note.markdown)

    def test_image_dimensions_survive_rich_edit(self):
        self.note.image('photo.png', alt='A & B', width=240, height=120)
        self.note.set_mode('wysiwyg')
        self.note.editor.moveCursor(QTextCursor.MoveOperation.End)
        self.note.editor.insertPlainText('\nAfter')
        self.assertIn('width="240"', self.note.markdown)
        self.assertIn('height="120"', self.note.markdown)
        self.assertIn('photo.png', self.note.markdown)
        self.assertIn('After', self.note.markdown)

    def test_save_open_unicode_and_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'note.md'
            self.note.text('Hei æøå 🌿').save(path)
            self.note.clear().load(path)
            self.assertEqual(self.note.markdown, 'Hei æøå 🌿\n\n')
            self.assertFalse(self.note.dirty)
            out = Path(folder) / 'note.html'
            self.note.export_html(out)
            self.assertIn('Hei', out.read_text())

    def test_modes_do_not_rewrite_source(self):
        original = '# Heading\n\n*one*  \nnext\n'
        self.note.markdown = original
        for mode in ['wysiwyg', 'source', 'split']:
            self.note.set_mode(mode)
            self.assertEqual(self.note.markdown, original)

    def test_validation(self):
        for call in [lambda: self.note.heading('x', 7),
                     lambda: self.note.image('a', width=-1),
                     lambda: self.note.set_mode('bogus'),
                     lambda: self.note.table(['a', 'b'], [['a']])]:
            with self.assertRaises(ValueError):
                call()

    def test_table_escaping_and_fences(self):
        self.note.table(['A', 'B'], [['a|b', 'c\nd']]).code('```\ncode')
        self.assertIn('a\\|b', self.note.markdown)
        self.assertIn('c<br>d', self.note.markdown)
        self.assertIn('````\n```\ncode\n````', self.note.markdown)

    def test_multiple_windows_share_application(self):
        other = Note('Other', show=False)
        self.assertIs(other.app, self.note.app)
        other.close(force=True)

    def test_resize_and_rich_undo(self):
        self.note.image('photo.png', width=240).set_mode('wysiwyg')
        self.note.editor.moveCursor(QTextCursor.MoveOperation.End)
        self.note.resize_image(120)
        self.assertIn('width="120"', self.note.markdown)
        self.note.editor.undo()
        self.assertIn('width="240"', self.note.markdown)

    def test_image_code_stays_literal(self):
        self.note.code('<img src="x.png" width="80">', 'html')
        self.assertIn('<img', self.note.editor.toPlainText())
        self.assertNotIn('\ufffc', self.note.editor.toPlainText())

    def test_unsubscribe(self):
        seen = []
        unsubscribe = self.note.on_change(seen.append)
        self.note.text('one')
        unsubscribe()
        self.note.text('two')
        self.assertEqual(len(seen), 1)

    def test_table_has_borders(self):
        self.note.table(['A', 'B'], [['one', 'two']])
        table = next(f for f in self.note.editor.document().rootFrame().childFrames()
                     if isinstance(f, QTextTable))
        self.assertGreater(table.format().border(), 0)
        self.assertGreater(table.format().cellPadding(), 0)
        self.assertGreater(table.cellAt(0, 0).format().toTableCellFormat().topBorder(), 0)

    def test_clipboard_image_in_both_editors_survives_reload(self):
        for mode in ['source', 'wysiwyg']:
            self.note.clear().set_mode(mode)
            image = QImage(200, 100, QImage.Format.Format_ARGB32)
            image.fill(0xff4488cc)
            mime = QMimeData()
            mime.setImageData(image)
            self.note.app.clipboard().setMimeData(mime)
            widget = self.note.source if mode == 'source' else self.note.editor
            widget.paste()
            self.assertIn('data:image/png;base64,', self.note.markdown)
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'paste.md'
                self.note.save(path).clear().load(path)
                self.assertIn('\ufffc', self.note.editor.toPlainText())
                self.note.set_mode('wysiwyg')
                self.note.editor.moveCursor(QTextCursor.MoveOperation.End)
                self.note.resize_image(80)
                self.assertIn('width="80"', self.note.markdown)
                self.assertIn('height="40"', self.note.markdown)

    def test_copy_image_and_resize_in_preview(self):
        image = QImage(200, 100, QImage.Format.Format_ARGB32)
        image.fill(0xff4488cc)
        self.note.app.clipboard().setImage(image)
        self.note.set_mode('wysiwyg')
        self.note.editor.paste()
        self.note.editor.selectAll()
        self.note.editor.copy()
        self.assertTrue(self.note.app.clipboard().mimeData().hasImage())
        self.note.set_mode('split').resize_image(100)
        self.assertIn('width="100"', self.note.markdown)
        self.assertIn('height="50"', self.note.markdown)
        self.note.set_mode('wysiwyg')
        self.note.editor.moveCursor(QTextCursor.MoveOperation.End)
        self.note.editor.paste()
        self.assertEqual(self.note.editor.toPlainText().count('\ufffc'), 2)

    def test_resize_does_not_format_adjacent_text(self):
        self.note.image('photo.png', width=240, height=120).set_mode('wysiwyg')
        self.note.editor.moveCursor(QTextCursor.MoveOperation.End)
        self.note.editor.insertPlainText('hello')
        self.note.editor.selectAll()
        with self.assertRaises(ValueError):
            self.note.resize_image(120)
        self.assertIn('hello', self.note.editor.toPlainText())

    def test_source_undo(self):
        self.note.source.insertPlainText('hello')
        self.note.source.undo()
        self.assertEqual(self.note.markdown, '')

    def test_toolbar_paragraph_formats_round_trip_and_undo(self):
        for kind, level, expected in [('heading', 2, '## Hello'),
                                      ('bullet', 0, '- Hello'),
                                      ('number', 0, '1.  Hello'),
                                      ('quote', 0, '> Hello')]:
            self.note.markdown = 'Hello'
            self.note.set_mode('wysiwyg')
            self.note.editor.moveCursor(QTextCursor.MoveOperation.Start)
            self.note._paragraph(kind, level)
            self.assertIn(expected, self.note.markdown)
            self.note.editor.undo()
            self.assertEqual(self.note.markdown.strip(), 'Hello')

    def test_toolbar_source_formats_selected_lines(self):
        self.note.markdown = 'one\ntwo'
        self.note.set_mode('source')
        self.note.source.selectAll()
        self.note._paragraph('bullet')
        self.assertEqual(self.note.markdown, '- one\n- two')

    def test_toolbar_strike_selection(self):
        self.note.markdown = 'Hello'
        self.note.set_mode('wysiwyg')
        self.note.editor.selectAll()
        self.note._format('strike')
        self.assertIn('~~Hello~~', self.note.markdown)

    def test_table_editing_and_undo(self):
        n = self.note
        n.set_mode('wysiwyg')
        n._insert_table(2, 3)
        table = n.editor.textCursor().currentTable()
        self.assertEqual((table.rows(), table.columns()), (3, 3))
        n.editor.insertPlainText('Name')
        self.assertIn('Name', n.markdown)
        for operation, shape in [('below', (4, 3)), ('right', (4, 4)),
                                 ('remove_row', (3, 4)), ('remove_column', (3, 3))]:
            n._edit_table(operation)
            self.assertEqual((table.rows(), table.columns()), shape)
        before = n.markdown
        n._edit_table('delete')
        self.assertNotIn('Name', n.markdown)
        n.editor.undo()
        self.assertEqual(n.markdown, before)
        n.set_mode('source').set_mode('wysiwyg')
        self.assertIn('Name', n.markdown)

    def test_insert_table_source(self):
        self.note.set_mode('source')
        self.note._insert_table(2, 2)
        self.assertIn('| Column 1 | Column 2 |', self.note.markdown)
        tables = [f for f in self.note.editor.document().rootFrame().childFrames()
                  if isinstance(f, QTextTable)]
        self.assertEqual((tables[0].rows(), tables[0].columns()), (3, 2))

    def test_table_tab_navigation_and_new_row(self):
        n = self.note
        n.set_mode('wysiwyg')
        n._insert_table(1, 2)
        table = n.editor.textCursor().currentTable()
        QTest.keyClick(n.editor, Qt.Key.Key_Tab)
        self.assertEqual(table.cellAt(n.editor.textCursor()).column(), 1)
        n.editor.setTextCursor(table.cellAt(1, 1).firstCursorPosition())
        QTest.keyClick(n.editor, Qt.Key.Key_Tab)
        self.assertEqual(table.rows(), 3)
        self.assertEqual(table.cellAt(n.editor.textCursor()).row(), 2)
        QTest.keyClick(n.editor, Qt.Key.Key_Backtab)
        self.assertEqual(table.cellAt(n.editor.textCursor()).row(), 1)
        n.editor.undo()
        self.assertEqual(table.rows(), 2)

    def test_delete_only_column_leaves_surrounding_text(self):
        self.note.markdown = 'Before\n\n| Header |\n| --- |\n| Value |\n\nAfter'
        self.note.set_mode('wysiwyg')
        table = next(f for f in self.note.editor.document().rootFrame().childFrames()
                     if isinstance(f, QTextTable))
        self.note.editor.setTextCursor(table.cellAt(1, 0).firstCursorPosition())
        self.note._edit_table('remove_column')
        self.assertIn('Before', self.note.markdown)
        self.assertIn('After', self.note.markdown)
        self.assertNotIn('Value', self.note.markdown)

if __name__ == '__main__':
    unittest.main()
