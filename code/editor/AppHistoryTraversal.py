# HUMAN VETTED

from dataclasses import replace


class AppHistoryTraversal:
    def __init__(self, max_history_size):
        self.max_history_size = max_history_size

    def do(self, app, content):
        if content != app.content:
            undo_history = [*app.undo_history, app.content]
            if len(undo_history) > self.max_history_size:
                undo_history.pop(0)
            app = replace(app, content=content, undo_history=undo_history,
                          redo_history=[], dirty=True)
        return app

    def undo(self, app):
        if app.undo_history:
            undo_history = list(app.undo_history)
            content = undo_history.pop()
            app = replace(app, content=content, undo_history=undo_history,
                          redo_history=[*app.redo_history, app.content], dirty=True)
        return app

    def redo(self, app):
        if app.redo_history:
            redo_history = list(app.redo_history)
            content = redo_history.pop()
            app = replace(app, content=content, redo_history=redo_history,
                          undo_history=[*app.undo_history, app.content], dirty=True)
        return app
