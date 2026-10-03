"""Safe Camera diagnostics: never retain source bytes, prompts or response text."""
import json


class CameraProviderError(RuntimeError):
    def __init__(self, status, response_body):
        self.status = int(status)
        codes = []
        try:
            payload = json.loads(response_body)
            errors = payload.get("errors", []) if isinstance(payload, dict) else []
            for error in errors[:4] if isinstance(errors, list) else []:
                code = error.get("code") if isinstance(error, dict) else None
                if isinstance(code, int) and not isinstance(code, bool) and 0 <= code <= 999999:
                    codes.append(str(code))
        except (ValueError, TypeError, UnicodeError):
            pass
        self.diagnostic = f"HTTP_{self.status}" + ("_CF_" + "_".join(codes) if codes else "")
        super().__init__(self.diagnostic)


def camera_failure_code(exc, stage):
    stage = stage if stage in ("prepare", "provider", "decode", "delivery") else "unknown"
    if isinstance(exc, CameraProviderError):
        return "CAMERA_" + exc.diagnostic
    if isinstance(exc, TimeoutError):
        return "CAMERA_" + stage.upper() + "_TIMEOUT"
    return "CAMERA_" + stage.upper() + "_ERROR"
