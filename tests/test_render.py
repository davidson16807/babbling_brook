"""Real adapter and optional OpenGL checks; never substitute fake math or GPU code."""
import os
import unittest
from bootstrap import ROOT
try:
    import pygame
    import moderngl
    from pyglm import glm
except ImportError:
    raise unittest.SkipTest('Install the render extra for adapter and OpenGL tests')
from babbling_brook.adapters.PygameMessageQueue import PygameMessageQueue
from babbling_brook.messages import KeyboardMessage, KeyboardAction, MouseMotionMessage, FocusLostMessage


class AdapterTests(unittest.TestCase):
    def test_event_translation_and_repeat_filter(self):
        events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w, mod=0, repeat=False),
                  pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w, mod=0, repeat=True),
                  pygame.event.Event(pygame.MOUSEMOTION, pos=(10,20), rel=(2,-3)),
                  pygame.event.Event(pygame.WINDOWFOCUSLOST)]
        messages = PygameMessageQueue(lambda: events).poll()
        self.assertEqual(messages[0], KeyboardMessage('w', KeyboardAction.PRESS))
        self.assertIsInstance(messages[1], MouseMotionMessage)
        self.assertEqual(messages[1].offset, glm.vec2(2,-3))
        self.assertIsInstance(messages[2], FocusLostMessage)
        self.assertEqual(len(messages), 3)


@unittest.skipUnless(os.environ.get('BB_TEST_GL') == '1', 'Set BB_TEST_GL=1 on a machine with EGL to run real rendering tests')
class RenderingTests(unittest.TestCase):
    def test_world_ui_and_resource_lifecycle(self):
        from dataclasses import replace
        from babbling_brook.game import load_game
        from babbling_brook.adapters.PygameImages import PygameImages
        from babbling_brook.adapters.PygameUiView import PygameUiView
        from babbling_brook.view.Textures import Textures
        from babbling_brook.view.programs.TileProgram import TileProgram
        from babbling_brook.view.programs.BillboardProgram import BillboardProgram
        from babbling_brook.view.programs.UiProgram import UiProgram
        from babbling_brook.view.views.TileView import TileView
        from babbling_brook.view.views.BillboardView import BillboardView
        from babbling_brook.view.views.GameView import GameView
        gl = moderngl.create_standalone_context(require=330, backend='egl')
        framebuffer = gl.simple_framebuffer((640, 480))
        framebuffer.use()
        textures = Textures(gl, PygameImages(ROOT / 'data/textures'))
        view = GameView(TileView(TileProgram(gl, textures)),
                       BillboardView(BillboardProgram(gl, textures)), PygameUiView(UiProgram(gl)))
        try:
            model = replace(load_game(ROOT / 'data'), viewport=(640,480))
            gl.clear(0,0,0,1, depth=1)
            view.draw(model)
            first = framebuffer.read()
            self.assertGreater(len(set(first)), 20)
            framebuffer.depth_mask = True
            gl.clear(0,0,0,1, depth=1)
            view.draw(replace(model, show_inventory=True))
            self.assertNotEqual(first, framebuffer.read())
            self.assertEqual(gl.error, 'GL_NO_ERROR')
            view.release()
            view.release()
            # Programs must remain harmless after release, including nonempty draws.
            view.draw(model)
        finally:
            view.release()
            textures.release()
            framebuffer.release()
            gl.release()
            pygame.quit()


if __name__ == '__main__':
    unittest.main()
