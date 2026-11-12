from mark import Note

note = Note('My notebook')
note.heading('Hello from Python')
note.text('Edit **Markdown** on the left, or switch to WYSIWYG.')
note.bullet_list(['Import one class', 'Build a note', 'Keep editing'])
note.task('Try the toolbar', checked=True)
note.code('note.image("photo.png", width=320)', 'python')
note.table(['Item', 'Status'], [['Editor', 'Ready'], ['Your idea', 'Next']])
# note.image('photo.png', alt='A photo', width=320)
# note.save('notebook.md')
Note.run()
