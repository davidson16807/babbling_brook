# HUMAN VETTED

from dataclasses import replace


class AppHistoryTraversal:
    def __init__(self, max_history_size):
        self.max_history_size = max_history_size

    def do(self, app, image):
        if image != app.image:
            undo_history = [*app.undo_history, app.image]
            if len(undo_history) > self.max_history_size:
                undo_history.pop(0)
            app = replace(app, image=image, undo_history=undo_history,
                          redo_history=[], dirty=True)
        return app

    def undo(self, app):
        if app.undo_history:
            undo_history = list(app.undo_history)
            image = undo_history.pop()
            app = replace(app, image=image, undo_history=undo_history,
                          redo_history=[*app.redo_history, app.image], dirty=True)
        return app

    def redo(self, app):
        if app.redo_history:
            redo_history = list(app.redo_history)
            image = redo_history.pop()
            app = replace(app, image=image, redo_history=redo_history,
                          undo_history=[*app.undo_history, app.image], dirty=True)
        return app
