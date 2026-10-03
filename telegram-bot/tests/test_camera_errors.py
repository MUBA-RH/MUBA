import unittest
from muba_camera_errors import CameraProviderError, camera_failure_code


class CameraErrors(unittest.TestCase):
    def test_only_numeric_provider_codes_are_retained(self):
        error = CameraProviderError(503, b'{"errors":[{"code":3030,"message":"private prompt secret-token"},{"code":"secret"}],"input_image":"private"}')
        self.assertEqual(str(error), "HTTP_503_CF_3030")
        self.assertNotIn("private", repr(vars(error)))
        self.assertNotIn("secret", repr(vars(error)))

    def test_html_and_unexpected_json_are_safe(self):
        for body in (b'<html>secret</html>', b'[]', b'{"errors":null}', b'{"errors":[null,true,{}]}'):
            self.assertEqual(str(CameraProviderError(502, body)), "HTTP_502")

    def test_timeout_and_unknown_errors_do_not_expose_exception_text(self):
        self.assertEqual(camera_failure_code(TimeoutError('secret'), 'provider'), 'CAMERA_PROVIDER_TIMEOUT')
        self.assertEqual(camera_failure_code(ValueError('secret'), 'decode'), 'CAMERA_DECODE_ERROR')
