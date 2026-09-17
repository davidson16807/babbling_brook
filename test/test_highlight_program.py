import os
import unittest

from pyglm import glm


@unittest.skipUnless(os.environ.get('BB_TEST_GL') == '1', 'Set BB_TEST_GL=1 to check EGL rendering')
class HighlightProgramTests(unittest.TestCase):
    def test_real_shader_blends_only_tile_tops_and_preserves_depth(self):
        import moderngl
        from babbling_brook.view.program.HighlightProgram import HighlightProgram
        from babbling_brook.view.program.ViewState import ViewState

        context = moderngl.create_standalone_context(require=330, backend='egl')
        framebuffer = context.simple_framebuffer((64, 32))
        framebuffer.use()
        program = HighlightProgram(context)
        try:
            framebuffer.clear(.2, .2, .2, 1, depth=1)
            view = ViewState(glm.ortho(0, 2, 0, 1, -10, 10), glm.vec3(1, 0, 0))
            depth_before = framebuffer.read(attachment=-1, components=1, dtype='f4')
            program.draw(((0, 0),), (glm.mat2(0, .5, 1, .25),), ((1, 0, 0, .5),), view)
            pixels = framebuffer.read(components=3, alignment=1)
            def pixel(x, y):
                offset = (y * 64 + x) * 3
                return tuple(pixels[offset:offset + 3])
            for x, y in ((8, 8), (24, 8), (8, 24), (24, 24)):
                for actual, expected in zip(pixel(x, y), (153, 26, 26)):
                    self.assertLessEqual(abs(actual - expected), 1)
            self.assertEqual(pixel(48, 16), (51, 51, 51))
            self.assertEqual(framebuffer.read(attachment=-1, components=1, dtype='f4'), depth_before)
            self.assertTrue(framebuffer.depth_mask)
            # Grow all instance buffers and check that an occluding depth wins.
            program.draw(((0, 0), (1, 0)), (glm.mat2(0), glm.mat2(0)),
                         ((0, 1, 0, .5), (0, 0, 1, .5)), view)
            framebuffer.clear(.2, .2, .2, 1, depth=0)
            program.draw(((0, 0),), (glm.mat2(0),), ((1, 0, 0, 1),), view)
            self.assertEqual(framebuffer.read(components=3, alignment=1), bytes((51, 51, 51)) * (64 * 32))
            with self.assertRaises(ValueError):
                program.draw(((0, 0),), (), (), view)
            program.draw((), (), (), view)
            program.release()
            program.release()
        finally:
            program.release()
            framebuffer.release()
            context.release()
